﻿import discord
import asyncio
import yaml
from credentials import token, canary_token
from epicgames import current_free_games, upcoming_free_games, generate_free_game_embed, check_epic_free_games
from messagereplacement import handle_message_replacement, replace_blacklist_settings
from webhooks import create_webhook_if_not_exists, manage_webhooks, clear_webhooks_for_guild, handle_webhook_startup

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
intents.guilds = True
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
    for guilds in config['guilds']:
        guild = bot.get_guild(guilds['guild_id'])
        if guild is None:
            config['guilds'].remove(guilds)
            print("Removed guild " + str(
                guilds['guild_id']) + " from config file, guild no longer exists or bot is no longer in it")

    # Load existing webhooks from the config file
    await handle_webhook_startup(bot, config)

    # Starts looking for changes to the epic games list
    worker = asyncio.create_task(task_consumer())
    await job_queue.put(lambda: check_epic_free_games(worker, bot))
    await bot.change_presence(activity=discord.Activity(type=running_status_type, name=running_status_message))
    print('Ready to go!')


@bot.listen('on_message')
async def replace_link(message):
    if message.author == bot.user:
        return

    replacements = {
        'https://twitter.com/': 'https://fxtwitter.com/',
        'https://x.com/': 'https://fxtwitter.com/',
        'https://www.reddit.com/': 'https://www.rxddit.com/',
        'https://old.reddit.com/': 'https://old.rxddit.com/',
        'https://www.youtube.com/shorts/': 'https://www.youtube.com/watch?v=',
    }

    for prefix, replacement in replacements.items():
        if message.content.startswith(prefix):
            with open('config.yml', 'r') as config_file:
                config = yaml.safe_load(config_file)
                if prefix in config['replace_blacklist'][message.author.id]:
                    return

            modified_message = message.content.replace(prefix, replacement)

            webhook = await create_webhook_if_not_exists(message.channel, config, bot)
            worker = asyncio.create_task(task_consumer())
            await job_queue.put(lambda: handle_message_replacement(message, modified_message, worker, webhook, bot))
            break


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="settings",
                          description="Allows you to choose what message types get replaced")
async def edit_link_replacements(ctx):
    worker = asyncio.create_task(task_consumer())
    await job_queue.put(lambda: replace_blacklist_settings(ctx, worker))


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="current",
                   description="Shows the current free games on the Epic Games Store")
async def current_games(ctx):
    with open('epicgames.yml', 'r') as epic_file:
        epic_free_games = yaml.safe_load(epic_file)
    free_games_list = epic_free_games['current_free_games']
    for game in free_games_list:
        await ctx.send(embed=generate_free_game_embed(free_games_list, game, "current", epic_free_games['update_time']))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " free games right now <a:duckSpin:892990312732053544>")


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="upcoming",
                   description="Shows the upcoming free games on the Epic Games Store")
async def upcoming_games(ctx):
    with open('epicgames.yml', 'r') as epic_file:
        epic_free_games = yaml.safe_load(epic_file)
    free_games_list = epic_free_games['upcoming_free_games']
    for game in free_games_list:
        await ctx.send(embed=generate_free_game_embed(free_games_list, game, "upcoming", epic_free_games['update_time']))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " upcoming free games <a:duckSpin:892990312732053544>")
    

@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="togglecurrentchannel",
                   description="Use to toggle posting of current free games in current channel")
async def toggle_current_games_channel(ctx):
    with open('config.yml', 'w') as edit_config:
        # Finds the guild in the config file
        guilds = next((entry for entry in config['guilds'] if entry['guild_id'] == ctx.guild.id), None)

        # Adds the current channel to the guilds current games channel list if it isn't already in it
        if ctx.channel.id not in guilds['current_games_channels']:
            guilds['current_games_channels'].append(ctx.channel.id)
            yaml.dump(config, edit_config)
            await ctx.respond("I'll send current free games messages here now <a:ralseiBlunt:899401210870763610>")
        else:
            # Removes the current channel from the guilds current games channel list if it is already in it
            guilds['current_games_channels'].remove(ctx.channel.id)
            yaml.dump(config, edit_config)
            await ctx.respond("I won't send current free games messages here anymore <a:ralseiBoom:899406996007190549>")


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="toggleupcomingchannel",
                   description="Use to toggle posting of upcoming free games in current channel")
async def toggle_upcoming_games_channel(ctx):
    with open('config.yml', 'w') as edit_config:
        # Finds the guild in the config file
        guilds = next((entry for entry in config['guilds'] if entry['guild_id'] == ctx.guild.id), None)

        # Adds the current channel to the guilds current games channel list if it isn't already in it
        if ctx.channel.id not in guilds['upcoming_games_channels']:
            guilds['upcoming_games_channels'].append(ctx.channel.id)
            yaml.dump(config, edit_config)
            await ctx.respond("I'll send upcoming free games messages here now <a:ralseiBlunt:899401210870763610>")
        else:
            # Removes the current channel from the guilds current games channel list if it is already in it
            guilds['upcoming_games_channels'].remove(ctx.channel.id)
            yaml.dump(config, edit_config)
            await ctx.respond("I won't send upcoming free games messages here anymore <a:ralseiBoom:899406996007190549>")


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


# When the bot is added to a server, add it to config
@bot.event
async def on_guild_join(guild):
    print("Joined guild: " + guild.name)
    guilds = {'guild_id': guild.id, 'guild_name': guild.name, 'webhooks': [], 'current_games_channels': [], 'upcoming_games_channels': []}
    config['guilds'].append(guilds)
    with open('config.yml', 'w') as edit_config:
        yaml.dump(config, edit_config)


# When the bot is removed from a server, remove it from config
@bot.event
async def on_guild_remove(guild):
    print("Left guild: " + guild.name)
    for guilds in config['guilds']:
        if guilds['guild_id'] == guild.id:
            config['guilds'].remove(guilds)
            with open('config.yml', 'w') as edit_config:
                yaml.dump(config, edit_config)

async def task_consumer():
    while True:
        task = await job_queue.get()
        await task()
        job_queue.task_done()


bot.run(canary_token)
