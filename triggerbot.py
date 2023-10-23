import discord
import asyncio
import yaml
import os
import time
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
webhooks = {}
MAX_WEBHOOKS = 15


@bot.event
async def on_ready():
    global queue, loop
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    # finds all webhooks made by bot and deletes them
    for guild in bot.guilds:
        for channel in guild.text_channels:
            webhooks = await channel.webhooks()
            for webhook in webhooks:
                # If the bot has created the webhook, delete it
                if webhook.user == bot.user:
                    print("Deleting webhook " + webhook.name)
                    await webhook.delete()
                else:
                    print("Not my webhook!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="vine compliations"))
    print('Ready to go!')


async def task_consumer():
    while True:
        task = await job_queue.get()
        await task()
        job_queue.task_done()


async def manageWebhooks(channel_id, newWebhook):
    global webhooks

    if len(webhooks) >= MAX_WEBHOOKS:
        # If the dictionary has reached its limit, remove the oldest entry
        oldest_channel_id = next(iter(webhooks))
        delete_message = await channel_id.send("Reached max number of webhooks, deleting oldest one")
        await webhooks[oldest_channel_id].delete()
        await delete_message.delete()
        del webhooks[oldest_channel_id]

    webhooks[channel_id] = newWebhook
    

@bot.listen('on_message')
async def replaceLink(message):
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
            modifiedMessage = message.content.replace(prefix, replacement)
            await message.delete()
            worker = asyncio.create_task(task_consumer())
        
            channel_id = message.channel.id  # Get the channel's ID

            if channel_id not in webhooks:
                # If there is no existing webhook for this channel, create a new one
                newWebhook = await message.channel.create_webhook(name=message.channel.name)
                await manageWebhooks(channel_id, newWebhook)  # Use the manageWebhooks function
                webhook = newWebhook
                print("Created webhook for channel: " + message.channel.name + " in guild: " + message.guild.name)
            else:
                webhook = webhooks[channel_id]  # Get the existing webhook from the dictionary
                print("Found existing webhook for: " + message.channel.name + " in guild: " + message.guild.name)
                
            await job_queue.put(lambda: handleMessageReplacement(message, modifiedMessage, worker, webhook))
            break


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="stop",
                          description="Stops the bot from replacing links you post")
async def stopLinkReplacements(ctx):
    await updateReplaceBlacklist(ctx, addToList=True)


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="start",
                          description="Starts the bot replacing links you post")
async def startLinkReplacements(ctx):
    await updateReplaceBlacklist(ctx, addToList=False)


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="current",
                   description="Shows the current free games on the Epic Games Store")
async def currentGames(ctx):
    free_games_list = currentFreeGames()
    for game in free_games_list:
        await ctx.send(embed=generateFreeGameEmbed(free_games_list, game, "current"))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " free games right now <a:duckSpin:892990312732053544>")


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="upcoming",
                   description="Shows the upcoming free games on the Epic Games Store")
async def upcomingGames(ctx):
    free_games_list = upcomingFreeGames()
    for game in free_games_list:
        await ctx.send(embed=generateFreeGameEmbed(free_games_list, game, "upcoming"))
    await ctx.respond(
        "There are a total of " + str(len(free_games_list)) + " upcoming free games <a:duckSpin:892990312732053544>")


def generateFreeGameEmbed(free_games_list, game, key):
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


async def handleMessageReplacement(message, modifiedMessage, worker, webhook):
    author = message.author
    channel = message.channel
    reaction_emoji = "☠"
    
    print("Replacing message from: " + author.name + " in channel: " + channel.name)

    sent_message, webhook = await sendReplacementMessage(modifiedMessage, author, channel, reaction_emoji, webhook)

    def check(reaction, user):
        return user == author and str(reaction.emoji) == reaction_emoji and reaction.message.id == sent_message.id

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30, check=check)
        if reaction.emoji == reaction_emoji:
            await sent_message.delete()
    except asyncio.TimeoutError:
        await sent_message.clear_reaction(reaction_emoji)

    worker.cancel()


async def sendReplacementMessage(modifiedMessage, author, channel, reaction_emoji, webhook):
    webhook_name = author.display_name
    avatar = author.guild_avatar.url if author.guild_avatar else author.avatar.url
    async with channel.typing():
        sent_message = await webhook.send(str(modifiedMessage), username=webhook_name, avatar_url=avatar, wait=True)
        await sent_message.add_reaction(reaction_emoji)
    return sent_message, webhook


async def updateReplaceBlacklist(ctx, addToList):
    user_id = ctx.author.id
    if addToList and user_id not in config['replace_blacklist']:
        config['replace_blacklist'].append(user_id)
        message = "Got it! I won't replace replace your links anymore <a:ralseiBoom:899406996007190549>"
        print("Added " + str(user_id) + " to replace_blacklist")
    elif not addToList and user_id in config['replace_blacklist']:
        config['replace_blacklist'].remove(user_id)
        message = "Got it! I'll start replacing your links again <a:ralseiBlunt:899401210870763610>"
        print("Removed " + str(user_id) + " from replace_blacklist")
    else:
        message = "You already have link replacements " + (
            "disabled" if addToList else "enabled") + " <a:duckSpin:892990312732053544>"

    with open('config.yml', 'w') as config_file:
        yaml.dump(config, config_file)

    await ctx.respond(message)


bot.run(canary_token)
