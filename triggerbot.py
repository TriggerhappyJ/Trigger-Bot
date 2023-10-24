import discord
import asyncio
import yaml
from credentials import token, canary_token
from epicgames import current_free_games, upcoming_free_games, generate_free_game_embed
from messagereplacement import handle_message_replacement, update_replace_blacklist
from webhooks import create_webhook_if_not_exists, manage_webhooks, clear_webhooks_for_guild

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)
freeGames = bot.create_group("freegames", "Commands related to the Epic Games Store")
linkReplacements = bot.create_group("linkreplacement", "Commands related to link replacements")
settings = bot.create_group("settings", "Commands related to bot settings")
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)
    startup_status_message = config['startup_status_message']
    startup_status_type = config['startup_status_type']
    running_status_message = config['running_status_message']
    running_status_type = config['running_status_type']

job_queue = asyncio.Queue()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    await bot.change_presence(activity=discord.Activity(type=startup_status_type, name=startup_status_message))

    # Clear existing webhooks from the config file for each guild
    for guild in bot.guilds:
        clear_webhooks_for_guild(guild.id, config)

    # Check if there are any guilds in the config file that the bot is no longer in
    for guild_webhooks in config['guild_webhooks']:
        guild = bot.get_guild(guild_webhooks['guild_id'])
        if guild is None:
            config['guild_webhooks'].remove(guild_webhooks)
            print("Removed guild " + str(
                guild_webhooks['guild_id']) + " from config file, guild no longer exists or bot is no longer in it")

    # Load existing webhooks from the config file
    for guild in bot.guilds:
        for channel in guild.text_channels:
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                # If the bot has created the webhook, save it in the config file
                if webhook.user == bot.user:
                    print("Saving webhook " + webhook.name)
                    await manage_webhooks(channel=channel, webhook=webhook, guild_id=guild.id, config=config)

    await bot.change_presence(activity=discord.Activity(type=running_status_type, name=running_status_message))
    print('Ready to go!')


@bot.listen('on_message')
async def replace_link(message):
    if message.author == bot.user or message.author.id in config.get('replace_blacklist', set()):
        return

    replacements = {
        'https://twitter.com/': 'https://fxtwitter.com/',
        'https://x.com/': 'https://fxtwitter.com/',
        'https://www.reddit.com/': 'https://www.rxddit.com/',
        'https://old.reddit.com/': 'https://old.rxddit.com/',
    }

    for prefix, replacement in replacements.items():
        if message.content.startswith(prefix):
            modified_message = message.content.replace(prefix, replacement)

            webhook = await create_webhook_if_not_exists(message.channel, config, bot)
            worker = asyncio.create_task(task_consumer())
            await job_queue.put(lambda: handle_message_replacement(message, modified_message, worker, webhook, bot))
            break


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="stop",
                          description="Stops the bot from replacing links you post")
async def stop_link_replacements(ctx):
    await update_replace_blacklist(ctx, add_to_list=True, config=config)


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="start",
                          description="Starts the bot replacing links you post")
async def start_link_replacements(ctx):
    await update_replace_blacklist(ctx, add_to_list=False, config=config)


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="current",
                   description="Shows the current free games on the Epic Games Store")
async def current_games(ctx):
    free_games_list = current_free_games()
    for game in free_games_list:
        await ctx.send(embed=generate_free_game_embed(free_games_list, game, "current"))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " free games right now <a:duckSpin:892990312732053544>")


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="upcoming",
                   description="Shows the upcoming free games on the Epic Games Store")
async def upcoming_games(ctx):
    free_games_list = upcoming_free_games()
    for game in free_games_list:
        await ctx.send(embed=generate_free_game_embed(free_games_list, game, "upcoming"))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " upcoming free games <a:duckSpin:892990312732053544>")


@settings.command(guild_ids=[741435438807646268, 369336391467008002], name="setstatus",
                  description="Sets the bots status", )
async def set_status(ctx, status_type: discord.Option(int, "playing: 0, streaming: 1, listening: 2, watching: 3"),
                     status_message: discord.Option(str, "The status message")):
    allowed_user_id = 233484220138258432
    status_type_map = {
        0: "playing",
        1: "streaming",
        2: "listening to",
        3: "watching"
    }

    if ctx.author.id == allowed_user_id:
        with open('config.yml', 'w') as edit_config:
            config['running_status_type'] = status_type
            config['running_status_message'] = status_message
            yaml.dump(config, edit_config)
        await bot.change_presence(activity=discord.Activity(type=status_type, name=status_message))

        if status_type in status_type_map:
            status_type_str = status_type_map[status_type]
            await ctx.respond(f"Status set to {status_type_str} {status_message} <a:ralseiBlunt:899401210870763610>")
        else:
            await ctx.respond("You don't have permission to use this command. <a:ralseiBoom:899406996007190549>")


async def task_consumer():
    while True:
        task = await job_queue.get()
        await task()
        job_queue.task_done()


bot.run(canary_token)
