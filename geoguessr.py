import os
import random
import aiohttp
import logging
import json
from config import DEFAULT_MAP

NCFA = os.environ.get("NCFA")


def load_json(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data['seeds']


class GeoGuessr:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Cookie": f"_ncfa={NCFA}"
        }
        self.game = None
        self.pool = None
        self.map_id = None

    async def create_geoguessr_game(self, map_id=None):
        """
        Creates a new GeoGuessr game.

        Returns:
            str: Game token
        """
        if not map_id:
            self.map_id = DEFAULT_MAP['map_id']
        else:
            self.map_id = map_id

        if self.map_id == 'qq':
            self.pool = load_json('qq_seeds.json')
            seed = random.choice(self.pool)
            self.game = {
                "token": "a",
                "map": "qq",
                "mapName": "西溪探梅",
                "round": 1,
                "rounds": [
                    {
                        "lat": seed['lat'],
                        "lng": seed['lng'],
                        "panoId": seed['panoId'],
                        "heading": 0,
                        "pitch": 0,
                        "zoom": 0,
                        "streakLocationCode": "cn"
                    }
                ],
            }
            return self.game

        elif self.map_id == 'baidu':
            self.pool = load_json('baidu_seeds.json')
            self.game = {
                "token": "a",
                "map": "baidu",
                "mapName": "湖山春社",
                "round": 1,
                "rounds": [
                    {
                        "lat": 40.34,
                        "lng": 116.35,
                        "panoId": random.choice(self.pool),
                        "heading": 0,
                        "pitch": 0,
                        "zoom": 0,
                        "streakLocationCode": "cn"
                    }
                ],
            }
            return self.game

        elif self.map_id == 'vn':
            self.pool = load_json('vn_seeds.json')
            seed = random.choice(self.pool)
            self.game = {
                "token": "a",
                "map": "vn",
                "mapName": "A Balanced Vietnam",
                "round": 1,
                "rounds": [
                    {
                        "lat": seed['lat'],
                        "lng": seed['lng'],
                        "panoId": seed['panoId'],
                        "heading": seed['heading'],
                        "pitch": 0,
                        "zoom": 0,
                        "streakLocationCode": "vn"
                    }
                ],
            }
            return self.game

        else:
            async with aiohttp.ClientSession() as session:
                game_response = await session.post(
                    "https://www.geoguessr.com/api/v3/games",
                    headers=self.headers,
                    json={
                        "map": self.map_id,
                        "type": "standard",
                        "timeLimit": 0,
                        "forbidMoving": True,
                        "forbidZooming": True,
                        "forbidRotating": True
                    }
                )
                if game_response.status != 200:
                    logging.error(f"Error creating game: {game_response.status}")
                    self.game = None

                self.game = await game_response.json()

                return self.game

    async def guess_and_advance(self):
        """
        Guesses at (0, 0) and advances to the next round.
        """
        logging.info("guess_and_advance")

        if self.game['round'] >= 5:
            if not self.map_id:
                self.map_id = DEFAULT_MAP['map_id']
            await self.create_geoguessr_game(self.map_id)
        if not self.game:
            return None

        if self.map_id not in ['baidu', 'qq', 'vn']:
            game_id = self.game['token']

            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"https://www.geoguessr.com/api/v3/games/{game_id}",
                    headers=self.headers,
                    json={
                        "token": game_id,
                        "lat": 0,
                        "lng": 0,
                        "timedOut": False,
                        "stepsCount": 0
                    }
                )
                if response.status != 200:
                    logging.error(f"Error getting game data: {response.status}")
                    return None

                self.game = await response.json()

                # Advance to next round
                self.game = await session.get(
                    f"https://www.geoguessr.com/api/v3/games/{game_id}",
                    headers=self.headers
                )

                if response.status != 200:
                    logging.error(f"Error advancing: {response.status}")
                    return None

                self.game = await self.game.json()
                logging.info(str(self.game['round']) + " - round begin")
                return self.game

        else:
            self.game['round'] += 1
            seed = random.choice(self.pool)
            self.game['rounds'].append(
                {
                    "lat": 40.34 if self.map_id == 'baidu' else seed['lat'],
                    "lng": 116.25 if self.map_id == 'baidu' else seed['lng'],
                    "panoId": seed if self.map_id == 'baidu' else seed['panoId'],
                    "heading": seed['heading'] if self.map_id == 'vn' else 0,
                    "pitch": 0,
                    "zoom": 0,
                    "streakLocationCode": "vn" if self.map_id == 'vn' else 'cn'
                }
            )
            logging.info(str(self.game['round']) + " - round begin")
            return self.game
