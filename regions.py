import logging

# Add your own countries/subdivisions if you wish to generalize
REGIONS = {
    "ru": {
        "Respublika Adygeya": {
            "aliases": ["Republic of Adygea", "Adygea", "Adygeya", "Adyghea", "Adygheia", "AD", "ADY"]
        },
        "Respublika Altay": {
            "aliases": ["Republic of Altai", "Altai Republic", "Gorniy Altai", "Gorny Altai", "AL", "Gorno"]
        },
        "Bashkortostan Republic": {
            "aliases": ["Republic of Bashkortostan", "Bashkiria", "Bashkortostan", "Bashkir", "BA", "bash", "bashkort",
                        "ufa"]
        },
        "Respublika Buryatiya": {
            "aliases": ["Republic of Buryatia", "Buryatia", "Buryat", "Buryatiya", "BU", "buryat", "Majin Buu", "Buu"]
        },
        "Chechenskaya Respublika": {
            "aliases": ["Chechen Republic", "Chechnya", "Chechenia", "Ichkeria", "Nokhchiyn Respublika", "CE", "chech",
                        "grozny"]
        },
        "Chuvashskaya Respublika": {
            "aliases": ["Chuvash Republic", "Chuvashia", "Chuvash", "CU", "cheboksary"]
        },
        "Dagestan Republic": {
            "aliases": ["Republic of Dagestan", "Dagestan", "Daghestan", "DA", "Dage", "Dag", "Makhachkala", "Dogestan"]
        },
        "Respublika Ingushetiya": {
            "aliases": ["Republic of Ingushetia", "Ingushetia", "Ingushetiya", "IN", "Ingush", "Ingushetia Republic"]
        },
        "Kabardino-Balkarskaya Respublika": {
            "aliases": ["Kabardino-Balkaria Republic", "Kabardino Balkaria", "Kabardino Balkar", "Kabardin Balkar",
                        "KB",
                        "kab", "Kabardino", "Balkaria", "balkar",
                        "kabardino-balkarian republic", "kabardino-balkaria", "kabardion",
                        "kabardino balkarian republic",
                        "nalchik"]
        },
        "Kalmykiya": {
            "aliases": ["Republic of Kalmykia", "Kalmykia", "Kalmyk", "Kalmykiya", "Khalmg Tangch", "KL", "elista"]
        },
        "Karachayevo-Cherkesiya": {
            "aliases": ["Karachay-Cherkess Republic", "Karachay Cherkessia", "Karachai Cherkess",
                        "Karachayevo Cherkessiya",
                        "KC", "karachay", "cherkess",
                        "cherkessiya", "cherkessia", "karachay-cherkessia", "Cherkessk"]
        },
        "Respublika Kareliya": {
            "aliases": ["Republic of Karelia", "Karelia", "Kareliya", "KR", "rok", "Karjala", "Finland", "Suomi"]
        },
        "Respublika Khakasiya": {
            "aliases": ["Republic of Khakassia", "Khakassia", "Khakassiya", "Khakasia", "KK", "khakassia republic",
                        "abakan"]
        },
        "Komi": {
            "aliases": ["Komi Republic", "Komi", "KO", "Komi-Permyak", "Komi-Permyak Autonomous Okrug",
                        "Komi-Permyak Autonomous District"]
        },
        "Respublika Mariy-El": {
            "aliases": ["Mari El Republic", "Mari El", "Mari", "Mariy El", "ME", "YoshkOla", "yoshkar", "mari",
                        "el mari"]
        },
        "Respublika Mordoviya": {
            "aliases": ["Republic of Mordovia", "Mordovia", "Mordoviya", "MO", "Saransk"]
        },
        "Respublika Sakha (Yakutiya)": {
            "aliases": ["Republic of Sakha", "Sakha", "Yakutia", "Yakutsk", "Yakutiya", "SA"]
        },
        "North Ossetia Republic": {
            "aliases": ["Republic of North Ossetia-Alania", "North Ossetia–Alania Republic",
                        "Respublika Severnaya Osetia-Alania", "North Ossetia–Alania",
                        "North Ossetia", "Alania", "Ossetia", "Ironston", "Iron", "Alaniya", "SE", "Vladikavkaz"]
        },
        "Tatarstan": {
            "aliases": ["Republic of Tatarstan", "Tatarstan", "Tatar", "Tataria", "TA", "Kazan"]
        },
        "Respublika Tyva": {
            "aliases": ["Republic of Tuva", "Tuva", "Tyva", "Tannu Tuva", "TY"]
        },
        "Udmurtskaya Respublika": {
            "aliases": ["Udmurt Republic", "Udmurtia", "Udmurt", "UD", "Izhevsk"]
        },

        # Krais
        "Altayskiy Kray": {
            "aliases": ["Altai Krai", "Altay Krai", "ALT", "Barnaul"]
        },
        "Kamchatka Krai": {
            "aliases": ["Kamchatka Krai", "Kamchatka", "Kamchatsky", "KAM", "Petropavlovsk-Kamchatsky", "Petropavlovsk"]
        },
        "Khabarovskiy Kray": {
            "aliases": ["Khabarovsk Krai", "Khabarovsk", "Khabarovsky", "KHA", "Khab"]
        },
        "Krasnodarskiy Kray": {
            "aliases": ["Krasnodar Krai", "Krasnodar", "Kuban", "KDA"]
        },
        "Krasnoyarskiy Kray": {
            "aliases": ["Krasnoyarsk Krai", "Krasnoyarsk", "Krasnoyarsky", "KYA"]
        },
        "Perm Krai": {
            "aliases": ["Perm Krai", "Perm", "Permsky", "PER"]
        },
        "Primorskiy Kray": {
            "aliases": ["Primorsky Krai", "Primorsky", "Primorye", "PRI", "Vladivostok", "Nakhodka", "PRIM",
                        "Primcess and the Frog"]
        },
        "Stavropol Kray": {
            "aliases": ["Stavropol Krai", "Stavropol", "Stavropolsky", "STA", "Pyatigorsk", "Stav", "Stavropolitan"]
        },
        "Transbaikal Territory": {
            "aliases": ["Zabaykalsky Krai", "Zabaykalsky", "Zabaikalsky", "Transbaikal", "ZAB", "Zabay", "Chita",
                        "Cheetah"]
        },

        # Oblasts
        "Amur Oblast": {
            "aliases": ["Amur Oblast", "Amur", "Amurskaya", "AMU", "Blagoveshchensk", "Blagoveshchenskaya", "Blago"]
        },
        "Arkhangelsk Oblast": {
            "aliases": ["Arkhangelsk Oblast", "Arkhangelsk", "Arkhangelskaya", "ARK"]
        },
        "Astrakhan Oblast": {
            "aliases": ["Astrakhan Oblast", "Astrakhan", "Astrakhanskaya", "AST"]
        },
        "Belgorod Oblast": {
            "aliases": ["Belgorod Oblast", "Belgorod", "Belgorodskaya", "BEL", "Belgo"]
        },
        "Bryansk Oblast": {
            "aliases": ["Bryansk Oblast", "Bryansk", "Bryanskaya", "BRY"]
        },
        "Chelyabinsk Oblast": {
            "aliases": ["Chelyabinsk Oblast", "Chelyabinsk", "Chelyabinskaya", "CHE", "Chelya"]
        },
        "Irkutsk Oblast": {
            "aliases": ["Irkutsk Oblast", "Irkutsk", "Irkutskaya", "IRK", "Bratsk"]
        },
        "Ivanovo Oblast": {
            "aliases": ["Ivanovo Oblast", "Ivanovo", "Ivanovskaya", "IVA"]
        },
        "Kaliningrad Oblast": {
            "aliases": ["Kaliningrad Oblast", "Kaliningrad", "Kaliningradskaya", "KGD", "Poland", "Lithuania",
                        "Teutonic Order", "Koenigsberg",
                        "Karaliaučius", "Królewiec", "Kunnegsgarbs", "Kyonigsberg", "Královec", "Königsberg"]
        },
        "Kaluga Oblast": {
            "aliases": ["Kaluga Oblast", "Kaluga", "Kaluzhskaya", "KLU"]
        },
        "Kemerovo Oblast": {
            "aliases": ["Kemerovo Oblast", "Kemerovo", "Kemerovskaya", "Kuzbass", "KEM"]
        },
        "Kirov Oblast": {
            "aliases": ["Kirov Oblast", "Kirov", "Kirovskaya", "KIR"]
        },
        "Kostroma Oblast": {
            "aliases": ["Kostroma Oblast", "Kostroma", "Kostromskaya", "KOS"]
        },
        "Kurgan Oblast": {
            "aliases": ["Kurgan Oblast", "Kurgan", "Kurganskaya", "KGN"]
        },
        "Kursk Oblast": {
            "aliases": ["Kursk Oblast", "Kursk", "Kurskaya", "KRS", "Ukraine"]
        },
        "Leningrad Oblast": {
            "aliases": ["Leningrad Oblast", "Leningrad", "Leningradskaya", "LEN", "Lenin"]
        },
        "Lipetsk Oblast": {
            "aliases": ["Lipetsk Oblast", "Lipetsk", "Lipetskaya", "LIP"]
        },
        "Magadan Oblast": {
            "aliases": ["Magadan Oblast", "Magadan", "Magadanskaya", "MAG", "maga"]
        },
        "Moscow Oblast": {
            "aliases": ["Moscow Oblast", "Moscow Oblast", "Moskovskaya", "Podmoskovye", "MOS"]
        },
        "Murmansk Oblast": {
            "aliases": ["Murmansk Oblast", "Murmansk", "Murmanskaya", "MUR"]
        },
        "Nizhny Novgorod Oblast": {
            "aliases": ["Nizhny Novgorod Oblast", "Nizhny Novgorod", "Nizhegorodskaya", "Nizhny", "NIZ"]
        },
        "Novgorod Oblast": {
            "aliases": ["Novgorod Oblast", "Novgorod", "Novgorodskaya", "NGR"]
        },
        "Novosibirsk Oblast": {
            "aliases": ["Novosibirsk Oblast", "Novosibirsk", "Novosibirskaya", "NVS", "Novo"]
        },
        "Omsk Oblast": {
            "aliases": ["Omsk Oblast", "Omsk", "Omskaya", "OMS"]
        },
        "Orenburg Oblast": {
            "aliases": ["Orenburg Oblast", "Orenburg", "Orenburgskaya", "ORE", "oren"]
        },
        "Orel Oblast": {
            "aliases": ["Oryol Oblast", "Oryol", "Orlovskaya", "Orel", "ORL", "Oreo"]
        },
        "Penza Oblast": {
            "aliases": ["Penza Oblast", "Penza", "Penzenskaya", "PNZ", "pen", "PEZ"]
        },
        "Pskov Oblast": {
            "aliases": ["Pskov Oblast", "Pskov", "Pskovskaya", "PSK"]
        },
        "Rostov Oblast": {
            "aliases": ["Rostov Oblast", "Rostov", "Rostovskaya", "ROS"]
        },
        "Ryazan Oblast": {
            "aliases": ["Ryazan Oblast", "Ryazan", "Ryazanskaya", "RYA"]
        },
        "Sakhalin Oblast": {
            "aliases": ["Sakhalin Oblast", "Sakhalin", "Sakhalinskaya", "SAK"]
        },
        "Samara Oblast": {
            "aliases": ["Samara Oblast", "Samara", "Samarskaya", "SAM", "Stavropol-on-Volga"]
        },
        "Saratovskaya Oblast": {
            "aliases": ["Saratov Oblast", "Saratov", "Saratovskaya", "SAR"]
        },
        "Smolensk Oblast": {
            "aliases": ["Smolensk Oblast", "Smolensk", "Smolenskaya", "SMO"]
        },
        "Sverdlovsk Oblast": {
            "aliases": ["Sverdlovsk Oblast", "Sverdlovsk", "Sverdlovskaya", "SVE", "Yekaterinburg", "Ekaterinburg",
                        "Yeka",
                        "yek", "Yekat"]
        },
        "Tambov Oblast": {
            "aliases": ["Tambov Oblast", "Tambov", "Tambovskaya", "TAM"]
        },
        "Tomsk Oblast": {
            "aliases": ["Tomsk Oblast", "Tomsk", "Tomskaya", "TOM"]
        },
        "Tula Oblast": {
            "aliases": ["Tula Oblast", "Tula", "Tulskaya", "TUL"]
        },
        "Tver Oblast": {
            "aliases": ["Tver Oblast", "Tver", "Tverskaya", "TVE"]
        },
        "Tyumenskaya Oblast’": {
            "aliases": ["Tyumen Oblast", "Tyumen", "Tyumenskaya", "TYU"]
        },
        "Ulyanovsk Oblast": {
            "aliases": ["Ulyanovsk Oblast", "Ulyanovsk", "Ulyanovskaya", "ULY", "Ulya"]
        },
        "Vladimirskaya Oblast’": {
            "aliases": ["Vladimir Oblast", "Vladimir", "Vladimirskaya", "VLA"]
        },
        "Volgograd Oblast": {
            "aliases": ["Volgograd Oblast", "Volgograd", "Volgogradskaya", "VGG", "Stalingrad", "Volgo"]
        },
        "Vologda Oblast": {
            "aliases": ["Vologda Oblast", "Vologda", "Vologodskaya", "VLG"]
        },
        "Voronezh Oblast": {
            "aliases": ["Voronezh Oblast", "Voronezh", "Voronezhskaya", "VOR"]
        },
        "Yaroslavl Oblast": {
            "aliases": ["Yaroslavl Oblast", "Yaroslavl", "Yaroslavskaya", "YAR", "Yaro"]
        },

        # Autonomous Okrugs
        "Chukotka Autonomous Okrug": {
            "aliases": ["Chukotka Autonomous Okrug", "Chukotka", "Chukotsky", "CHU"]
        },
        "Khanty-Mansiyskiy Avtonomnyy Okrug-Yugra": {
            "aliases": ["Khanty-Mansi Autonomous Okrug", "Khanty Mansi", "Jugra", "Yugra", "Khantia Mansia", "KHM",
                        "Khanty", "Khanty-Mansi", "Khanty-Mansiysk",
                        "Khanty-Mansiyskiy", "Khanty-Mansiyskiy Avtonomnyy Okrug",
                        "Khanty-Mansiyskiy Avtonomnyy Okrug-Yugra", "Khanty Mansi Autonomous Okrug", "Mansi",
                        "Surgut"]
        },
        "Nenetskiy Avtonomnyy Okrug": {
            "aliases": ["Nenets Autonomous Okrug", "Nenets", "Nenetsky", "NEN"]
        },
        "Yamalo-Nenetskiy Avtonomnyy Okrug": {
            "aliases": ["Yamalo-Nenets Autonomous Okrug", "Yamalo Nenets", "Yamal", "YAN", "Yamalo", "Ian Nepomniatchi",
                        "Yanmega"]
        },

        # Federal Cities
        "Moscow Federal City": {
            "aliases": ["Moscow", "Moskva", "MOW"]
        },
        "Saint Petersburg Federal City": {
            "aliases": ["Saint Petersburg", "Saint Petersburg", "St Petersburg", "SPb", "Petersburg", "SPE"]
        },
        "Sevastopol Federal City": {
            "aliases": ["Sevastopol", "Sevastopol", "SEV"]
        },

        # Autonomous Oblast
        "Yevrey (Jewish) Autonomous Oblast": {
            "aliases": ["Jewish Autonomous Oblast", "Jewish", "Yevrey", "Birobidzhan", "YEV", "JAO", "Israel"]
        }
    },
    "cn": {
        "北京市": {"aliases": ["北京", "京", "BJ", "Beijing"]},
        "天津市": {"aliases": ["天津", "津", "TJ", "Tianjin"]},
        "河北省": {"aliases": ["河北", "冀", "Hebei", "HE"]},
        "山西省": {"aliases": ["山西", "晋", "SX", "Shanxi"]},
        "内蒙古自治区": {"aliases": ["内蒙古", "蒙", "NM", "Inner Mongolia", "Neimenggu", "nmg"]},
        "辽宁省": {"aliases": ["辽宁", "辽", "LN", "Liaoning"]},
        "吉林省": {"aliases": ["吉林", "吉", "JL", "Jilin"]},
        "黑龙江省": {"aliases": ["黑龙江", "黑", "HL", "Heilongjiang"]},
        "上海市": {"aliases": ["上海", "沪", "SH", "Shanghai"]},
        "江苏省": {"aliases": ["江苏", "苏", "JS", "Jiangsu"]},
        "浙江省": {"aliases": ["浙江", "浙", "ZJ", "Zhejiang"]},
        "安徽省": {"aliases": ["安徽", "皖", "AH", "Anhui"]},
        "福建省": {"aliases": ["福建", "闽", "FJ", "Fujian"]},
        "江西省": {"aliases": ["江西", "赣", "JX", "Jiangxi"]},
        "山东省": {"aliases": ["山东", "鲁", "SD", "Shandong"]},
        "河南省": {"aliases": ["河南", "豫", "HA", "Henan"]},
        "湖北省": {"aliases": ["湖北", "鄂", "HB", "Hubei"]},
        "湖南省": {"aliases": ["湖南", "湘", "HN", "Hunan"]},
        "广东省": {"aliases": ["广东", "粤", "GD", "Guangdong"]},
        "广西壮族自治区": {"aliases": ["广西", "桂", "GX", "Guangxi"]},
        "海南省": {"aliases": ["海南", "琼", "HI", "Hainan"]},
        "重庆市": {"aliases": ["重庆", "渝", "CQ", "重慶市", "Chongqing"]},
        "四川省": {"aliases": ["四川", "川", "蜀", "SC", "Sichuan"]},
        "贵州省": {"aliases": ["贵州", "黔", "GZ", "Guizhou"]},
        "云南省": {"aliases": ["云南", "云", "滇", "YN", "Yunnan"]},
        "西藏自治区": {"aliases": ["西藏", "藏", "Tibet", "Xizang", "XZ"]},
        "陕西省": {"aliases": ["陕西", "陕", "SN", "秦", "Shaanxi"]},
        "甘肃省": {"aliases": ["甘肃", "甘", "GS", "陇", "Gansu"]},
        "青海省": {"aliases": ["青海", "青", "QH", "Qinghai"]},
        "宁夏回族自治区": {"aliases": ["宁夏", "宁", "NX", "Ningxia"]},
        "台湾省": {"aliases": ["台湾", "TW", "台", "Taiwan", "Formosa"]},
        "香港特别行政区": {"aliases": ["香港", "HK", "Hongkong", "Hong Kong", "Xianggang", "港"]},
        "澳门特别行政区": {"aliases": ["澳门", "MO", "Macau", "Aomen", "澳"]},
        "新疆维吾尔族自治区": {"aliases": ["新疆", "XJ", "新", "Xinjiang"]},
        '彰化县': {'aliases': ['Changhua County', '彰化', 'zhanghua', 'ch', 'CHA']},
        '嘉义市': {'aliases': ['Chiayi City', 'CYI', "嘉义市"]},
        '嘉义县': {'aliases': ['Chiayi County', "嘉义县", 'cyc', 'cy', 'CYQ']},
        '新竹市': {'aliases': ['Hsinchu City', 'hci', 'HSZ']},
        '新竹县': {'aliases': ['Hsinchu County', 'hcc', 'xinzhu', 'hc', 'HSQ']},
        '花莲县': {'aliases': ['Hualien County', '花莲', 'hualian', 'hl', 'HUA']},
        '高雄市': {'aliases': ['Kaohsiung City', '高雄', 'gaoxiong', 'kao', 'ks', 'KHH']},
        '基隆市': {'aliases': ['Keelung City', '基隆', '基', 'jilong', 'kl', 'KEE']},
        '金门县': {'aliases': ['Kinmen County', '金门', '金', 'jinmen', 'km', 'KIN']},
        '连江县': {'aliases': ['Lienchiang County', '连江', '连', 'lianjiang', '马祖', 'lc', 'LIE']},
        '苗栗县': {'aliases': ['Miaoli County', '苗栗', '苗', 'miaoli', 'ml', 'MIA']},
        '南投县': {'aliases': ['Nantou County', '南投', 'nantou', 'nt', 'NAN']},
        '新北市': {'aliases': ['New Taipei City', '新北', 'ntp', 'np', 'xinbei', 'NWT']},
        '澎湖县': {'aliases': ['Penghu County', '澎湖', '澎', 'penghu', 'ph', 'PEN']},
        '屏东县': {'aliases': ['Pingtung County', '屏东', '屏', 'pingdong', 'pin', 'pt', 'PIF']},
        '台中市': {'aliases': ['Taichung City', '台中', 'taizhong', 'tc', 'TXG']},
        '台南市': {'aliases': ['Tainan City', '台南', 'tainan', 'tn', 'TNN']},
        '台北市': {'aliases': ['Taipei City', 'taipei', 'taibei', 'tp', 'TPE']},
        '台东县': {'aliases': ['Taitung County', '台东', 'taidong', 'tt', 'TTT']},
        '桃园市': {'aliases': ['Taoyuan City', '桃园', 'taoyuan', 'ty', 'TAO']},
        '宜兰县': {'aliases': ['Yilan County', '宜兰', '宜', 'yilan', 'yil', 'yi', 'ILA']},
        '云林县': {'aliases': ['Yunlin County', '云林', '云', 'yunlin', 'yu', 'YUN']}
    },
    "vn": {
        "An Giang": {
            "aliases": ["An Giang", "AG", "44"]
        },
        "Ba Ria - Vung Tau": {
            "aliases": ["Ba Ria - Vung Tau", "BRVT", "43"]
        },
        "Bac Giang": {
            "aliases": ["Bac Giang", "BG", "54"]
        },
        "Bac Kan": {
            "aliases": ["Bac Kan", "BK", "53"]
        },
        "Bac Lieu": {
            "aliases": ["Bac Lieu", "BL", "55"]
        },
        "Bac Ninh": {
            "aliases": ["Bac Ninh", "BN", "56"]
        },
        "Ben Tre": {
            "aliases": ["Ben Tre", "BT", "50"]
        },
        "Binh Dinh": {
            "aliases": ["Binh Dinh", "BD", "31"]
        },
        "Binh Duong": {
            "aliases": ["Binh Duong", "BDU", "57"]
        },
        "Binh Phuoc": {
            "aliases": ["Binh Phuoc", "BP", "58"]
        },
        "Binh Thuan": {
            "aliases": ["Binh Thuan", "BTH", "40"]
        },
        "Ca Mau": {
            "aliases": ["Ca Mau", "CM", "59"]
        },
        "Can Tho": {
            "aliases": ["Can Tho", "CT", "CT"]
        },
        "Cao Bang": {
            "aliases": ["Cao Bang", "CB", "04"]
        },
        "Da Nang": {
            "aliases": ["Da Nang", "DN", "DN"]
        },
        "Dak Lak": {
            "aliases": ["Dak Lak", "DL", "33"]
        },
        "Dak Nong": {
            "aliases": ["Dak Nong", "DN", "72"]
        },
        "Dien Bien": {
            "aliases": ["Dien Bien", "DB", "71"]
        },
        "Dong Nai": {
            "aliases": ["Dong Nai", "DNA", "39"]
        },
        "Dong Thap": {
            "aliases": ["Dong Thap", "DT", "45"]
        },
        "Gia Lai": {
            "aliases": ["Gia Lai", "GL", "30"]
        },
        "Ha Giang": {
            "aliases": ["Ha Giang", "HG", "03"]
        },
        "Ha Nam": {
            "aliases": ["Ha Nam", "HNA", "63"]
        },
        "Ha Noi": {
            "aliases": ["Ha Noi", "HN"]
        },
        "Ha Tinh": {
            "aliases": ["Ha Tinh", "HT", "23"]
        },
        "Hai Duong": {
            "aliases": ["Hai Duong", "HD", "61"]
        },
        "Hai Phong": {
            "aliases": ["Hai Phong", "HP", "HP"]
        },
        "Hau Giang": {
            "aliases": ["Hau Giang", "HG", "73"]
        },
        "Ho Chi Minh City": {
            "aliases": ["Ho Chi Minh City", "Ho Chi Minh", "HCM", "SG"]
        },
        "Hoa Binh": {
            "aliases": ["Hoa Binh", "HB", "14"]
        },
        "Hung Yen": {
            "aliases": ["Hung Yen", "HY", "66"]
        },
        "Khanh Hoa": {
            "aliases": ["Khanh Hoa", "KH", "34"]
        },
        "Kien Giang": {
            "aliases": ["Kien Giang", "KG", "47"]
        },
        "Kon Tum": {
            "aliases": ["Kon Tum", "KT", "28"]
        },
        "Lai Chau": {
            "aliases": ["Lai Chau", "LC", "01"]
        },
        "Lam Dong": {
            "aliases": ["Lam Dong", "LD", "35"]
        },
        "Lang Son": {
            "aliases": ["Lang Son", "LS", "09"]
        },
        "Lao Cai": {
            "aliases": ["Lao Cai", "LCA", "02"]
        },
        "Long An": {
            "aliases": ["Long An", "LA", "41"]
        },
        "Nam Dinh": {
            "aliases": ["Nam Dinh", "ND", "67"]
        },
        "Nghe An": {
            "aliases": ["Nghe An", "NA", "22"]
        },
        "Ninh Binh": {
            "aliases": ["Ninh Binh", "NB", "18"]
        },
        "Ninh Thuan": {
            "aliases": ["Ninh Thuan", "NT", "36"]
        },
        "Phu Tho": {
            "aliases": ["Phu Tho", "PT", "68"]
        },
        "Phu Yen": {
            "aliases": ["Phu Yen", "PY", "32"]
        },
        "Quang Binh": {
            "aliases": ["Quang Binh", "QB", "24"]
        },
        "Quang Nam": {
            "aliases": ["Quang Nam", "QN", "27"]
        },
        "Quang Ngai": {
            "aliases": ["Quang Ngai", "QNG", "29"]
        },
        "Quang Ninh": {
            "aliases": ["Quang Ninh", "QNH", "13"]
        },
        "Quang Tri": {
            "aliases": ["Quang Tri", "QT", "25"]
        },
        "Soc Trang": {
            "aliases": ["Soc Trang", "ST", "52"]
        },
        "Son La": {
            "aliases": ["Son La", "SL", "05"]
        },
        "Tay Ninh": {
            "aliases": ["Tay Ninh", "TN", "37"]
        },
        "Thai Binh": {
            "aliases": ["Thai Binh", "TB", "20"]
        },
        "Thai Nguyen": {
            "aliases": ["Thai Nguyen", "TNG", "69"]
        },
        "Thanh Hoa": {
            "aliases": ["Thanh Hoa", "TH", "21"]
        },
        "Thua Thien Hue": {
            "aliases": ["Thua Thien Hue", "TTH", "26"]
        },
        "Tien Giang": {
            "aliases": ["Tien Giang", "TG", "46"]
        },
        "Tra Vinh": {
            "aliases": ["Tra Vinh", "TV", "51"]
        },
        "Tuyen Quang": {
            "aliases": ["Tuyen Quang", "TQ", "07"]
        },
        "Vinh Long": {
            "aliases": ["Vinh Long", "VL", "49"]
        },
        "Vinh Phuc": {
            "aliases": ["Vinh Phuc", "VP", "70"]
        },
        "Yen Bai": {
            "aliases": ["Yen Bai", "YB", "06"]
        }
    },
    "by": {
        "Brest": {
            "aliases": ["Brest", "BR"]
        },
        "Gomel": {
            "aliases": ["Gomel", "GO", "HO"]
        },
        "Grodno": {
            "aliases": ["Grodno", "GR", "HR"]
        },
        "Minsk City": {
            "aliases": ["Minsk City", "MC", "HM"]
        },
        "Minsk Region": {
            "aliases": ["Minsk Region", "MR", "MI"]
        },
        "Mogilev": {
            "aliases": ["Mogilev", "MO", "MA"]
        },
        "Vitebsk": {
            "aliases": ["Vitebsk", "VI"]
        }
    },
    "world": {
        "China": {"aliases": ["China", "CN", "中国", "MO", "HK", "TW"]},
        "Russia": {"aliases": ["Russia", "RU", "俄罗斯"]},
        "United States": {"aliases": ["United States", "US", "VI", "AS", "GU", "MP", "美国"]},
        "Brazil": {"aliases": ["Brazil", "BR", "巴西"]},
        "Japan": {"aliases": ["Japan", "JP", "日本"]},
        "Germany": {"aliases": ["Germany", "DE", "德国"]},
        "United Kingdom": {"aliases": ["United Kingdom", "GB", "UK", "JE", "英国"]},
        "France": {"aliases": ["France", "FR", "法国"]},
        "Monaco": {"aliases": ["Monaco", "MC", "摩纳哥"]},
        "São Tomé and Príncipe": {"aliases": ["Sao Tome and Principe", "ST", "圣多美和普林西比", ]},
        "Mexico": {"aliases": ["Mexico", "MX", "墨西哥"]},
        "Canada": {"aliases": ["Canada", "CA", "加拿大"]},
        "Australia": {"aliases": ["Australia", "AU", "澳大利亚"]},
        "Italy": {"aliases": ["Italy", "IT", "意大利"]},
        "Spain": {"aliases": ["Spain", "ES", "西班牙"]},
        "South Korea": {"aliases": ["South Korea", "KR", "韩国"]},
        "India": {"aliases": ["India", "IN", "印度"]},
        "Indonesia": {"aliases": ["Indonesia", "ID", "印度尼西亚"]},
        "Argentina": {"aliases": ["Argentina", "AR", "阿根廷"]},
        "South Africa": {"aliases": ["South Africa", "ZA", "南非"]},
        "Saudi Arabia": {"aliases": ["Saudi Arabia", "SA", "沙特阿拉伯"]},
        "Turkey": {"aliases": ["Turkey", "TR", "土耳其"]},
        "Colombia": {"aliases": ["Colombia", "CO", "哥伦比亚"]},
        "Egypt": {"aliases": ["Egypt", "EG", "埃及"]},
        "Thailand": {"aliases": ["Thailand", "TH", "泰国"]},
        "Malaysia": {"aliases": ["Malaysia", "MY", "马来西亚"]},
        "Philippines": {"aliases": ["Philippines", "PH", "菲律宾"]},
        "Chile": {"aliases": ["Chile", "CL", "智利"]},
        "Peru": {"aliases": ["Peru", "PE", "秘鲁"]},
        "Poland": {"aliases": ["Poland", "PL", "波兰"]},
        "Ukraine": {"aliases": ["Ukraine", "UA", "乌克兰"]},
        "Sweden": {"aliases": ["Sweden", "SE", "瑞典"]},
        "Belgium": {"aliases": ["Belgium", "BE", "比利时"]},
        "Norway": {"aliases": ["Norway", "NO", "挪威"]},
        "Denmark": {"aliases": ["Denmark", "DK", "丹麦"]},
        "Finland": {"aliases": ["Finland", "FI", "芬兰"]},
        "Switzerland": {"aliases": ["Switzerland", "CH", "瑞士"]},
        "Austria": {"aliases": ["Austria", "AT", "奥地利"]},
        "Netherlands": {"aliases": ["Netherlands", "NL", "荷兰"]},
        "Czech Republic": {"aliases": ["Czech Republic", "CZ", "捷克"]},
        "Slovakia": {"aliases": ["Slovakia", "SK", "斯洛伐克"]},
        "Romania": {"aliases": ["Romania", "RO", "罗马尼亚"]},
        "Portugal": {"aliases": ["Portugal", "PT", "葡萄牙"]},
        "Greece": {"aliases": ["Greece", "GR", "希腊"]},
        "Israel": {"aliases": ["Israel", "IL", "以色列"]},
        "New Zealand": {"aliases": ["New Zealand", "NZ", "新西兰"]},
        "Qatar": {"aliases": ["Qatar", "QA", "卡塔尔"]},
        "Kazakhstan": {"aliases": ["Kazakhstan", "KZ", "哈萨克斯坦"]},
        "Kyrgyzstan": {"aliases": ["Kyrgyzstan", "KG", "吉尔吉斯斯坦"]},
        "Uzbekistan": {"aliases": ["Uzbekistan", "UZ", "乌兹别克斯坦"]},
        "Uganda": {"aliases": ["Uganda", "UG", "乌干达"]},
        "Kenya": {"aliases": ["Kenya", "KE", "肯尼亚"]},
        "Senegal": {"aliases": ["Senegal", "SN", "塞内加尔"]},
        "Ghana": {"aliases": ["Ghana", "GH", "加纳"]},
        "Nigeria": {"aliases": ["Nigeria", "NG", "尼日利亚"]},
        "Oman": {"aliases": ["Oman", "OM", "阿曼"]},
        "Tunisia": {"aliases": ["Tunisia", "TN", "突尼斯"]},
        "Liechtenstein": {"aliases": ["Liechtenstein", "LI", "列支敦士登"]},
        "San Marino": {"aliases": ["San Marino", "SM", "圣马力诺"]},
        "Malta": {"aliases": ["Malta", "MT", "马耳他"]},
        "Iceland": {"aliases": ["Iceland", "IS", "冰岛"]},
        "Faroe Islands": {"aliases": ["Faroe Islands", "FO", "法罗群岛"]},
        "Ecuador": {"aliases": ["Ecuador", "EC", "厄瓜多尔"]},
        "Bangladesh": {"aliases": ["Bangladesh", "BD", "孟加拉国"]},
        "Bhutan": {"aliases": ["Bhutan", "BT", "不丹"]},
        "Nepal": {"aliases": ["Nepal", "NP", "尼泊尔"]},
        "Panama": {"aliases": ["Panama", "PA", "巴拿马"]},
        "Guatemala": {"aliases": ["Guatemala", "GT", "危地马拉"]},
        "Dominican Republic": {"aliases": ["Dominican Republic", "DR", "多尼米加"]},
        "Rwanda": {"aliases": ["Rwanda", "RW", "卢旺达"]},
        "Tanzania": {"aliases": ["Tanzania", "TZ", "坦桑尼亚"]},
        "Réunion": {"aliases": ["Réunion", "Reunion", "RE", "留尼旺"]},
        "Madagascar": {"aliases": ["Madagascar", "MG", "马达加斯加"]},
        "Mali": {"aliases": ["Mali", "ML", "马里"]},
        "Latvia": {"aliases": ["Latvia", "LV", "拉脱维亚"]},
        "Lithuania": {"aliases": ["Lithuania", "LT", "立陶宛"]},
        "Estonia": {"aliases": ["Estonia", "EE", "爱沙尼亚"]},
        "Belarus": {"aliases": ["Belarus", "BY", "白俄罗斯"]},
        "North Macedonia": {"aliases": ["North Macedonia", "MK", "北马其顿"]},
        "Serbia": {"aliases": ["Serbia", "RS", "塞尔维亚"]},
        "Bulgaria": {"aliases": ["Bulgaria", "BG", "保加利亚"]},
        "Lebanon": {"aliases": ["Lebanon", "LB", "黎巴嫩"]},
        "Palestine": {"aliases": ["Palestine", "PS", "巴勒斯坦"]},
        "Jordan": {"aliases": ["Jordan", "JO", "约旦"]},
        "Gibraltar": {"aliases": ["Gibraltar", "GI", "直布罗陀"]},
        "Mongolia": {"aliases": ["Mongolia", "MN", "蒙古"]},
        "Costa Rica": {"aliases": ["Costa Rica", "CR", "哥斯达黎加"]},
        "Curaçao": {"aliases": ["Curaçao", "CW", "库拉索"]},
        "Bermuda": {"aliases": ["Bermuda", "BM", "百慕大"]},
        "Greenland": {"aliases": ["Greenland", "GL", "格陵兰岛"]},
        "Bolivia": {"aliases": ["Bolivia", "BO", "玻利维亚"]},
        "Andorra": {"aliases": ["Andorra", "AD", "安道尔"]},
        "Slovenia": {"aliases": ["Slovenia", "SI", "斯洛文尼亚"]},
        "Croatia": {"aliases": ["Croatia", "HR", "克罗地亚"]},
        "Hungary": {"aliases": ["Hungary", "HU", "匈牙利"]},
        "Albania": {"aliases": ["Albania", "AL", "阿尔巴尼亚"]},
        "Montenegro": {"aliases": ["Montenegro", "ME", "黑山"]},
        "Ireland": {"aliases": ["Ireland", "IE", "爱尔兰"]},
        "Botswana": {"aliases": ["Botswana", "BW", "博茨瓦纳"]},
        "Eswatini": {"aliases": ["Eswatini", "SZ", "斯威士兰"]},
        "Lesotho": {"aliases": ["Lesotho", "LS", "莱索托"]},
        "Sri Lanka": {"aliases": ["Sri Lanka", "LK", "斯里兰卡"]},
        "Cambodia": {"aliases": ["Cambodia", "KH", "柬埔寨"]},
        "Laos": {"aliases": ["Laos", "LA", "老挝"]},
        "Puerto Rico": {"aliases": ["Puerto Rico", "PR", "波多黎各"]},
        "Luxembourg": {"aliases": ["Luxembourg", "LU", "卢森堡"]},
        "Isle of Man": {"aliases": ["Isle of Man", "IM", "马恩岛"]},
        "Pakistan": {"aliases": ["Pakistan", "PK", "巴基斯坦"]},
        "Uruguay": {"aliases": ["Uruguay", "UY", "乌拉圭"]},
        "Singapore": {"aliases": ["Singapore", "SG", "新加坡"]},
        "Georgia": {"aliases": ["Georgia", "GE", "格鲁吉亚"]},
        "Armenia": {"aliases": ["Armenia", "AM", "亚美尼亚"]},
        "Paraguay": {"aliases": ["Paraguay", "PY", "巴拉圭"]},
        "El Salvador": {"aliases": ["El Salvador", "SV", "萨尔瓦多"]},
        "Vietnam": {"aliases": ["Vietnam", "VN", "越南"]},
        "Bosnia and Herzegovina": {"aliases": ["Bosnia and Herzegovina", "BA", "波黑"]},
        "Morocco": {"aliases": ["Morocco", "MA", "摩洛哥"]},
        "Namibia": {"aliases": ["Namibia", "NA", "纳米比亚"]}
    }
}


