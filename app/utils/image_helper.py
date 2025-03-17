import aiohttp
import asyncio
import math
import gc
import io
from PIL import Image, ImageDraw
from io import BytesIO
from functools import lru_cache
from app.utils import E2P

MAX_CONCURRENT_REQUESTS=5

def process_image(image_data):
    image_bytes = io.BytesIO()
    image_data.save(image_bytes, format="PNG")
    image_bytes.seek(0)

    # 强制垃圾回收，释放不再使用的内存
    gc.collect()

    return image_bytes


async def fetch_tile(session, panoId, x, y, zoom, template, semaphore):
    """异步获取单个街景图瓦片"""
    async with semaphore:  # 限制并发请求数
        url = template.format(panoId=panoId, x=x, y=y, zoom=zoom)
        async with session.get(url) as response:
            if response.status == 200:
                return x, y, Image.open(BytesIO(await response.read()))
    return x, y, None


async def download_pano_async(panoId, width, height, zoom, template):
    """异步下载街景图的多个瓦片并拼接成完整图像"""
    tile_size = 512
    tiles_x, tiles_y = width // tile_size, height // tile_size
    canvas = Image.new("RGBA", (tiles_x * tile_size, tiles_y * tile_size))

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  # 限制并发请求数
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_tile(session, panoId, x, y, zoom, template, semaphore) for y in range(tiles_y) for x in range(tiles_x)]
        results = await asyncio.gather(*tasks)

        for x, y, tile in results:
            if tile:
                canvas.paste(tile, (x * tile_size, y * tile_size))
            del tile
    return canvas


@lru_cache(maxsize=1)  # 确保指南针底盘只加载一次
def load_compass_assets():
    """加载并缓存指南针底盘图像"""
    compass_size = 115
    image_size = compass_size + 10
    ellipse_image = Image.new("RGBA", (image_size, image_size), (255, 255, 255, 0))
    ellipse_draw = ImageDraw.Draw(ellipse_image)

    # 画圆形指南针底盘
    ellipse_draw.ellipse([5, 5, compass_size, compass_size], outline=(255, 255, 255, int(0.7 * 255)), width=24)

    return ellipse_image


def add_compass(image, heading):
    """在全景图片上添加指南针"""
    image_copy = image.copy()  # 创建副本，避免直接在原图上修改
    draw = ImageDraw.Draw(image_copy, "RGBA")

    # 获取缓存的指南针底盘
    ellipse_image = load_compass_assets()

    compass_size = 120
    compass_position = (18, image_copy.height - compass_size - 40)

    # 粘贴指南针底盘
    image_copy.paste(ellipse_image, compass_position, ellipse_image)

    # 计算指针角度和中心点
    angle = math.radians(360 - heading)
    center = (compass_position[0] + compass_size / 2, compass_position[1] + compass_size / 2)
    pointer_length = compass_size / 2 - 5
    pointer_width = 15

    # 计算红色指针的顶点
    end_x = center[0] + pointer_length * math.sin(angle)
    end_y = center[1] - pointer_length * math.cos(angle)

    points_red = [
        (center[0] + pointer_width * math.cos(angle), center[1] + pointer_width * math.sin(angle)),
        (center[0] - pointer_width * math.cos(angle), center[1] - pointer_width * math.sin(angle)),
        (end_x, end_y)
    ]
    draw.polygon(points_red, fill="red")

    # 计算白色指针的顶点
    end_x_white = center[0] - pointer_length * math.sin(angle)
    end_y_white = center[1] + pointer_length * math.cos(angle)

    points_white = [
        (center[0] + pointer_width * math.cos(angle + math.pi), center[1] + pointer_width * math.sin(angle + math.pi)),
        (center[0] - pointer_width * math.cos(angle + math.pi), center[1] - pointer_width * math.sin(angle + math.pi)),
        (end_x_white, end_y_white)
    ]
    draw.polygon(points_white, fill="white")

    return image_copy


async def get_perspective_pano(panoId, width, height, heading=0, oh=0, pitch=0):
    """下载全景图并转换为透视视角，添加指南针"""
    if len(panoId) == 23:
        template = "https://sv4.map.qq.com/tile?svid={panoId}&x={x}&y={y}&from=web&level=1"
    elif len(panoId) == 27:
        template = "https://mapsv0.bdimg.com/?qt=pdata&sid={panoId}&pos={y}_{x}&z={zoom}"
    else:
        template = "https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=apiv3&panoid={panoId}&output=tile&zoom={zoom}&x={x}&y={y}"

    # 下载街景图
    panorama = await download_pano_async(panoId, width, height, 5, template)

    # 转换 equirectangular 到 透视视角
    equ = E2P.Equirectangular(panorama)
    perspective = equ.GetPerspective(125, heading - oh, pitch, 1080, 1920)

    # 添加指南针
    final_image = add_compass(perspective, heading)

    # 强制垃圾回收，释放不再使用的内存
    gc.collect()

    return final_image