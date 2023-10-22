from datetime import datetime, timezone
from epicstore_api import EpicGamesStoreAPI

api = EpicGamesStoreAPI()

def dateConversion(start_date_iso, end_date_iso):
    start_date = datetime.fromisoformat(start_date_iso).replace(tzinfo=timezone.utc).astimezone(tz=None)
    end_date = datetime.fromisoformat(end_date_iso).replace(tzinfo=timezone.utc).astimezone(tz=None)
    return start_date, end_date

def getFreeGames():
    free_games = api.get_free_games()['data']['Catalog']['searchStore']['elements']
    free_games = list(sorted(
        filter(
            lambda g: g.get('promotions'),
            free_games
        ),
        key=lambda g: g['title']
    ))
    return free_games

def getGameData(game):
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

def currentFreeGames():
    free_games_list = {}

    for game in getFreeGames():
        gameData = getGameData(game)
        
        if gameData[6] and game['price']['totalPrice']['discountPrice'] == 0:
            promotion_data = gameData[6][0]['promotionalOffers'][0]
            start_date_iso, end_date_iso = (
                promotion_data['startDate'][:-1], promotion_data['endDate'][:-1]
            )
            dates = dateConversion(start_date_iso, end_date_iso)
            free_games_list[gameData[0]] = [gameData[0], gameData[2], gameData[3], gameData[4], dates[0], dates[1]]

    return free_games_list

def upcomingFreeGames():
    free_games_list = {}

    for game in getFreeGames():
        gameData = getGameData(game)

        if gameData[7]:
            promotion_data = gameData[7][0]['promotionalOffers'][0]
            start_date_iso, end_date_iso = (
                promotion_data['startDate'][:-1], promotion_data['endDate'][:-1]
            )
            dates = dateConversion(start_date_iso, end_date_iso)
            free_games_list[gameData[0]] = [gameData[0], gameData[2], gameData[3], gameData[4], dates[0], dates[1]]

    return free_games_list