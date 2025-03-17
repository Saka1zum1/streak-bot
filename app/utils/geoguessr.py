import requests
import json
import random
import logging
from typing import Optional
import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeoGuessr:
    def __init__(self, user_agent: str, geoguessr_cookie: str):
        self.user_agent = user_agent
        self.geoguessr_cookie = geoguessr_cookie
        self.current_seed = None
        self.current_token = None
        self.base_url = "https://www.geoguessr.com/api/v3/games"

    async def _make_request(self, method: str, url: str, data: Optional[dict] = None) -> dict:
        """通用方法，用于发起 GET 或 POST 请求"""
        headers = {"Content-Type": "application/json", "User-Agent": self.user_agent, "Cookie": self.geoguessr_cookie}
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP request failed: {e.status} - {e.message}")
            return {}
        except aiohttp.ClientError as e:
            logger.error(f"Request error: {e}")
            return {}

    async def get_seed(self, tk: str):
        """获取当前回合的种子数据"""
        url = f"{self.base_url}/{tk}"
        data = await self._make_request("GET", url)

        if data.get('rounds'):
            self.current_seed = data['rounds'][-1]
            if len(data['rounds']) < 4:
                await self.make_guess(tk)
            else:
                self.current_token = await self.create_game()

    async def make_guess(self, tk: str):
        """提交一个随机猜测"""
        payload = {
            "token": tk,
            "lat": round(random.uniform(-60, 60), 2),
            "lng": round(random.uniform(-180, 180), 2),
            "timedOut": False,
            "stepsCount": random.randint(2, 8)
        }
        url = f"{self.base_url}/{tk}"
        await self._make_request("POST", url, payload)

    async def create_game(self, map_id) -> Optional[str]:
        """创建一个新的游戏并返回游戏 token"""
        payload = {
            "map": map_id,
            "type": "standard",
            "timeLimit": 0,
            "forbidMoving": False,
            "forbidZooming": False,
            "forbidRotating": False,
            "rounds": 5
        }
        url = self.base_url
        data = await self._make_request("POST", url, payload)
        return data.get('token')

    def get_current_seed(self) -> Optional[dict]:
        """返回当前游戏的种子信息"""
        return self.current_seed

    def get_current_token(self) -> Optional[str]:
        """返回当前游戏的 token"""
        return self.current_token
