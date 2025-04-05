FIVE_K_DISTANCE = 50  # TODO: Hardcoded but change if you want to w/ bound calculations
ALLOWED_CHANNELS = []  # e.g. [12345678,999999]
MAPS = {
    "62a44b22040f04bd36e8a914": ["A Community World", "acw"],
    "5dbaf08ed0d2a478444d2e8e": ["AI Generated World", "agw"],
    "5b0a80f8596695b708122809": ["An Improved World", "aiw"],
    "5be0de51fe3a84037ca36447": ["A Rural World", "arw"],
    "643dbc7ccc47d3a344307998": ["An Arbitrary Rural World", "aarw"],
    "6165f7176c26ac00016bca3d": ["A Skewed World", "asw"],
    "652ba0d9002aa0d36f996153": ["An Official World", "aow"],
    "6089bfcff6a0770001f645dd": ["An Arbitrary World", "aaw"],
    "64ce812adc7614680516ff8c": ["A Varied World", "avw"],
    "672efde5c22a8c3d28dc5554": ["A Zi8gzag World", "azw"],
    "65c86935d327035509fd616f": ["A Rainbolt World", "arbw"],
    "64919f3c95165ff26469091a": ["Terminus", "tmn"],
    "65e97f26625ad27a6af383da": ["A Yandex World", "yandex"],
    "6145d90496b10b0001ac2bbb": ["Yandex Air", "air"],
    "66e684a8d86f90f1d3036208": ["Yandex Test", "test"],
    "62e309bfac02fca31aa404b8": ["A Balanced Russia", "abr", "ru"],
    "645fee824b5a2a4652553378": ["An Arbitrary Russia", "aar", "ru"],
    "61dfb63654e4730001e8faf5": ["An Arbitrary United States", "aaus", "us"],
    "672532f6414ef3effe689e07": ["A Community USA v2.0", "acusa", "us"],
    "6116c51c5e6d8d00011bcd7d": ["IntersectionGuessr-Japan", "igj", "jp"],
    "6430f6ae803b91d398056286": ["A Balanced AI Generated Chile", "agc", "cl"],
    "62e10035c97fc44e29bd8e0e": ["A Balanced AI Generated India", "agin", "in"],
    "61df8477a94f5d0001ef9f2c": ["A Balanced Brazil", "abb", "br"],
    "61067f9608061c000157a851": ["A Balanced Canada", "abc", "ca"],
    "60afb9b2dcdbe60001438fa6": ["A Balanced Australia", "aba", "au"],
    "63a3cef9571dcbb3660427c4": ["An Arbitrary Argentina", "aaa", "ar"],
    "63382d2cc00816fde6cd69b6": ["AI gen - Mexico", "agm", "mx"],
    "65fda213210c988a99251730": ["A Diverse Kazakhstan", "adk", "kz"],
    "63e7e2184c0ca2dca3723ca2": ["A Balanced Peru", "abp", "pe"],
    "64f4959080229b9a3d429041": ["A Balanced Philippines", "abph", "ph"],
    "617d2526ed0f750001c24b21": ["A Balanced Germany", "abg", "de"],
    "663d5ea93e1f20f3d481ae6a": ["An AI Generated South Africa", "aasa", "za"],
    "63d9cf8dc062831649aee066": ["An AI Generated Botswana", "agb", "bw"],
    "638777aabd4e538d5e52d4f9": ["AI gen - Thailand", "aith", "th"],
    "619086606e5572000185a1db": ["AI gen - Indonesia", "agid", "id"],
    "63c0a65c985b2d9d2425c6a1": ["A Balanced Colombia", "abcolo", "co"],
    "634050c7fc09dbb1e6c107c6": ["A Balanced Malaysia", "abm", "my"],
    "61fb2314990720000141ecc9": ["A Balanced Turkey", "abt", "tr"],
    "6383cdd0be0d9b60a5ab2e5d": ["AI Gen - France", "agf", "fr"],
    "62f439cfe46df79befe5c5f8": ["A Balanced Spain", "abs", "es"],
    "63f420f9f1482fc046350710": ["AI gen - Taiwan", "aitw", "cn", "tw"],
    "61f3f49330ad7100010d56c2": ["AI gen - New Zealand", "ainz", "nz"],
    "63715d43261c845960550585": ["AI Generated Nigeria", "aing", "ng"],
    "63e14435f677f1f620717797": ["AI Generated Sweden", "aise", "se"],
    "6387d6ccc465a7add9d9aaaf": ["AI Gen - Finland", "aifi", "fi"],
    "64f7824aae1d156d26e056a3": ["An Arbitrary Norway", "aan", "no"],
    "65d8c274811075137ed28c01": ["AI gen - Ukraine", 'aiua', 'ua'],
    "65d37bc2d172e33f7ba44793": ["A Yandex Belarus", "ayb", 'by'],
    "vn": ["A Balanced Vietnam", "abv", "vn"],
    "qq": ["腾讯街景", "tencent", "腾讯", "qq", "cn"],
    "baidu": ["湖山春社", "baidu", "百度街景", "百度", "cn"],
}

