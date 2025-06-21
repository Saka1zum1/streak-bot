FIVE_K_DISTANCE = 50  # TODO: Hardcoded but change if you want to w/ bound calculations
ALLOWED_CHANNELS = []  # e.g. {12345678} 

MAPS = {
    "685027072b48b15b2a91acf6": ["A Completed World", "comp"],
    "62a44b22040f04bd36e8a914": ["A Community World", "acw"],
    "67efece34e7a7e5c1be7405c": ["A Yandex World", "yandex"],
    "6852c5772c73c85eba48d6a9": ["Look Around The World", "apple"],
    "684abfa1df5bea77c509e7a0": ["A Bing Streetside World", "bing"],
    "67f3c86c6515ac1c009dfc91": ["A Kakao South Korea", "kakao", 'kr'],
    "67fa91aca33ebef9070aea94": ["An Openmap Vietnam", "abv", "vn"],
    "68501449cc3fe5fbf8cd0bf9": ["A Tecent China", "qq", "cn"],
    "68501c67d55629ddf0b7efff": ["A Baidu China", "baidu", "cn"],
    "61dfb63654e4730001e8faf5": ["An Arbitrary United States", "aaus", "us"]
}

WORLD_MAPS = [
    "685027072b48b15b2a91acf6",
    "62a44b22040f04bd36e8a914",
    "67efece34e7a7e5c1be7405c",
    "6852c5772c73c85eba48d6a9",
    "684abfa1df5bea77c509e7a0"
]

REGIONS_NAMES = {

    "province": {
        "plural": "provinces",
        "maps": [
            "67f3c86c6515ac1c009dfc91",
            "67fa91aca33ebef9070aea94",
            "68501449cc3fe5fbf8cd0bf9",
            "68501c67d55629ddf0b7efff"
        ]},

    "oblast": {
        "plural": "oblasts",
        "maps": [

        ]},
    "state": {
        "plural": "states",
        "maps": [
            "61dfb63654e4730001e8faf5",
        ]},

    "country/countrycode": {
        "plural": "countries",
        "maps": [
            "685027072b48b15b2a91acf6",
            "67efece34e7a7e5c1be7405c",
            "62a44b22040f04bd36e8a914",
            "6852c5772c73c85eba48d6a9",
            "684abfa1df5bea77c509e7a0"
        ]}
}

DEFAULT_MAP = {"map_id": "61dfb63654e4730001e8faf5", "map_code": "us"}

MOD_ROLE_NAMES = ["Mod", "Moderator"]
