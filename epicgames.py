from datetime import datetime, timezone
from epicstore_api import EpicGamesStoreAPI
import yaml
import discord
import asyncio
import requests

api = EpicGamesStoreAPI()

def date_conversion(start_date_iso, end_date_iso):
    start_date = datetime.fromisoformat(start_date_iso).replace(tzinfo=timezone.utc).astimezone(tz=None)
    end_date = datetime.fromisoformat(end_date_iso).replace(tzinfo=timezone.utc).astimezone(tz=None)
    return start_date, end_date


def get_free_games():
    print("Starting to gather free games")
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    response = requests.get(url)
    data = response.json()

    games = data['data']['Catalog']['searchStore']['elements']
    free_games_info = []

    for game in games:
        if game['promotions'] and game['promotions']['promotionalOffers']:
            offers = game['promotions']['promotionalOffers']
            for offer in offers:
                for promotionalOffer in offer['promotionalOffers']:
                    if promotionalOffer['discountSetting']['discountPercentage'] == 0:
                        game_info = {
                            'title': game['title'],
                            'description': game.get('description'),
                            'pageSlug': game['offerMappings'][0]['pageSlug'],
                            'image': game['keyImages'][0]['url'] if game['keyImages'] else 'No image found',
                            'expiry': promotionalOffer['endDate']
                        }
                        free_games_info.append(game_info)

    return free_games_info

def get_game_data(game):
    print("Getting game data")
    game_title = game['title']
    game_publisher = game['seller']['name']
    game_url = f"https://store.epicgames.com/en-US/p/{game['catalogNs']['mappings'][0]['pageSlug']}"
    game_thumbnail = None
    game_description = game['description']
    for image in game['keyImages']:
        if image['type'] == 'OfferImageWide':
            game_thumbnail = image['url']
    game_price = game['price']['totalPrice']['fmtPrice']['originalPrice']
    game_promotions = game['promotions']['promotionalOffers']
    upcoming_promotions = game['promotions']['upcomingPromotionalOffers']
    print(game_title, game_publisher, game_url, game_thumbnail, game_description, game_price, game_promotions, upcoming_promotions)
    return game_title, game_publisher, game_url, game_thumbnail, game_description, game_price, game_promotions, upcoming_promotions


def current_free_games():
    print("Getting current free games from data")
    free_games_list = {}

    for game in get_free_games():
        print("Sorting game")
        promotion_data = game_data[6][0]['promotionalOffers'][0]
        start_date_iso, end_date_iso = (
            promotion_data['startDate'][:-1], promotion_data['endDate'][:-1]
        )
        dates = date_conversion(start_date_iso, end_date_iso)
        free_games_list[game_data[0]] = [game_data[0], game_data[2], game_data[3], game_data[4], dates[0], dates[1]]

    return free_games_list


def upcoming_free_games():
    free_games_list = {}

    for game in get_free_games():
        game_data = get_game_data(game)

        if game_data[7]:
            promotion_data = game_data[7][0]['promotionalOffers'][0]
            start_date_iso, end_date_iso = (
                promotion_data['startDate'][:-1], promotion_data['endDate'][:-1]
            )
            dates = date_conversion(start_date_iso, end_date_iso)
            free_games_list[game_data[0]] = [game_data[0], game_data[2], game_data[3], game_data[4], dates[0], dates[1]]

    return free_games_list


def generate_free_game_embed(free_games_list, game, update_time):
    print("Generating embed for free games")
    embed = discord.Embed(color=0x353336)
    print("color set")
    embed.type = "rich"
    print("type set")
    embed.title = game['title']
    print("title set")
    embed.url = ('https://store.epicgames.com/p/' + game['pageSlug'])
    print("url set")
    embed.description = game['description']
    print("desc set")
    embed.set_image(url=game['image'])
    print("image set")
    embed.set_footer(text="Last Updated: " + update_time + " || Developed by Jacob 😎")
    print("footer set")
    embed.set_thumbnail(
        url="https://cdn2.unrealengine.com/Unreal+Engine%2Feg-logo-filled-1255x1272-0eb9d144a0f981d1cbaaa1eb957de7a3207b31bb.png")
    # Parse the ISO 8601 date string into a datetime object
    expiry_dt = datetime.fromisoformat(game['expiry'].replace('Z', '+00:00'))  # Convert the 'Z' to UTC offset

    # Add the field with the correctly formatted datetime
    embed.add_field(name="Valid Until", value=str(discord.utils.format_dt(expiry_dt)), inline=True)
    print("expiry set")
    print(embed)
    return embed


async def check_epic_free_games(worker, bot):
    while True:
        try: 
            current_games_list = get_free_games()
            #upcoming_games_list = upcoming_free_games()
    
            with open('yaml/epicgames.yml', 'r') as epic_file:
                epic_config = yaml.safe_load(epic_file)
    
            with open('yaml/config.yml', 'r') as config_file:
                config = yaml.safe_load(config_file)
    
            print("Checking for free games...  Current time: " + str(datetime.now())[:-7])
            epic_config['update_time'] = str(datetime.now())[:-7]
    
            if current_games_list != epic_config['current_free_games']:
                print("Current free game is different! Updating...")
                epic_config['current_free_games'] = current_games_list
                for guild in config['guilds']:
                    if guild['current_games_channel'] is not None and str(guild['current_games_channel']) != '':
                        current_games_channel = bot.get_channel(guild['current_games_channel'])
                        for game in epic_config['current_free_games']:
                            await current_games_channel.send(embed=generate_free_game_embed(current_games_list, game, str(datetime.now())[:-7]))
            else:
                print("Current free games are the same!")
    
            #if upcoming_games_list != epic_config['upcoming_free_games']:
            #   print("Upcoming free game is different! Updating...")
            #   epic_config['upcoming_free_games'] = upcoming_games_list
            #   for guild in config['guilds']:
            #       if guild['upcoming_games_channel'] is not None and str(guild['upcoming_games_channel']) != '':
            #           upcoming_games_channel = bot.get_channel(guild['upcoming_games_channel'])
            #           for game in epic_config['upcoming_free_games']:
            #               await upcoming_games_channel.send(embed=generate_free_game_embed(upcoming_games_list, game, "upcoming", str(datetime.now())[:-7]))
            #else:
            #   print("Upcoming free games are the same!")
    
            with open('yaml/epicgames.yml', 'w') as edit_epicgames:
                yaml.dump(epic_config, edit_epicgames)
                print("Updated epicgames.yml")
        except:
            print("Failed to post free games, will try again")
    
        await asyncio.sleep(14400)
