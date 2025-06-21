import aiohttp
import asyncio
import certifi
import io
import os
import json
import logging
import requests
import math
import sqlite3
from math import radians, sin, cos, sqrt, atan2
from typing import Self
import numpy as np
from PIL import Image, ImageFile
from config import MAPS
from coordTransform import bd09mc_to_wgs84
from e2p import Equirectangular
from py360convert import c2e
from apple import get_apple_coverage_tile, get_apple_equ
from auth import Authenticator
from dotenv import load_dotenv
# from pypinyin import lazy_pinyin


load_dotenv()
BIGDATACLOUD_API_KEY = os.getenv("BIGDATACLOUD_API_KEY")

ImageFile.LOAD_TRUNCATED_IMAGES = True

auth = Authenticator()

GSV_PANO_URL = "https://geo0.ggpht.com/cbk"
BAIDU_PANO_URL = "https://mapsv0.bdimg.com/?qt=pdata"
TENCENT_PANO_URL = "https://sv0.map.qq.com/tile"
YANDEX_PANO_URL = "https://pano.maps.yandex.net"
KAKAO_PANO_URL = "https://map0.daumcdn.net/map_roadview"
BING_PREFIX = "BING:"
APPLE_PREFIX = "APPLE:"
BAIDU_PREFIX = "BAIDU:"
KAKAO_PREFIX = "KAKAO:"
TENCENT_PREFIX = "TENCENT:"
YANDEX_PREFIX = "YANDEX:"
OPENMAP_PREFIX = "OPENMAP:"
GOOGLE_TO_KAKAO_ZOOM = [0, 0, 1, 1, 2]
KAKAO_HORZ_TILES = [1, 8, 16]


def strip_panoid(pano, prefix):
    return pano.replace(prefix, "")


def get_host_city(pano):
    if pano:
        parts = str(pano).split(':')
        if len(parts) > 1:
            return parts[0]


