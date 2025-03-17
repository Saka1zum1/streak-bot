import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"

GEOGUESSR_COOKIE = os.getenv("GEOGUESSR_COOKIE")

AMAP_API_KEY = os.getenv("AMAP_API_KEY")

STREAK_CHANNELS = [1279068439939645542]

MAPS_NAME = {"acw": "A Community World",
             "agw": "AI Generated World",
             "aiw": "An Improved World",
             "arw": "A Rural World",
             "aarw": "An Arbitrary Rural World",
             "abw": "A Balanced World",
             "aow": "An Official World",
             "aaw": "An Arbitrary World",
             "zi": "A Zi8gzag World",
             "jp": "IntersectionGuessr-Japan",
             "ru": "A Balanced Russia",
             "us": "An Arbitrary United States",
             "au": "A Balanced Australia",
             "br": "A Balanced Brazil",
             "ca": "A Balanced Canada",
             "ph": "A Balanced Philippines",
             "de": "A Balanced Germany",
             "tr": "A Balanced Turkey",
             "ar": "An Arbitrary Argentina",
             "id": "AI gen - Indonesia",
             "mx": "AI gen - Mexico",
             "in": "A Balanced AI Generated India",
             "za": "An AI Generated South Africa",
             "pe": "A Balanced Peru",
             "es": "A Balanced Spain",
             "cl": "A Balanced AI Generated Chile",
             "kz": "A Diverse Kazakhstan",
             "bw": "An AI Generated Botswana",
             "cn": "AI gen - Taiwan",
             "at": "A Balanced Austria",
             "mn": "A Curated Mongolia",
             "nz": "AI gen - New Zealand",
             "baidu": "湖山春社",
             "qq": "腾讯街景"
             }

STREAK_MAPS = {
            "acw": "62a44b22040f04bd36e8a914",
            "arw": "5be0de51fe3a84037ca36447",
            "aiw": "5b0a80f8596695b708122809",
            "aarw": "643dbc7ccc47d3a344307998",
            "agw": "5dbaf08ed0d2a478444d2e8e",
            "aaw": "6089bfcff6a0770001f645dd",
            "aow": "652ba0d9002aa0d36f996153",
            "abw": "5d73f83d82777cb5781464f2",
            "us": "61dfb63654e4730001e8faf5",
            "ru": "62e309bfac02fca31aa404b8",
            "au": "60afb9b2dcdbe60001438fa6",
            "jp": "6116c51c5e6d8d00011bcd7d",
            "br": "61df8477a94f5d0001ef9f2c",
            "ca": "61067f9608061c000157a851",
            "ph": "64f4959080229b9a3d429041",
            "de": "617d2526ed0f750001c24b21",
            "tr": "61fb2314990720000141ecc9",
            "ar": "63a3cef9571dcbb3660427c4",
            "id": "619086606e5572000185a1db",
            "mx": "63382d2cc00816fde6cd69b6",
            "in": "62e10035c97fc44e29bd8e0e",
            "za": "663d5ea93e1f20f3d481ae6a",
            "pe": "63e7e2184c0ca2dca3723ca2",
            "es": "62f439cfe46df79befe5c5f8",
            "cl": "6430f6ae803b91d398056286",
            "kz": "65fda213210c988a99251730",
            "bw": "63d9cf8dc062831649aee066",
            "cn": "63f420f9f1482fc046350710",
            "at": "639dd16256418a9903a7b61b",
            "mn": "61f153744f445700019e9bfb",
            "nz": "61f3f49330ad7100010d56c2",
            "zi": "672efde5c22a8c3d28dc5554",
            "baidu": "1",
            "qq": "2"
        }

REGION_TYPES = {
    "jp": "prefecture",  # 日本 - 都道府县
    "ro": "county",  # 罗马尼亚 - 县
    "in": "pradesh",
    "de": "state",
    "mx": "state",
    "au": "state",
    "ca": "province",
    "qq": "province",
    "baidu": "province",
    "us": "state",
    "br": "state",
    "za": "province",  # 南非 - 省
    "ar": "province",
    "ru": "oblast",  # 俄罗斯 - 州
}
