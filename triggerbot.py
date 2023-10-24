import discord
import asyncio
import yaml
import os
import time
import requests
from credentials import token, canary_token
from epicgames import currentFreeGames, upcomingFreeGames
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)
freeGames = bot.create_group("freegames", "Commands related to the Epic Games Store")
linkReplacements = bot.create_group("linkreplacement", "Commands related to link replacements")
with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

job_queue = asyncio.Queue()
MAX_WEBHOOKS = 14


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="startup sequence"))

    for guild in bot.guilds:
        # Check if the bot has permission to manage webhooks in any text channel
        if any(channel.permissions_for(guild.me).manage_webhooks for channel in guild.text_channels):
            # Remove old webhooks and update config
            for channel in guild.text_channels:
                webhooks = await channel.webhooks()
                for webhook in webhooks:
                    if webhook.user == bot.user:
                        print(f"Deleting webhook {webhook.name} in guild: {guild.name} id: {guild.id}")
                        await webhook.delete()
                        # Remove the webhook from the config
                        config['guild_webhooks'].pop(guild.id, None)

            # Create a new webhook and set the avatar
            webhook_avatar_url = 'https://i.imgur.com/WY4IxCU.png'
            avatar_bytes = requests.get(webhook_avatar_url).content
            new_webhook = await guild.text_channels[0].create_webhook(name="TriggerBotWebhook", avatar=avatar_bytes)

            if new_webhook is not None:
                config['guild_webhooks'][guild.id] = new_webhook.url
                print(f"Created webhook in guild: {guild.name} id: {guild.id}")
            else:
                print(f"Failed to create webhook in guild: {guild.name} id: {guild.id}")

    with open('config.yml', 'w') as config_file:
        yaml.dump(config, config_file)

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you"))
    print('Ready to go!')


async def task_consumer():
    while True:
        task = await job_queue.get()
        await task()
        job_queue.task_done()


@bot.listen('on_message')
async def replace_link(message):
    if message.author == bot.user or message.author.id in config.get(
            'replace_blacklist', set()):
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
            await message.delete()
            worker = asyncio.create_task(task_consumer())

            channel_id = message.channel.id  # Get the channel's ID

            if channel_id not in webhooks:
                # If there is no existing webhook for this channel, create a new one
                new_webhook = await message.channel.create_webhook(name=message.channel.name)
                await manage_webhooks(channel_id, new_webhook, message.channel)  # Use the manageWebhooks function
                webhook = new_webhook
                print("Created webhook for channel: " + message.channel.name + " in guild: " + message.guild.name)
            else:
                webhook = webhooks[channel_id]  # Get the existing webhook from the dictionary
                print("Found existing webhook for: " + message.channel.name + " in guild: " + message.guild.name)

            await job_queue.put(lambda: handle_message_replacement(message, modified_message, worker, webhook))
            break


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="stop",
                          description="Stops the bot from replacing links you post")
async def stop_link_replacements(ctx):
    await update_replace_blacklist(ctx, add_to_list=True)


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="start",
                          description="Starts the bot replacing links you post")
async def start_link_replacements(ctx):
    await update_replace_blacklist(ctx, add_to_list=False)


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="current",
                   description="Shows the current free games on the Epic Games Store")
async def current_games(ctx):
    free_games_list = currentFreeGames()
    for game in free_games_list:
        await ctx.send(embed=generate_free_game_embed(free_games_list, game, "current"))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " free games right now <a:duckSpin:892990312732053544>")


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="upcoming",
                   description="Shows the upcoming free games on the Epic Games Store")
async def upcoming_games(ctx):
    free_games_list = upcomingFreeGames()
    for game in free_games_list:
        await ctx.send(embed=generate_free_game_embed(free_games_list, game, "upcoming"))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " upcoming free games <a:duckSpin:892990312732053544>")


def generate_free_game_embed(free_games_list, game, key):
    embed = discord.Embed(color=0x353336)
    embed.type = "rich"
    embed.title = free_games_list[game][0]
    embed.url = free_games_list[game][1]
    embed.description = free_games_list[game][3]
    embed.set_image(url=free_games_list[game][2])
    embed.set_footer(text="Last Updated: " + str(datetime.now())[:-7] + " || Developed by Jacob 😎")
    embed.set_thumbnail(
        url="https://cdn2.unrealengine.com/Unreal+Engine%2Feg-logo-filled-1255x1272-0eb9d144a0f981d1cbaaa1eb957de7a3207b31bb.png")
    if key == "current":
        embed.add_field(name="Valid Until", value=str(discord.utils.format_dt(free_games_list[game][5])), inline=True)
    else:
        embed.add_field(name="Available By", value=str(discord.utils.format_dt(free_games_list[game][4])), inline=True)
    return embed


async def handle_message_replacement(message, modified_message, worker, webhook):
    author = message.author
    channel = message.channel
    reaction_emoji = "☠"

    print("Replacing message from: " + author.name + " in channel: " + channel.name)

    sent_message, webhook = await send_replacement_message(modified_message, author, channel, reaction_emoji, webhook)

    def check(reaction, user):
        return user == author and str(reaction.emoji) == reaction_emoji and reaction.message.id == sent_message.id

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30, check=check)
        if reaction.emoji == reaction_emoji:
            await sent_message.delete()
    except asyncio.TimeoutError:
        await sent_message.clear_reaction(reaction_emoji)

    worker.cancel()


async def send_replacement_message(modified_message, author, channel, reaction_emoji, webhook):
    webhook_name = author.display_name
    avatar = author.guild_avatar.url if author.guild_avatar else author.avatar.url
    async with channel.typing():
        sent_message = await webhook.send(str(modified_message), username=webhook_name, avatar_url=avatar, wait=True)
        await sent_message.add_reaction(reaction_emoji)
    return sent_message, webhook


async def update_replace_blacklist(ctx, add_to_list):
    user_id = ctx.author.id
    if add_to_list and user_id not in config['replace_blacklist']:
        config['replace_blacklist'].append(user_id)
        message = "Got it! I won't replace replace your links anymore <a:ralseiBoom:899406996007190549>"
        print("Added " + str(user_id) + " to replace_blacklist")
    elif not add_to_list and user_id in config['replace_blacklist']:
        config['replace_blacklist'].remove(user_id)
        message = "Got it! I'll start replacing your links again <a:ralseiBlunt:899401210870763610>"
        print("Removed " + str(user_id) + " from replace_blacklist")
    else:
        message = "You already have link replacements " + (
            "disabled" if add_to_list else "enabled") + " <a:duckSpin:892990312732053544>"

    with open('config.yml', 'w') as config_file:
        yaml.dump(config, config_file)

    await ctx.respond(message)


bot.run(canary_token)
