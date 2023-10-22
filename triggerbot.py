import discord
from credentials import token
from epicgames import currentFreeGames, upcomingFreeGames
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

freeGames = bot.create_group("freegames", "Commands related to the Epic Games Store")

def generateEmbed(free_games_list, game, key):
    embed = discord.Embed(color=0x353336)
    embed.type = "rich"
    embed.title = free_games_list[game][0]
    embed.url = free_games_list[game][1]
    embed.description = free_games_list[game][3]
    embed.set_image(url=free_games_list[game][2])
    embed.set_footer(text="Last Updated: " + str(datetime.now())[:-7] + " || Developed by Jacob 😎")
    embed.set_thumbnail(url="https://cdn2.unrealengine.com/Unreal+Engine%2Feg-logo-filled-1255x1272-0eb9d144a0f981d1cbaaa1eb957de7a3207b31bb.png")
    if key == "current":
        embed.add_field(name="Valid Until", value=str(discord.utils.format_dt(free_games_list[game][5])), inline=True)
    else:
        embed.add_field(name="Available By", value=str(discord.utils.format_dt(free_games_list[game][4])), inline=True)
    return embed

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Ready to go!')

@bot.command()
async def impersonate(ctx, member: discord.Member, *, message=None):

    if message == None:
        await ctx.send(f'Who do you want to impersonate?')
        return

   

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.guild.id == 369336391467008002:
        return

    if message.content.startswith('https://twitter.com/'):
        modifiedLink = message.content.replace("https://twitter.com/", "https://fxtwitter.com/")
        await message.delete()
        webhook = await message.channel.create_webhook(name=message.author.display_name)
        if (message.author.guild_avatar):
            avatar = message.author.guild_avatar.url
        else:
            avatar = message.author.avatar.url
        await webhook.send(str(modifiedLink), username=message.author.display_name, avatar_url=avatar)
        webhooks = await message.channel.webhooks()
        for webhook in webhooks:
            await webhook.delete()
    elif message.content.startswith('https://x.com/'):
        modifiedLink = message.content.replace("https://x.com/", "https://fxtwitter.com/")
        await message.delete()
        webhook = await message.channel.create_webhook(name=message.author.display_name)
        if (message.author.guild_avatar):
            avatar = message.author.guild_avatar.url
        else:
            avatar = message.author.avatar.url
        await webhook.send(str(modifiedLink), username=message.author.display_name, avatar_url=avatar)
        webhooks = await message.channel.webhooks()
        for webhook in webhooks:
            await webhook.delete()
    elif message.content.startswith('https://www.reddit.com/'):
        modifiedLink = message.content.replace("https://www.reddit.com/", "https://www.rxddit.com/")
        await message.delete()
        webhook = await message.channel.create_webhook(name=message.author.display_name)
        if (message.author.guild_avatar):
            avatar = message.author.guild_avatar.url
        else:
            avatar = message.author.avatar.url
        await webhook.send(str(modifiedLink), username=message.author.display_name, avatar_url=avatar)
        webhooks = await message.channel.webhooks()
        for webhook in webhooks:
            await webhook.delete()
    elif message.content.startswith('https://old.reddit.com/'):
        modifiedLink = message.content.replace("https://old.reddit.com/", "https://old.rxddit.com/")
        await message.delete()
        webhook = await message.channel.create_webhook(name=message.author.display_name)
        if (message.author.guild_avatar):
            avatar = message.author.guild_avatar.url
        else:
            avatar = message.author.avatar.url
        await webhook.send(str(modifiedLink), username=message.author.display_name, avatar_url=avatar)
        webhooks = await message.channel.webhooks()
        for webhook in webhooks:
            await webhook.delete()
        
    
@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="current", description="Shows the current free games on the Epic Games Store")
async def currentGames(ctx):
    free_games_list = currentFreeGames()
    for game in free_games_list:
        await ctx.send(embed=generateEmbed(free_games_list, game, "current"))
    await ctx.respond("There are a total of " + str(len(free_games_list)) + " free games right now <a:duckSpin:892990312732053544>")

@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="upcoming", description="Shows the upcoming free games on the Epic Games Store")
async def upcomingGames(ctx):
    free_games_list = upcomingFreeGames()
    for game in free_games_list:
        await ctx.send(embed=generateEmbed(free_games_list, game, "upcoming"))
    await ctx.respond("There are a total of " + str(len(free_games_list)) + " upcoming free games <a:duckSpin:892990312732053544>")


bot.run(token)