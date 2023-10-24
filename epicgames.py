from datetime import datetime, timezone
from epicstore_api import EpicGamesStoreAPI
import yaml
import discord
import asyncio


api = EpicGamesStoreAPI()


def date_conversion(start_date_iso, end_date_iso):
    start_date = datetime.fromisoformat(start_date_iso).replace(tzinfo=timezone.utc).astimezone(tz=None)
    end_date = datetime.fromisoformat(end_date_iso).replace(tzinfo=timezone.utc).astimezone(tz=None)
    return start_date, end_date


def get_free_games():
    free_games = api.get_free_games()['data']['Catalog']['searchStore']['elements']
    free_games = list(sorted(
        filter(
            lambda g: g.get('promotions'),
            free_games
        ),
        key=lambda g: g['title']
    ))
    return free_games


def get_game_data(game):
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
    return game_title, game_publisher, game_url, game_thumbnail, game_description, game_price, game_promotions, upcoming_promotions


def current_free_games():
    free_games_list = {}

    for game in get_free_games():
        game_data = get_game_data(game)

        if game_data[6] and game['price']['totalPrice']['discountPrice'] == 0:
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