WORLD_MAPS = [
    "62a44b22040f04bd36e8a914",
    "5dbaf08ed0d2a478444d2e8e",
    "5b0a80f8596695b708122809",
    "5be0de51fe3a84037ca36447",
    "643dbc7ccc47d3a344307998",
    "6165f7176c26ac00016bca3d",
    "652ba0d9002aa0d36f996153",
    "6089bfcff6a0770001f645dd",
    "672efde5c22a8c3d28dc5554",
    "64ce812adc7614680516ff8c",
    "65c86935d327035509fd616f",
    "65e97f26625ad27a6af383da",
    "6145d90496b10b0001ac2bbb",
    "66e684a8d86f90f1d3036208"
]

REGIONS_NAMES = {
    "district":
        {"plural": "districts",
         "maps": [
             "63d9cf8dc062831649aee066",
         ]},
    "department": {
        "plural": "departments",
        "maps": [
            "63c0a65c985b2d9d2425c6a1",
        ]},
    "prefecture": {
        "plural": "prefectures",
        "maps": [
            "6116c51c5e6d8d00011bcd7d",
        ]},
    "province": {
        "plural": "provinces",
        "maps": [
            "61067f9608061c000157a851",
            "619086606e5572000185a1db",
            "663d5ea93e1f20f3d481ae6a",
            "63a3cef9571dcbb3660427c4",
            "64f4959080229b9a3d429041",
            "61fb2314990720000141ecc9",
            "638777aabd4e538d5e52d4f9",
            "vn",
            "qq",
            "baidu"
        ]},

    "county": {
        "plural": "counties",
        "maps": [
            "63f420f9f1482fc046350710",
            "64f7824aae1d156d26e056a3"
        ]},
    "region": {
        "plural": "regions",
        "maps": [
            "6383cdd0be0d9b60a5ab2e5d",
            "6430f6ae803b91d398056286",
            "65fda213210c988a99251730",
            "63e7e2184c0ca2dca3723ca2",
            "6387d6ccc465a7add9d9aaaf",
            "61f3f49330ad7100010d56c2",
            "63e14435f677f1f620717797"
        ]},
    "oblast": {
        "plural": "oblasts",
        "maps": [
            "65d37bc2d172e33f7ba44793",
            "62e309bfac02fca31aa404b8",
            "65d8c274811075137ed28c01",

        ]},
    "state": {
        "plural": "states",
        "maps": [
            "672532f6414ef3effe689e07",
            "62e309bfac02fca31aa404b8",
            "65d8c274811075137ed28c01",
            "634050c7fc09dbb1e6c107c6",
            "62e10035c97fc44e29bd8e0e",
            "617d2526ed0f750001c24b21",
            "63382d2cc00816fde6cd69b6",
            "60afb9b2dcdbe60001438fa6",
            "61dfb63654e4730001e8faf5",
            "61df8477a94f5d0001ef9f2c",
            "63715d43261c845960550585"
        ]},

    "country/countrycode": {
        "plural": "countries",
        "maps": [
            "65e97f26625ad27a6af383da",
            "6145d90496b10b0001ac2bbb",
            "62e309bfac02fca31aa404b8",
            "65d8c274811075137ed28c01",
            "64ce812adc7614680516ff8c",
            "65c86935d327035509fd616f",
            "62a44b22040f04bd36e8a914",
            "5dbaf08ed0d2a478444d2e8e",
            "5b0a80f8596695b708122809",
            "5be0de51fe3a84037ca36447",
            "643dbc7ccc47d3a344307998",
            "6165f7176c26ac00016bca3d",
            "652ba0d9002aa0d36f996153",
            "6089bfcff6a0770001f645dd",
            "672efde5c22a8c3d28dc5554",
        ]},
    "autonomous community": {
        "plural": "autonomous communities",
        "maps": [
            "62f439cfe46df79befe5c5f8",
        ]}
}

DEFAULT_MAP = {"map_id": "61dfb63654e4730001e8faf5", "map_code": "us"}  # AAR 645fee824b5a2a4652553378

MOD_ROLE_NAMES = ["Moderator"]
