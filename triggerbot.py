import discord
from credentials import token
from epicgames import currentFreeGames, upcomingFreeGames
from datetime import datetime

bot = discord.Bot()

freeGames = bot.create_group("freegames", "Commands related to the Epic Games Store")

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    
@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="current", description="Shows the current free games on the Epic Games Store")
async def currentGames(ctx):
    free_games_list = currentFreeGames()
    for game in free_games_list:
        gameName = free_games_list[game][0]
        gameUrl = free_games_list[game][1]
        gameThumbnail = free_games_list[game][2]
        gameDescription = free_games_list[game][3]
        startDate = free_games_list[game][4]
        endDate = free_games_list[game][5]
        
        embed = discord.Embed(color=0x353336)
        embed.type = "rich"
        embed.title = gameName
        embed.url = gameUrl
        embed.description = gameDescription
        embed.add_field(name="Valid Until", value=str(discord.utils.format_dt(endDate)), inline=True)
        embed.set_image(url=gameThumbnail)
        # Shows the current local time
        embed.set_footer(text="Last Updated: " + str(datetime.now())[:-7] + " || Developed by Jacob 😎")
        embed.set_thumbnail(url="https://cdn2.unrealengine.com/Unreal+Engine%2Feg-logo-filled-1255x1272-0eb9d144a0f981d1cbaaa1eb957de7a3207b31bb.png")
        await ctx.send(embed=embed)
    await ctx.respond("There are a total of " + str(len(free_games_list)) + " free games right now <a:duckSpin:892990312732053544>")


@freeGames.command(guild_ids=[741435438807646268, 369336391467008002], name="upcoming", description="Shows the upcoming free games on the Epic Games Store")
async def upcomingGames(ctx):
    free_games_list = upcomingFreeGames()
    for game in free_games_list:
        gameName = free_games_list[game][0]
        gameUrl = free_games_list[game][1]
        gameThumbnail = free_games_list[game][2]
        gameDescription = free_games_list[game][3]
        startDate = free_games_list[game][4]
        endDate = free_games_list[game][5]

        embed = discord.Embed(color=0x353336)
        embed.type = "rich"
        embed.title = gameName
        embed.url = gameUrl
        embed.description = gameDescription
        embed.add_field(name="Available By", value=str(discord.utils.format_dt(startDate)), inline=True)
        embed.set_image(url=gameThumbnail)
        # Shows the current local time
        embed.set_footer(text="Last Updated: " + str(datetime.now())[:-7] + " || Developed by Jacob 😎")
        embed.set_thumbnail(url="https://cdn2.unrealengine.com/Unreal+Engine%2Feg-logo-filled-1255x1272-0eb9d144a0f981d1cbaaa1eb957de7a3207b31bb.png")
        await ctx.send(embed=embed)
    await ctx.respond("There are a total of " + str(len(free_games_list)) + " upcoming free games <a:duckSpin:892990312732053544>")

bot.run(token)