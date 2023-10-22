import discord
import yaml
from credentials import token
from epicgames import currentFreeGames, upcomingFreeGames
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

print(config['replace_blacklist'])

freeGames = bot.create_group("freegames", "Commands related to the Epic Games Store")
linkReplacements = bot.create_group("linkreplacements", "Commands related to link replacements")


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Ready to go!')


@bot.listen('on_message')
async def replaceLink(message):
    if message.author == bot.user or message.guild.id == 369336391467008002 or message.author.id in open('names.yaml').read(config['replace_blacklist']):
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
            await generateReplacementMessage(message, modifiedMessage)
            break


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="stop",
                          description="Stops the bot from replacing links you post")
async def stopLinkReplacements(ctx):
    # adds the user to the list of users who don't want their links replaced
    if ctx.author.id not in config['replace_blacklist']:
        config['replace_blacklist'].append(ctx.author.id)
        with open('config.yml', 'w') as config_file:
            yaml.dump(config, config_file)
        await ctx.respond("Got it! I won't replace your links anymore <a:duckSpin:892990312732053544>")
    else:
        await ctx.respond("You already have link replacements disabled <a:duckSpin:892990312732053544>")


@linkReplacements.command(guild_ids=[741435438807646268, 369336391467008002], name="start",
                          description="Starts the bot replacing links you post")
async def startLinkReplacements(ctx):
    # removes the user from the list of users who don't want their links replaced
    if ctx.author.id in config['replace_blacklist']:
        config['replace_blacklist'].remove(ctx.author.id)
        with open('config.yml', 'w') as config_file:
            yaml.dump(config, config_file)
        await ctx.respond("Got it! I'll replace your links now <a:duckSpin:892990312732053544>")
    else:
        await ctx.respond("You already have link replacements enabled <a:duckSpin:892990312732053544>")


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


async def generateReplacementMessage(message, modifiedMessage):
    author = message.author
    channel = message.channel

    webhook_name = author.display_name
    avatar = author.guild_avatar.url if author.guild_avatar else author.avatar.url

    async with channel.typing():
        webhook = await channel.create_webhook(name=webhook_name)
        await webhook.send(str(modifiedMessage), username=webhook_name, avatar_url=avatar)

    webhooks = await channel.webhooks()
    for webhook in webhooks:
        await webhook.delete()


bot.run(token)