class Pano:
    """
    A GSV panorama, with a unique ID and image file.
    """

    def __init__(self, pano_id=None, lat=None, lng=None):
        self.zoom = 4
        self.dimensions = None
        self.driving_direction = None
        self.origin_heading = None
        self.image_key = None
        self.apple_pano = None

        if not pano_id:
            self.pano_id = None
        else:
            self.pano_id = self.convert_pano_id(pano_id)

        if lat is not None and lng is not None:
            self.lat = lat
            self.lng = lng
        else:
            self.lat = None
            self.lng = None

        self.panorama = None
        self.img = None

    async def get_panorama(self, heading, pitch, FOV=125):
        if self.pano_id is None:
            self.pano_id = await self.get_panoid()

        if self.panorama is None:
            if "BING:" == str(self.pano_id)[0:5]:
                self.dimensions = [4096, 8192]
                await self.get_pano_metadata_bing()
            elif "APPLE:" == str(self.pano_id)[0:6]:
                self.apple_pano = await self.get_pano_metadata_apple()
                self.dimensions = [2280, 4560]
            elif "OPENMAP:" == str(self.pano_id)[0:8]:
                self.driving_direction = heading
                self.dimensions = [2880, 5760]
            elif "BAIDU:" == str(self.pano_id)[0:6]:
                # await self.get_pano_metadata_bd()
                self.dimensions = [4096, 8192]
                self.driving_direction = heading
            elif "TENCENT:" == str(self.pano_id)[0:8]:
                self.dimensions = [4096, 8192]
                self.driving_direction = heading
            elif "YANDEX:" == str(self.pano_id)[0:7] or self.pano_id == 'yandex':
                self.pano_id = strip_panoid(self.pano_id, YANDEX_PREFIX)
                await self.get_pano_metadata_yd(self.lat, self.lng)
            elif 'KAKAO:' == str(self.pano_id)[0:6]:
                self.dimensions = [4096, 8192]
                await self.get_pano_metadata_kk()
            else:
                await self.get_pano_metadata()

            if "BING:" == str(self.pano_id)[0:5]:
                self.panorama = await self.build_bing_streetside_panorama()
            elif "APPLE:" == str(self.pano_id)[0:6]:
                with requests.Session() as session:
                    try:
                        self.panorama = await asyncio.to_thread(
                            get_apple_equ, self.apple_pano, 3, auth, session
                        )
                    except Exception as error:
                        logging.error(f"Error getting apple equirectangular pano: {error}")
                    finally:
                        session.close()
            else:
                self.panorama = await self._fetch_and_build_panorama()

        equ = Equirectangular(self.panorama)

        if "BING:" == str(self.pano_id)[0:5] or "TENCENT:" == str(self.pano_id)[0:8]:
            h = 0
        elif "YANDEX:" == str(self.pano_id)[0:7] or self.pano_id == 'yandex':
            h = 0
            pitch = 5 if self.zoom == 1 else 0
            FOV = 110
        elif "BAIDU:" == str(self.pano_id)[0:6]:
            h = 90
        elif str(self.pano_id)[0:6] in ["KAKAO:", 'APPLE:']:
            h = 180
        else:
            h = heading - self.driving_direction

        result = equ.GetPerspective(FOV, h, pitch, 1080, 1920)

        return result

    async def fetch_cube_tile(self, session, template, direction):
        tile_url = template.format(direction=direction,
                                   panoid=strip_panoid(self.pano_id, f"{get_host_city(self.pano_id)}:"))

        try:
            async with session.get(tile_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    tile_img = Image.open(io.BytesIO(image_data))
                    return tile_img
                else:
                    print(f"Error: Failed to download tile {tile_url}")
                    return None
        except Exception as e:
            print(f"Error: {e} while downloading tile {tile_url}")
            return None

    def create_cubemap(self, tiles):
        f, r, b, l, u, d = tiles

        tile_width, tile_height = f.size

        cubemap_width = 4 * tile_width
        cubemap_height = 3 * tile_height
        cubemap_img = Image.new('RGB', (cubemap_width, cubemap_height))

        cubemap_img.paste(u, (tile_width, 0))  # 上面 (第一行，中央)
        cubemap_img.paste(l, (0, tile_height))  # 左面 (第二行，左侧)
        cubemap_img.paste(f, (tile_width, tile_height))  # 前面 (第二行，中央)
        cubemap_img.paste(r, (2 * tile_width, tile_height))  # 右面 (第二行，右侧)
        cubemap_img.paste(b, (3 * tile_width, tile_height))  # 背面 (第二行，最右)
        cubemap_img.paste(d, (tile_width, 2 * tile_height))  # 下面 (第三行，中央)

        return np.array(cubemap_img)

    async def fetch_cube_tiles(self, template):
        directions = ['f', 'r', 'b', 'l', 'u', 'd']
        async with aiohttp.ClientSession() as session:
            tasks = []
            for direction in directions:
                task = self.fetch_cube_tile(session, template, direction)
                tasks.append(task)

            # 执行所有任务
            tiles = await asyncio.gather(*tasks)
            return tiles

    async def fetch_single_tile(self, session, x, y, retries=3):
        async def check_host_url(url):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
            except Exception as e:
                logging.error(f"Host check failed for {url}: {e}")
                return False

        if "OPENMAP:" == str(self.pano_id)[0:8]:
            host_1 = "https://storage.nambox.com/streetview-cdn/derivates/"
            host_2 = "https://hn.storage.weodata.vn/streetview-cdn/derivates/"
            param_url = (
                f"{strip_panoid(self.pano_id, OPENMAP_PREFIX)[0:2]}/{strip_panoid(self.pano_id, OPENMAP_PREFIX)[2:4]}/"
                f"{strip_panoid(self.pano_id, OPENMAP_PREFIX)[4:6]}/{strip_panoid(self.pano_id, OPENMAP_PREFIX)[6:8]}/"
                f"{strip_panoid(self.pano_id, OPENMAP_PREFIX)[9:]}/tiles/{x}_{y}.jpg")
            TILE_URL = f"{host_1}{param_url}" if await check_host_url(
                f"{host_1}{param_url}") else f"{host_2}{param_url}"
            params = None
        elif 'KAKAO:' == str(self.pano_id)[0:6]:

            def get_tile_index(zoom, tile_x, tile_y):
                w = KAKAO_HORZ_TILES[zoom]
                return (tile_y + 1) * w + (tile_x - w) + 1

            def get_tile_image_name(image_path):
                return image_path.split("/")[-1]

            def build_tile_url(image_path, zoom, tile_x, tile_y):
                zoom = GOOGLE_TO_KAKAO_ZOOM[zoom - 1]
                tile_index = str(get_tile_index(zoom, tile_x, tile_y)).zfill(zoom + 1)

                if zoom == 1:
                    return f"{KAKAO_PANO_URL}{image_path}/{get_tile_image_name(image_path)}_{tile_index}.jpg"
                elif zoom == 2:
                    return f"{KAKAO_PANO_URL}{image_path}_HD1/{get_tile_image_name(image_path)}_HD1_{tile_index}.jpg"

            TILE_URL = build_tile_url(self.image_key, 5, x, y)

            params = None

        elif "BAIDU:" == str(self.pano_id)[0:6]:
            TILE_URL = BAIDU_PANO_URL
            params = {
                "qt": "pdata",
                "sid": strip_panoid(self.pano_id, BAIDU_PREFIX),
                "pos": str(y) + '_' + str(x),
                "z": 5
            }
        elif "TENCENT:" == str(self.pano_id)[0:8]:
            TILE_URL = TENCENT_PANO_URL
            params = {
                "svid": strip_panoid(self.pano_id, TENCENT_PREFIX),
                "x": x,
                "y": y,
                "level": 2 if self.dimensions[1] == 7168 else 1,
                "from": "web"
            }
        elif "YANDEX:" == str(self.pano_id)[0:7]:
            TILE_URL = f"{YANDEX_PANO_URL}/{self.image_key}/{self.zoom}.{x}.{y}"
            params = None

        else:
            TILE_URL = GSV_PANO_URL
            params = {
                "cb_client": "apiv3",
                "panoid": self.pano_id,
                "output": "tile",
                "zoom": self.zoom,
                "x": x,
                "y": y
            }

        for attempt in range(retries):
            try:
                async with session.get(TILE_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        logging.error(f"Error fetching tile {x},{y}: Status {response.status}")
                        if attempt < retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return None
                    data = await response.read()
                    tile = Image.open(io.BytesIO(data))
                    return tile
            except Exception as e:
                logging.error(f"Exception fetching tile {x},{y}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                    continue
                return None

    async def _fetch_and_build_panorama(self):
        if self.dimensions[1] == 8192:  # google Gen 4, qq, baidu, kakao
            max_x, max_y = 16, 8
        elif self.dimensions[1] == 6656:  # Gen 3
            max_x, max_y = 13, 6.5
        elif self.dimensions[1] == 5760:
            max_x, max_y = 8, 4
        elif self.dimensions[1] == 7168:
            max_x, max_y = 8, 2
        else:  # Fallback
            max_x, max_y = 7, 4

        if "YANDEX:" == str(self.pano_id)[0:7]:
            max_x, max_y = math.ceil(self.dimensions[1] / 256), math.ceil(self.dimensions[0] / 256)
            # if self.dimensions[0] == 2560:
            #     max_x, max_y = 28, 10
            # else:
            #     max_x, max_y = 28, 14
            # if self.dimensions[1] == 6912:
            #     max_x, max_y = 27, 14

        async with aiohttp.ClientSession() as session:
            # Get tiles based on determined dimensions
            raw_tiles = await asyncio.gather(
                *[self.fetch_single_tile(session, x, y)
                  for y in range(int(max_y) if max_y != 6.5 else 7)  # Handle Gen 3's 6.5
                  for x in range(max_x)]
            )

            if max_y == 6.5:  # Handle Gen 3's half row
                tiles = []
                # First 6 rows
                for y in range(6):
                    for x in range(13):
                        idx = y * max_x + x
                        tiles.append(raw_tiles[idx])

                # Half of 7th row
                for x in range(13):
                    idx = 6 * max_x + x
                    tile = raw_tiles[idx]
                    if tile is None:
                        continue
                    tile_array = np.array(tile)
                    half_height = tile_array.shape[0] // 2
                    half_tile = Image.fromarray(tile_array[:half_height])
                    tiles.append(half_tile)

                return self._stitch_panorama(tiles, max_x, max_y)
            else:
                return self._stitch_panorama(raw_tiles, max_x, max_y)

    def _stitch_panorama(self, tiles, max_x, max_y):
        # 根据 dimensions 和 pano_id 设置 tile 尺寸
        dimensions_map = {5760: (720, 720), 7168: (896, 896)}
        tile_width, tile_height = dimensions_map.get(self.dimensions[1], (512, 512))
        if "YANDEX:" == str(self.pano_id)[0:7]:
            tile_width, tile_height = 256, 256

        # 检查是否是半高模式
        is_half_height = max_y % 1 != 0
        full_height = int(max_y)

        # 计算总高度
        last_row_height = tile_height // 2 if is_half_height else 0
        total_height = (full_height * tile_height) + last_row_height

        total_width = int(max_x * tile_width)

        if "YANDEX:" == str(self.pano_id)[0:7]:
            if self.zoom == 1:
                total_height = 3584
            else:
                total_height, total_width = self.dimensions[0], self.dimensions[1]
                if self.dimensions[1] == 5632:
                    total_height = 2816

        full_panorama = Image.new('RGB', (total_width, total_height))

        # 拼接图像
        for idx, img in enumerate(tiles):
            x = (idx % int(max_x)) * tile_width
            y = (idx // int(max_x)) * tile_height

            # 如果是半高模式，调整最后一行的位置
            if is_half_height and y == full_height * tile_height:
                y += last_row_height

            full_panorama.paste(img, (x, y))

        return np.array(full_panorama)

    async def get_panoid(self):
        url = "https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1.MapsJsInternalService/SingleImageSearch"

        headers = {
            "Content-Type": "application/json+protobuf"
        }
        radius = 50
        payload = f'[["apiv3"],[[null,null,{self.lat},{self.lng}],{radius}],[[null,null,null,null,null,null,null,null,null,null,[null,null]],null,null,null,null,null,null,null,[1],null,[[[2,true,2]]]],[[2,6]]]'

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers) as response:
                try:
                    data = await response.json()
                    return data[1][1][1]
                except Exception as e:
                    logging.error(f"Error getting panoid: {e}")

    async def get_pano_metadata_apple(self):
        async with aiohttp.ClientSession() as session:
            try:
                apple_pano = await get_apple_coverage_tile(self.lat, self.lng, session)
                if not apple_pano:
                    logging.error("Error getting apple metadata.")
                    return None
                else:
                    return apple_pano

            except Exception as error:
                logging.error(f"Error fetching apple metadata: {error}")
                return None

    async def get_pano_metadata_bing(self):
        url = f"https://t.ssl.ak.tiles.virtualearth.net/tiles/cmd/StreetSideBubbleMetaData?id={strip_panoid(self.pano_id, BING_PREFIX)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                try:
                    if resp.status == 200:
                        text = await resp.text()
                        parsed = json.loads(text)
                        self.driving_direction = parsed[1].get("he")
                    else:
                        logging.error("Error getting bing metadata.")
                        return None

                except Exception:
                    logging.error(f"Error fetching bing metadata")
                    return None

    async def get_pano_metadata_yd(self, lat, lng):
        endpoint = 'sta' if self.pano_id == "air" else 'stv'
        YANDEX_SEARCH_URL = f"https://api-maps.yandex.com/services/panoramas/1.x/?l={endpoint}&lang=en_US&origin=userAction&provider=streetview"
        url = f"{YANDEX_SEARCH_URL}&ll={lng}%2C{lat}" if self.pano_id == 'yandex' else f"{YANDEX_SEARCH_URL}&oid={strip_panoid(self.pano_id, YANDEX_PREFIX)}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                try:
                    data = await response.json()
                    if data and 'data' in data and 'Data' in data['data'] and 'Images' in data['data']['Data']:
                        tiles_size = data['data']['Data']['Images']['Zooms']
                        if len(tiles_size) > 4:
                            self.dimensions = [tiles_size[1]['height'], tiles_size[1]['width']]
                            self.zoom = 1
                        else:
                            self.dimensions = [tiles_size[0]['height'], tiles_size[0]['width']]
                            self.zoom = 0
                        self.pano_id = f"YANDEX:{data['data']['Data']['panoramaId']}"
                        self.image_key = data['data']['Data']['Images']['imageId']
                        self.driving_direction = (data['data']['Data']['EquirectangularProjection']['Origin'][
                                                      0] + 180) % 360
                        return
                    else:
                        logging.error("Error fetching imageKey: Data format invalid.")
                        return None

                except Exception as error:
                    logging.error(f"Error fetching imageKey: {str(error)}")
                    return None

    async def get_pano_metadata_kk(self):

        KAKAO_METADATA_URL = "https://rv.map.kakao.com/roadview-search/v2/node"
        KAKAO_SEARCH_URL = "https://rv.map.kakao.com/roadview-search/v2/nodes?TYPE=w&SERVICE=glpano"

        url = f"{KAKAO_METADATA_URL}/{strip_panoid(self.pano_id, KAKAO_PREFIX)}?SERVICE=glpano"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                try:
                    data = await response.json()
                    if data and 'street_view' in data and 'street' in data['street_view']:
                        kakao = data['street_view']['street']
                        self.driving_direction = float(kakao['angle'])
                        self.image_key = kakao['img_path']
                        return
                    else:
                        logging.error("Error fetching imagePath: Data format invalid.")
                        return None

                except Exception as error:
                    logging.error(f"Error fetching imagePath: {str(error)}")
                    return None

    async def get_pano_metadata(self, retry_count=0, max_retries=3):
        if self.dimensions and self.driving_direction:
            return self.dimensions, self.driving_direction
        if retry_count >= max_retries:
            logging.error("Max retries reached, giving up on fetching metadata.")
            return None
        url = "https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1.MapsJsInternalService/GetMetadata"

        headers = {
            "Content-Type": "application/json+protobuf"
        }

        request_data = [
            ["apiv3", None, None, None, "US", None, None, None, None, None, [[0]]],
            ["en", "US"],
            [[[2, self.pano_id]]],
            [[1, 2, 3, 4, 8, 6]]
        ]

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=request_data, headers=headers) as response:
                try:
                    data = await response.json()
                    if data[1] and data[1][0] and data[1][0][2]:
                        self.dimensions = data[1][0][2][3][0][4][0]  # [height, width]
                        self.driving_direction = data[1][0][5][0][1][2][0]  # Driving direction
                        logging.info(f"Metadata: {self.dimensions}, {self.driving_direction}")
                        return self.dimensions, self.driving_direction
                    else:
                        logging.info("Start fetching metadata from latLng.")
                        if self.lat and self.lng:
                            try:
                                self.pano_id = await self.get_panoid()
                                logging.info(f"Valid pano_id: {self.pano_id}")
                                return await self.get_pano_metadata(retry_count + 1,
                                                                    max_retries)
                            except Exception as retry_error:
                                logging.error(f"Error fetching pano_id or retrying metadata: {retry_error}")
                except Exception as e:
                    logging.error(f"Error getting metadata: {e}")
                    return None

    async def get_pano_metadata_bd(self):
        url = f'https://mapsv0.bdimg.com/?qt=sdata&sid={strip_panoid(self.pano_id, BAIDU_PREFIX)}'
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'content' in data and len(data['content']) >= 1:
                            metadata = data['content'][0]
                            if metadata:
                                wgs84 = bd09mc_to_wgs84(metadata['X'] / 100, metadata['Y'] / 100)
                                self.lat, self.lng = wgs84[1], wgs84[0]
                                self.dimensions = [4096, 8192]
                                self.driving_direction = metadata['MoveDir']
                    return None
            except Exception as error:
                logging.error(f"Error getting metadata: {error}")
                return None

    async def get_pano_metadata_qq(self):
        url = f'https://sv.map.qq.com/sv?svid={strip_panoid(self.pano_id, TENCENT_PREFIX)}&output=jsonp'
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None  # 直接返回，减少嵌套

                    content = await response.text()  # 处理响应文本
                    prefix, suffix = "qqsvcallback&&qqsvcallback(", ")"

                    if content.startswith(prefix) and content.endswith(suffix):
                        jsonp_data = content[len(prefix):-1]  # 提取 JSONP 内容
                    else:
                        return None  # 格式不对，返回 None

                    try:
                        data = json.loads(jsonp_data)  # 解析 JSON
                    except json.JSONDecodeError:
                        return None  # 解析失败

                    metadata = data.get("detail", {}).get("basic")  # 获取元数据

                    if not metadata:
                        return None
                    tile_size = metadata.get("tile_height")
                    if not tile_size or tile_size != '512':
                        self.dimensions = [1792, 7168]
                    self.driving_direction = float(metadata["dir"])
            except Exception as error:
                logging.error(f"Error fetching metadata: {error}")
                return None

    @staticmethod
    def convert_pano_id(pano_id):
        """
        Convert GeoGuessr hex-encoded pano ID to base64-encoded pano ID.
        """
        try:
            decoded = bytes.fromhex(pano_id).decode()
            return decoded
        except ValueError:
            return pano_id
        except Exception as e:
            logging.error(f"Error: {e}")
            return pano_id

    @staticmethod
    def add_compass(image: np.ndarray, heading: float, output_path: str = 'image.jpg'):
        """
        Add a compass overlay to an image.
        
        Args:
            image: numpy array of the image
            heading: Heading angle in degrees (0-360)
            output_path: Path to save the resulting image
        """
        try:
            # Convert numpy array to PIL Image
            main_image = Image.fromarray(image)
            compass = Image.open('compass.png')

            compass_size = int(min(main_image.size) * 0.15)  # 15% of smaller dimension
            compass = compass.resize((compass_size, compass_size), Image.Resampling.LANCZOS)

            compass = compass.convert('RGBA')
            rotated_compass = compass.rotate(heading, expand=False, resample=Image.Resampling.BICUBIC)

            # Calculate position (bottom left with padding)
            padding = int(compass_size * 0.2)  # 20% of compass size as padding
            position = (padding, main_image.size[1] - compass_size - padding)

            result = main_image.convert('RGBA')
            result.paste(rotated_compass, position, rotated_compass)

            result = result.convert('RGB')
            return result

        except Exception as e:
            logging.error(f"Error adding compass overlay: {e}")

    @staticmethod
    def to_base4(n: int) -> str:
        """
        Converts an integer to a base 4 string.

        :param n: The integer.
        :return: The base 4 representation of the integer.
        """
        return np.base_repr(n, 4)

    @staticmethod
    def quadtree_position_to_xy(position: str, width: int = 8) -> tuple[int, int]:
        """将四进制字符串 position 转换为 (x, y) 坐标"""
        x = 0
        y = 0
        for j, ch in enumerate(position):
            delta = width / (2 ** (j + 1))
            if ch == "1":
                x += delta
            elif ch == "2":
                y += delta
            elif ch == "3":
                x += delta
                y += delta
        return int(x), int(y)

    async def fetch_bing_streetside_tiles(self, pano_id, ZOOM=3):
        id4 = self.to_base4(int(pano_id)).rjust(16, "0")
        WIDTH = 2 ** ZOOM  # 8
        tiles = [[None for _ in range(WIDTH * WIDTH)] for _ in range(6)]  # 6 faces

        semaphore = asyncio.Semaphore(128)

        async def fetch_tile(session, face, position):
            face4 = self.to_base4(face + 1).rjust(2, "0")
            position4 = self.to_base4(position).rjust(ZOOM, "0")
            url = f"https://t.ssl.ak.tiles.virtualearth.net/tiles/hs{id4}{face4}{position4}.jpg?g=13716"

            try:
                async with semaphore:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            img_data = await resp.read()
                            img = Image.open(io.BytesIO(img_data)).convert("RGB")
                            return face, position, img
                        else:
                            return face, position, None
            except Exception as e:
                logging.error(f"Error downloading {url}: {e}")
                return face, position, None

        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_tile(session, face, position)
                for face in range(6)
                for position in range(WIDTH * WIDTH)
            ]
            results = await asyncio.gather(*tasks)

        for face, position, img in results:
            tiles[face][position] = img

        return tiles

    @staticmethod
    def stitch_bing_streetside_face(tiles: list, width: int = 8, tile_size: int = 256) -> Image.Image:
        """
        拼接单个面的64张tile为一张大图，tiles为长度64的PIL.Image列表
        """
        face_img = Image.new("RGB", (width * tile_size, width * tile_size))
        for idx, tile in enumerate(tiles):
            if tile is None:
                continue
            pos_str = Pano.to_base4(idx).zfill(3)
            x, y = Pano.quadtree_position_to_xy(pos_str, width)
            face_img.paste(tile, (x * tile_size, y * tile_size))
        return face_img

    async def build_bing_streetside_panorama(self):
        """
        下载并拼接 Bing Streetside 全景图，返回equirectangular numpy数组
        """
        tiles = await self.fetch_bing_streetside_tiles(strip_panoid(self.pano_id, BING_PREFIX))
        faces = [self.stitch_bing_streetside_face(face_tiles) for face_tiles in tiles]
        cubemap_img = self.create_cubemap(faces)
        # 转为equirectangular
        equirectangular_array = c2e(np.array(cubemap_img), 2048, 4096)
        return equirectangular_array

    def to_dict(self):
        """Return a JSON-serializable representation of the Pano"""
        return {
            'pano_id': self.pano_id,
            'zoom': self.zoom,
            'dimensions': self.dimensions,
            'driving_direction': self.driving_direction
        }


class Round:
    """
    A round in a GeoGuessr game.

    Attributes:
        pano (Pano): Panorama object
        heading (float): Camera heading
        pitch (float): Camera pitch
        zoom (float): Camera zoom
        lat (float): Latitude
        lng (float): Longitude
        subdivision (str): Subdivision name
        locality (str): Locality name
    """

    def __init__(self, round_data):

        self.pano = Pano(pano_id=round_data['panoId'], lat=round_data['lat'], lng=round_data['lng']) if round_data[
            'panoId'] else Pano(lat=round_data['lat'], lng=round_data['lng'])
        self.heading = round_data['heading']
        self.pitch = round_data['pitch']
        self.zoom = round_data['zoom']
        self.lat = round_data['lat']
        self.lng = round_data['lng']
        self.country = None
        self.subdivision = None
        self.adm_2 = None
        self.locality = None
        self.pool = []

    async def get_location_info(self, lat: float, lng: float, mode: str):
        """Get location info from BigDataCloud reverse geocoding API
        
        Args:
            lat (float): Latitude
            lng (float): Longitude

        Returns:
            tuple:
                subdivision (str): Subdivision name
                locality (str): Locality name
        """
        url = "https://api.bigdatacloud.net/data/reverse-geocode"
        language = "en"
        # if self.pano.pano_id:
        #     if "BAIDU:" in str(self.pano.pano_id) or "TENCENT:" in str(self.pano.pano_id):
        #         language = "zh-Hans"
        params = {
            "latitude": lat,
            "longitude": lng,
            "localityLanguage": language,
            "key": BIGDATACLOUD_API_KEY
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                logging.debug(f"Reverse geocoding status: {response.status}")
                if response.status == 403:
                    logging.error("API key not set or not authorized")
                    exit(1)
                if response.status != 200:
                    logging.error("Geocoding error")
                    return None

                data = await response.json()
                country = data.get("countryCode")
                self.country = country
                adm_1, adm_2 = None, None

                if country == "ID":
                    for admin in data.get("localityInfo", {}).get("administrative", []):
                        if admin.get("adminLevel") == 4:
                            if mode == 'state':
                                adm_1 = admin.get("isoCode", "Unknown")[3:]
                            else:
                                adm_1 = admin.get("name")
                elif country in ["MO", "HK", "CX", "CC"]:
                    adm_1 = data.get("countryCode") if mode == 'state' else data.get("countryName")
                else:
                    adm_1 = data.get('principalSubdivisionCode', '')
                    if not adm_1:
                        for admin in data.get("localityInfo", {}).get("administrative", []):
                            if country in ['VN', 'AU', 'ES', 'KZ'] and admin.get("adminLevel") == 4:
                                adm_1 = admin.get("name")
                            if admin.get("isoCode") and country in admin.get("isoCode"):
                                if admin.get("adminLevel") == 4:
                                    adm_1 = admin.get("isoCode", "Unknown")[3:]
                                elif country == 'PH' and admin.get("adminLevel") == 3:
                                    adm_1 = admin.get("name", "Unknown")
                        if country == 'AR' and data.get('city'):
                            adm_1 = data.get('city')
                    elif mode != 'state':
                        adm_1 = data.get('principalSubdivision')
                    else:
                        if adm_1 == 'KP-03':
                            adm_1 = 'Liaoning'
                        elif adm_1 == 'KP-09':
                            adm_1 = 'Jilin'
                        else:
                            adm_1 = adm_1[3:]

                for admin in data.get("localityInfo", {}).get("administrative", []):
                    if admin.get("adminLevel") == 5:
                        adm_2 = admin.get("name")
                        if country == "CN" and adm_2:
                            self.pool.extend([
                                "".join(adm_2),
                                "".join(adm_2[:-1])])
                            """self.pool.extend([
                                "".join(lazy_pinyin(adm_2)),
                                "".join(lazy_pinyin(adm_2[:-1]))])"""

                # Return appropriate values based on mode
                return (adm_1, adm_2, data.get('locality')) if mode == 'state' else (
                    country, adm_1, data.get('locality'))

    async def set_subdivision(self, round_data, mode=None):
        self.subdivision, self.adm_2, self.locality = await self.get_location_info(
            round_data.get('lat'),
            round_data.get('lng'),
            mode)

        self.pool.extend(filter(None, [self.subdivision and self.subdivision.lower(),
                                       self.locality and self.locality.lower(),
                                       # self.locality and self.country == 'CN' and "".join(lazy_pinyin(self.locality)),
                                       # self.locality and self.country == 'CN' and "".join(
                                       #     lazy_pinyin(self.locality[0:-1])),
                                       self.adm_2 and self.adm_2.lower()]))
        logging.info(self.pool)

        return self.subdivision, self.adm_2, self.locality

    @staticmethod
    async def reconstruct_round(round_data: dict, pano_processor) -> Self:
        """Helper to reconstruct a Round object from saved data"""
        pano_data = round_data['pano']
        round_obj = Round({
            'panoId': pano_data['pano_id'],
            'heading': round_data['heading'],
            'pitch': round_data['pitch'],
            'zoom': round_data['zoom'],
            'lat': round_data['lat'],
            'lng': round_data['lng']
        })
        round_obj.subdivision = round_data['subdivision']
        round_obj.adm_2 = round_data['adm_2'] if 'adm_2' in round_data else None
        round_obj.locality = round_data['locality'] if 'locality' in round_data else None

        await pano_processor.process_pano(
            round_obj.pano,
            round_obj.heading,
            round_obj.pitch
        )
        return round_obj

    def to_dict(self):
        """Return a JSON-serializable representation of the Round"""
        return {
            'pano': self.pano.to_dict(),
            'heading': self.heading,
            'pitch': self.pitch,
            'zoom': self.zoom,
            'lat': self.lat,
            'lng': self.lng,
            'subdivision': self.subdivision,
            'adm_2': self.adm_2,
            'locality': self.locality,
            'pool': self.pool
        }

    @property
    def tile_link(self):
        zoom = 10

        def lon2tile(lng, zoom):
            return int((lng + 180) / 360 * (2 ** zoom))

        def lat2tile(lat, zoom):
            return int(
                (1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * (
                        2 ** zoom))

        tileX = lon2tile(self.pano.lng or self.lng, zoom)
        tileY = lat2tile(self.pano.lat or self.lat, zoom)

        return f"https://www.google.com/maps/vt?pb=!1m5!1m4!1i{zoom}!2i{tileX}!3i{tileY}!4i256!2m1!2sm!3m17!2sen!3sUS!5e18!12m4!1e68!2m2!1sset!2sRoadmap!12m3!1e37!2m1!1ssmartmaps!12m4!1e26!2m2!1sstyles!2ss.e:l|p.v:on,s.t:0.8|s.e:g.s|p.v:on!5m1!5f1.5"

    @property
    def link(self):
        if "APPLE:" == str(self.pano.pano_id)[0:6]:
            return (f"https://lookmap.eu.pythonanywhere.com/#c=12/{self.pano.apple_pano.lat}/{self.pano.apple_pano.lon}"
                    f"&p={self.pano.apple_pano.lat}/{self.pano.apple_pano.lon}&a={self.pano.driving_direction}/0")
        elif "BING:" == str(self.pano.pano_id)[0:5]:
            return f"https://www.bing.com/maps/?cp={self.lat}%7E{self.lng}&dir={self.pano.driving_direction}&pi={self.pitch}&style=x&lvl=9.0"
        elif "BAIDU:" == str(self.pano.pano_id)[0:6]:
            return f"https://map.baidu.com/?newmap=1&shareurl=1&panoid={strip_panoid(self.pano.pano_id, BAIDU_PREFIX)}&panotype=street&heading={self.heading}&pitch={self.pitch}&l=21&tn=B_NORMAL_MAP&sc=0&newmap=1&shareurl=1&pid={strip_panoid(self.pano.pano_id, BAIDU_PREFIX)}"
        elif "OPENMAP:" == str(self.pano.pano_id)[0:8]:
            return f"https://vn-map.netlify.app/#zoom=19&center={self.lat}%2C{self.lng}&pano={strip_panoid(self.pano.pano_id, OPENMAP_PREFIX)}&ppos={self.lat}%2C{self.lng}&heading={self.heading}&pitch=0&svz=0"
        elif "TENCENT:" == str(self.pano.pano_id)[0:8]:
            return f"https://qq-map.netlify.app/#base=roadmap&zoom=18&center={self.lat}%2C{self.lng}&pano={strip_panoid(self.pano.pano_id, TENCENT_PREFIX)}&heading={self.pano.driving_direction or 0}&pitch=0&svz=0"
        elif "YANDEX:" == str(self.pano.pano_id)[0:7]:
            return f"https://yandex.com/maps/?l=stv%2Csta&ll={self.lng}%2C{self.lat}&panorama%5Bdirection%5D={self.pano.driving_direction or self.heading}%2C0&panorama%5Bfull%5D=true&panorama%5Bid%5D={strip_panoid(self.pano.pano_id, YANDEX_PREFIX)}&panorama%5Bpoint%5D={self.lng}%2C{self.lat}"
        elif 'KAKAO:' == str(self.pano.pano_id)[0:6]:
            return f"https://map.kakao.com/?map_type=TYPE_MAP&map_attribute=ROADVIEW&panoid={strip_panoid(self.pano.pano_id, KAKAO_PREFIX)}&pan={self.heading}"

        return f"https://www.google.com/maps/@?api=1&map_action=pano&pano={self.pano.pano_id}&heading={self.heading}&pitch={self.pitch}"


class GameManager:
    """
    A game manager that handles state of individual channels.

    Attributes:
        db_path (str): Path to the SQLite database file
        subdivisions (list): List of subdivisions to use for location info
        rounds (dict): Current round data for each channel
        next_rounds (dict): Next round data for each channel
        waiting_for_guess (dict): Whether a channel is waiting for a guess
        streak (dict): Current streak count for each channel
        five_k_attempts (dict): 5k attempts for each user in each channel
    """

    def __init__(self, subdivisions, db_path="game_state.db"):
        self.db_path = db_path
        self.subdivisions = subdivisions
        self._init_db()
        self.rounds = {}
        self.next_rounds = {}
        self.waiting_for_guess = {}

        self.streak = {}
        self.five_k_attempts = {}

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Existing game state table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_state (
                    channel_id INTEGER PRIMARY KEY,
                    streak INTEGER,
                    game_data TEXT,
                    current_round TEXT,
                    next_round TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS maps (
                    map_id TEXT PRIMARY KEY,
                    map_name TEXT
                )
            """)

            for map_id, map_info in MAPS.items():
                map_name = map_info[0]  # First element is the full name
                conn.execute("""
                    INSERT OR IGNORE INTO maps (map_id, map_name)
                    VALUES (?, ?)
                """, (map_id, map_name))

            # New rounds history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rounds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER,
                    user_id INTEGER,
                    streak_id INTEGER,
                    pano_id TEXT,
                    actual_location TEXT,
                    guessed_location TEXT,
                    is_correct BOOLEAN,
                    lat REAL,
                    lng REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    map TEXT,
                    FOREIGN KEY(channel_id) REFERENCES game_state(channel_id)
                    FOREIGN KEY(streak_id) REFERENCES streaks(id)
                    FOREIGN KEY(map) REFERENCES maps(map_id)
                )
            """)

            # Create some useful views for leaderboards
            conn.execute("""
                CREATE VIEW IF NOT EXISTS player_stats AS
                WITH streak_counts AS (
                    SELECT 
                        streak_id,
                        COUNT(*) AS participant_count
                    FROM streak_participants
                    GROUP BY streak_id
                ),
                streak_stats AS (
                    SELECT 
                        sp.user_id,
                        r.map,
                        MAX(CASE WHEN sc.participant_count = 1 THEN s.number ELSE 0 END) AS best_solo_streak,
                        MAX(CASE WHEN sc.participant_count > 1 THEN s.number ELSE 0 END) AS best_assisted_streak,
                        AVG(CASE WHEN sc.participant_count = 1 THEN s.number ELSE NULL END) AS avg_solo_streak
                    FROM streak_participants sp
                    JOIN streaks s ON sp.streak_id = s.id
                    JOIN streak_counts sc ON s.id = sc.streak_id
                    JOIN rounds r ON r.user_id = sp.user_id AND r.streak_id = sp.streak_id
                    GROUP BY sp.user_id, r.map
                )
                SELECT 
                    r.user_id,
                    r.map,
                    COUNT(*) AS total_guesses,
                    SUM(CASE WHEN r.is_correct THEN 1 ELSE 0 END) AS correct_guesses,
                    ROUND(AVG(CASE WHEN r.is_correct THEN 100.0 ELSE 0 END), 1) AS accuracy,
                    COALESCE(ss.best_solo_streak, 0) AS best_solo_streak,
                    COALESCE(ss.best_assisted_streak, 0) AS best_assisted_streak,
                    ROUND(COALESCE(ss.avg_solo_streak, 0), 2) AS avg_solo_streak
                FROM rounds r
                LEFT JOIN streak_stats ss
                    ON r.user_id = ss.user_id AND r.map = ss.map
                GROUP BY r.user_id, r.map;
            """)

            conn.execute("""
                CREATE VIEW IF NOT EXISTS player_subdivision_stats AS
                WITH player_location_stats AS (
                    SELECT 
                        user_id,
                        map,
                        actual_location,
                        COUNT(*) AS times_seen,
                        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS times_correct,
                        ROUND(AVG(CASE WHEN is_correct THEN 100.0 ELSE 0 END), 1) AS accuracy_rate,
                        MAX(timestamp) AS last_seen
                    FROM rounds
                    GROUP BY user_id, map, actual_location
                )
                SELECT 
                    user_id,
                    map,
                    actual_location,
                    times_seen,
                    times_correct,
                    accuracy_rate,
                    last_seen,
                    RANK() OVER (
                        PARTITION BY user_id, map
                        ORDER BY accuracy_rate ASC, times_seen DESC
                    ) AS hardest_rank,
                    RANK() OVER (
                        PARTITION BY user_id, map
                        ORDER BY accuracy_rate DESC, times_seen DESC
                    ) AS easiest_rank
                FROM player_location_stats
                WHERE times_seen >= 3;
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS streaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER,
                    number INTEGER NOT NULL,
                    start_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_timestamp DATETIME,
                    FOREIGN KEY(channel_id) REFERENCES game_state(channel_id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS streak_participants (
                    streak_id INTEGER,
                    user_id INTEGER,
                    guesses_count INTEGER DEFAULT 1,
                    PRIMARY KEY (streak_id, user_id),
                    FOREIGN KEY(streak_id) REFERENCES streaks(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS five_k_guesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id INTEGER NOT NULL,
                    FOREIGN KEY (round_id) REFERENCES rounds(id)
                );
            """)

    def log_round(self, channel_id: int, user_id: int, round_obj: Round, guess: str, actual: str, is_correct: bool,
                  map_id: str):
        """Updates the database with data of a completed round.
        
        Args:
            channel_id (int): Channel ID
            user_id (int): User ID
            round_obj (Round): Round object
            guess (str): Guessed location (user)
            actual (str): Actual location (game)
            is_correct (bool): Whether the guess was correct
        """
        with sqlite3.connect(self.db_path) as conn:
            streak_id = conn.execute("""
                SELECT id FROM streaks 
                WHERE channel_id = ? AND end_timestamp IS NULL
                ORDER BY id DESC LIMIT 1
            """, (channel_id,)).fetchone()

            if is_correct:
                streak_record = conn.execute("""
                    SELECT id FROM streaks 
                    WHERE channel_id = ? AND end_timestamp IS NULL
                    ORDER BY id DESC LIMIT 1
                """, (channel_id,)).fetchone()

                if streak_record:
                    streak_id = streak_record[0]
                    conn.execute("""
                        UPDATE streaks SET number = ?
                        WHERE id = ?
                    """, (self.streak.get(channel_id), streak_id,))
                else:
                    cursor = conn.execute("""
                        INSERT INTO streaks (channel_id, number)
                        VALUES (?, ?)
                    """, (channel_id, self.streak.get(channel_id, 1),))
                    streak_id = cursor.lastrowid

                if streak_id:
                    conn.execute("""
                        INSERT INTO streak_participants (streak_id, user_id)
                        VALUES (?, ?)
                        ON CONFLICT(streak_id, user_id) DO UPDATE SET
                        guesses_count = guesses_count + 1
                    """, (streak_id, user_id))
            else:
                streak_record = conn.execute("""
                    SELECT id FROM streaks 
                    WHERE channel_id = ? AND end_timestamp IS NULL
                    ORDER BY id DESC LIMIT 1
                """, (channel_id,)).fetchone()

                if streak_record:
                    streak_id = streak_record[0]
                    conn.execute("""
                        UPDATE streaks SET end_timestamp = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (streak_id,))
                streak_id = None

            cur = conn.execute("""
                INSERT INTO rounds (
                    channel_id, user_id, streak_id, pano_id, 
                    actual_location, guessed_location, is_correct, 
                    lat, lng, map
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                channel_id,
                user_id,
                streak_id,
                round_obj.pano.pano_id,
                actual,
                guess,
                is_correct,
                round_obj.lat,
                round_obj.lng,
                map_id
            ))
            return cur.lastrowid

    def save_state(self, channel_id: int, game_data: dict):
        with sqlite3.connect(self.db_path) as conn:
            current_round = json.dumps(self.rounds[channel_id].to_dict()) if channel_id in self.rounds else None
            next_round = json.dumps(self.next_rounds[channel_id].to_dict()) if channel_id in self.next_rounds else None

            conn.execute("""
                INSERT OR REPLACE INTO game_state 
                VALUES (?, ?, ?, ?, ?)
            """, (
                channel_id,
                self.streak.get(channel_id, 0),
                json.dumps(game_data),
                current_round,
                next_round
            ))

    def has_saved_state(self, channel_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM game_state WHERE channel_id = ?",
                (channel_id,)
            ).fetchone()
            return row is not None

    def load_state(self, channel_id: int) -> dict:
        """Load saved game state for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT streak, game_data, current_round, next_round FROM game_state WHERE channel_id = ?",
                (channel_id,)
            ).fetchone()

            if not row:
                return None

            return {
                'streak': row[0],
                'game_data': json.loads(row[1]) if row[1] else None,
                'current_round': json.loads(row[2]) if row[2] else None,
                'next_round': json.loads(row[3]) if row[3] else None
            }

    def end_streak(self, channel_id: int):
        """Force-end the current streak for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            # End any active streak
            streak_record = conn.execute("""
                SELECT id FROM streaks 
                WHERE channel_id = ? AND end_timestamp IS NULL
                ORDER BY id DESC LIMIT 1
            """, (channel_id,)).fetchone()

            if streak_record:
                streak_id = streak_record[0]
                conn.execute("""
                    UPDATE streaks SET end_timestamp = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (streak_id,))

            # Reset streak counter
            self.streak[channel_id] = 0

    async def check_if_top_streak(self, channel_id: int, streak_number: int) -> list:
        """
        Check if a streak is in any of the top 5 leaderboards.
        Returns a list of tuples (category, position) for leaderboards where the streak places.
        """
        achievements = []

        with sqlite3.connect(self.db_path) as conn:
            # Get the latest ended streak's participant info
            participants = conn.execute("""
                WITH latest_streak AS (
                    SELECT id, number 
                    FROM streaks 
                    WHERE channel_id = ? AND end_timestamp IS NULL
                    LIMIT 1
                )
                SELECT COUNT(DISTINCT user_id) as participant_count
                FROM streak_participants
                WHERE streak_id = (SELECT id FROM latest_streak)
            """, (channel_id,)).fetchone()

            if not participants:
                return achievements

            participant_count = participants[0]
            is_solo = participant_count == 1

            # Check all streaks category first
            base_query = """
                WITH streak_counts AS (
                    SELECT streak_id, COUNT(user_id) as participant_count
                    FROM streak_participants
                    GROUP BY streak_id
                ),
                ranked_streaks AS (
                    SELECT 
                        s.number,
                        RANK() OVER (ORDER BY s.number DESC) as position
                    FROM streaks s
                    JOIN streak_counts sc ON s.id = sc.streak_id
                    WHERE s.number > 0 {filter}
                )
                SELECT number, position
                FROM ranked_streaks
                WHERE position <= 5
                ORDER BY position
                """

            # Check "all" category
            all_top_streaks = conn.execute(base_query.format(filter="")).fetchall()
            if not all_top_streaks or streak_number >= min(s[0] for s in all_top_streaks):
                position = 1
                for rank, (number, _) in enumerate(all_top_streaks, 1):
                    if streak_number >= number:
                        position = rank
                        break
                    position = rank + 1
                if position <= 5:
                    achievements.append(("all", position))

            # Only check the specific category matching this streak's type
            category_filter = "AND sc.participant_count = 1" if is_solo else "AND sc.participant_count > 1"
            category_name = "solo" if is_solo else "assisted"

            category_top_streaks = conn.execute(base_query.format(filter=category_filter)).fetchall()
            if not category_top_streaks or streak_number >= min(s[0] for s in category_top_streaks):
                position = 1
                for rank, (number, _) in enumerate(category_top_streaks, 1):
                    if streak_number >= number:
                        position = rank
                        break
                    position = rank + 1
                if position <= 5:
                    achievements.append((category_name, position))

        return achievements

    def check_5k_guess(self, text: str) -> tuple[float, float] | None:
        """
        Check if text is a valid coordinate guess.
        Returns (lat, lng) tuple if valid, None otherwise.
        """
        text = text.lower().replace('!g', '').strip()

        try:
            parts = [p.strip() for p in text.split(',')]
            if len(parts) != 2:
                return None

            lat, lng = map(float, parts)

            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return None

            return (lat, lng)
        except (ValueError, IndexError):
            return None

    def verify_5k_guess(self, channel_id: int, user_id: int, guess_coords: tuple[float, float], round_obj: Round) -> \
            tuple[bool, float]:
        """
        Verify a 5K guess.
        Returns (is_correct, distance) tuple. First bool indicates if we can proceed (have attempts),
        distance is actual distance if we can proceed.
        """
        if not self.check_5k_attempts(channel_id, user_id):
            return (False, 0)

        distance = self.calculate_distance_meters(
            guess_coords[0], guess_coords[1],
            round_obj.lat, round_obj.lng
        )

        self.increment_5k_attempts(channel_id, user_id)

        return (True, distance)

    def reset_5k_attempts(self, channel_id):
        """Reset 5k attempts for a channel"""
        self.five_k_attempts[channel_id] = {}

    def check_5k_attempts(self, channel_id, user_id) -> bool:
        """Check if user has attempts remaining"""
        attempts = self.five_k_attempts.get(channel_id, {}).get(user_id, 0)
        return attempts < 5

    def increment_5k_attempts(self, channel_id, user_id):
        """Increment 5k attempts for a user"""
        if channel_id not in self.five_k_attempts:
            self.five_k_attempts[channel_id] = {}
        self.five_k_attempts[channel_id][user_id] = self.five_k_attempts[channel_id].get(user_id, 0) + 1

    def reset_subdivisions(self, subdivisions):
        self.subdivisions = subdivisions

    @staticmethod
    def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth's radius in meters

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c
