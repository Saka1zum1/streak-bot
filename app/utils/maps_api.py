import requests
import aiohttp
import time
import json
from app.config import GOOGLE_API_KEY
from app.config import AMAP_API_KEY
from app.utils.coordTransform import bd09mc_to_gcj02


last_token = None
last_token_expiry = 0


def parse_meta(data):
    if len(data) == 3:
        try:
            heading = data[1][5][0][1][2][0]
        except:
            heading = 90
        try:
            width = data[1][2][2][1]
            height = data[1][2][2][0]
        except:
            width = 16384
            height = 8192
        try:
            country = data[1][5][0][1][4]
            return [data[1][1][1], country, width, height, heading]
        except:
            return [data[1][1][1], None, width, height, heading]
    else:
        lat = data[1][0][5][0][1][0][2]
        lng = data[1][0][5][0][1][0][3]
        try:
            region = data[1][0][3][2][1][0]
        except:
            region = None

        try:
            address = data[1][0][3][2][0][0]
        except:
            address = None

        try:
            country = data[1][0][5][0][1][4]
        except:
            country = None

        if country in ['TW', 'HK', 'MO']:
            country = 'CN'
        if region:
            full_address = f"{address}, {region}"
        else:
            full_address = f"{address}, {country}"

        return {"lat": lat, "lng": lng, "address": full_address, "country": country}


