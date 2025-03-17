import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # 地球平均半径（单位：米）
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = (R * c)
    return distance


def get_tile_url(lat, lng, isbaidu):
    def lon2tile(lng, zoom):
        return int((lng + 180) / 360 * (2 ** zoom))

    def lat2tile(lat, zoom):
        return int((1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * (2 ** zoom))

    zoom = 10
    if not isbaidu:
        zoom = 11
    tileX = lon2tile(lng, zoom)
    tileY = lat2tile(lat, zoom)
    if not isbaidu:
        return f"https://www.google.com/maps/vt?pb=!1m5!1m4!1i{zoom}!2i{tileX}!3i{tileY}!4i256!2m1!2sm!3m17!2sen!3sUS!5e18!12m4!1e68!2m2!1sset!2sRoadmap!12m3!1e37!2m1!1ssmartmaps!12m4!1e26!2m2!1sstyles!2ss.e:l|p.v:on,s.t:0.8|s.e:g.s|p.v:on!5m1!5f1.5"
    else:
        return f"https://www.google.com/maps/vt?pb=!1m5!1m4!1i{zoom}!2i{tileX}!3i{tileY}!4i256!2m1!2sm!3m17!2sen!3sUS!5e18!12m4!1e68!2m2!1sset!2sRoadmap!12m3!1e37!2m1!1ssmartmaps!12m4!1e26!2m2!1sstyles!2ss.e:l|p.v:on,s.t:0.8|s.e:g.s|p.v:on!5m1!5f1.5"