class RegionFlatmap:
    """Flat map where each alias points to alias list with standardized name first"""

    def __init__(self, subdivisions_data):
        self.flat_map = {}

        for canonical_name, data in subdivisions_data.items():
            # Get standardized name (first alias) and rest of aliases
            standardized_name = data['aliases'][0]  # First alias is standardized name
            other_aliases = data['aliases'][1:] + [canonical_name]  # Rest of aliases + canonical

            # Create ordered alias list with standardized name first
            all_aliases = [standardized_name] + other_aliases

            # Map each alias to the full list
            for alias in all_aliases:
                self.flat_map[alias.lower()] = all_aliases

    def verify_guess(self, guess: str, actual: str, pool: list) -> bool:
        """
        Verify if a guess matches any alias of the actual location
        Returns True if guess and actual share any aliases
        """
        if not guess:
            logging.error("Invalid guess")
        if not actual:
            logging.error("Invalid actual")

        guess = guess.lower().strip()
        actual = actual.lower().strip()

        for answer in pool:
            if answer and guess:
                if guess.lower() == answer.lower():
                    return True

        if guess not in self.flat_map or actual not in self.flat_map:
            return False

        return self.flat_map[guess] == self.flat_map[actual]

    def get_canonical_name(self, location: str) -> str:
        """Get the first alias (canonical) for any valid alias"""
        location = location.lower().strip()
        if location in self.flat_map:
            return self.flat_map[location][0]
        return None

    def is_valid_location(self, location: str) -> bool:
        """Check if a string is a valid location alias"""
        return location.lower().strip() in self.flat_map

    def get_all_aliases(self, location: str) -> list:
        """Get all aliases for a location"""
        location = location.lower().strip()
        if location in self.flat_map:
            return self.flat_map[location]
        return []

    def get_all_subdivisions(self):
        """Get all subdivisions (standardized names)"""
        # Return a list of all standardized names (the first alias of each subdivision)
        subdivisions = set()  # Use a set to avoid duplicates
        for aliases in self.flat_map.values():
            subdivisions.add(aliases[0])  # The first alias is the standardized name
        return list(subdivisions)