def make_request(url, method='GET', headers=None, data=None):
    """通用的 HTTP 请求函数，支持 GET 和 POST 方法。"""
    try:
        if method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(data))
        else:
            response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Error {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except ValueError as ve:
        print(f"Response Error: {ve}")
    return None


# 获取 token 的函数
def get_Token():
    """获取 Google API 的 session token。"""
    global last_token, last_token_expiry
    current_time = time.time()
    if last_token and last_token_expiry > current_time:
        return last_token

    url = f"https://tile.googleapis.com/v1/createSession?key={GOOGLE_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"mapType": "streetview", "language": "en-US", "region": "US"}
    response = make_request(url, method='POST', headers=headers, data=data)

    if response:
        token = response.get('session', {})
        last_token_expiry = current_time + 86400  # 设置 token 的过期时间
        last_token = token
        return token
    return None


# 谷歌街景api获取地址信息
def get_address(id):
    """根据 panoId 获取街景地址信息。"""
    token = get_Token()
    if not token:
        return None

    url = f"https://tile.googleapis.com/v1/streetview/metadata?session={token}&key={GOOGLE_API_KEY}&panoId={id}"
    response = make_request(url)

    if response:
        data = response
        address = {"pool": []}
        for add in data['addressComponents']:
            if 'administrative_area_level_1' in add['types']:
                address['state'] = add['longName'].lower()
                address['pool'].append(add['longName'].lower())
                address['pool'].append(add['shortName'].lower())
            elif 'administrative_area_level_2' in add['types']:
                address['subdivision'] = add['longName'].lower()
                address['pool'].append(add['longName'].lower())
                address['pool'].append(add['shortName'].lower())
            elif 'locality' in add['types']:
                address['locality'] = add['longName'].lower()
                address['pool'].append(add['longName'].lower())
                address['pool'].append(add['shortName'].lower())
        return address
    return None


# 高德逆地理编码
def reverse_geocode(lon, lat):
    """根据经纬度反向获取地址。"""
    url = f'https://restapi.amap.com/v3/geocode/regeo?location={lon},{lat}&key={AMAP_API_KEY}'
    response = make_request(url)

    if response and 'regeocode' in response and 'addressComponent' in response['regeocode']:
        address_dict = {'pool': []}
        address = response['regeocode']['addressComponent']
        address_dict['state'] = address['province']
        address_dict['pool'].append(address['province'])
        if len(address['city']) > 1:
            address_dict['subdivision'] = address['city']
            address_dict['pool'].append(address['city'])
        if len(address['district']) > 1:
            address_dict['locality'] = address['district']
            address_dict['pool'].append(address['district'])
        return address_dict
    return None


# 获取 Google 街景全景数据
def get_google_pano(mode, coor_data, s=None, d=None, r=50):
    try:
        url = f"https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1.MapsJsInternalService/{mode}"
        payload = create_payload(mode, coor_data, s, d, r)
        headers = {
            "Content-Type": "application/json+protobuf",
            "X-User-Agent": "grpc-web-javascript/0.1"
        }
        response = requests.post(url, data=payload, headers=headers)

        if response.status_code != 200:
            print(f"HTTP error! Status: {response.status_code}, Response: {response.text}")
            return None

        try:
            return response.json()
        except json.JSONDecodeError:
            print("Error: Invalid JSON response from Google API")
            return None

    except Exception as error:
        print(f"Error in get_google_pano: {error}")
        return None


# 获取腾讯街景数据
async def get_qq_pano(seed):
    url = f'https://sv.map.qq.com/sv?svid={seed["panoId"]}&output=jsonp'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                content = await response.text()
                if not content.startswith("qqsvcallback&&qqsvcallback(") or not content.endswith(")"):
                    return None

                jsonp_data = content[len("qqsvcallback&&qqsvcallback("):-1]
                try:
                    data = json.loads(jsonp_data)
                except json.JSONDecodeError:
                    return None

                metadata = data.get("detail", {}).get("basic", {})
                if not metadata:
                    return None

                return {
                    "heading": float(metadata.get("dir", 0)),
                    "originHeading": float(metadata.get("dir", 0)),
                    "lat": seed["lat"],
                    "lng": seed["lng"],
                    "pitch": 0,
                    "panoId": seed["panoId"]
                }
        except Exception as error:
            print(f"Error fetching QQ metadata: {error}")
            return None


# 获取百度街景数据
async def get_bd_pano(pano_id):
    url = f'https://mapsv0.bdimg.com/?qt=sdata&sid={pano_id}'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                metadata = data.get("content", [{}])[0]
                if not metadata:
                    return None

                if "X" not in metadata or "Y" not in metadata:
                    return None

                gcj02 = bd09mc_to_gcj02(metadata["X"] / 100, metadata["Y"] / 100)
                heading = metadata.get("MoveDir", 180)
                origin_heading = heading - 90 if heading > 90 else 90

                return {
                    "heading": heading,
                    "originHeading": origin_heading,
                    "pitch": metadata.get("Pitch", 0),
                    "lat": gcj02[1],
                    "lng": gcj02[0],
                    "panoId": pano_id
                }
        except Exception as error:
            print(f"Error fetching BD metadata: {error}")
            return None


# 生成请求的 JSON Payload
def create_payload(mode, coor_data, s=None, d=None, r=50):
    if mode == 'GetMetadata':
        return json.dumps([
            ["apiv3", None, None, None, "US", None, None, None, None, None, [[0]]],
            ["en", "US"],
            [[[2, coor_data]]],
            [[1, 2, 3, 4, 8, 6]]
        ])

    elif mode == 'SingleImageSearch':
        if s and d:
            return json.dumps([
                ["apiv3"],
                [[None, None, coor_data["lat"], coor_data["lng"]], r],
                [[None, None, None, None, None, None, None, None, None, None, [s, d]],
                 None, None, None, None, None, None, None,
                 [2], None, [[[2, True, 2]]]],
                [[2, 6]]
            ])
        else:
            return json.dumps([
                ["apiv3", None, None, None, "US"],
                [[None, None, coor_data["lat"], coor_data["lng"]], r],
                [[None, None, False], ["en"], None, None, None, None, None, None, [2], None,
                 [[[2, True, 2], [3, True, 2], [10, True, 2]]]],
                [[1, 2, 3, 4, 8, 6], [], None, None, [], []]
            ])
    else:
        raise ValueError("Invalid mode!")