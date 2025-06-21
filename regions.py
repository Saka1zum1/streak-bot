import logging

# Add your own countries/subdivisions if you wish to generalize
REGIONS = {
    "cn": {
        "北京市": {"aliases": ["Beijing", "北京", "京", "BJ"]},
        "天津市": {"aliases": ["Tianjin", "天津", "津", "TJ"]},
        "河北省": {"aliases": ["Hebei", "河北", "冀", "HE"]},
        "山西省": {"aliases": ["Shanxi", "山西", "晋", "SX"]},
        "内蒙古自治区": {"aliases": ["Inner Mongolia", "内蒙古", "蒙", "NM", "Neimenggu", "nmg"]},
        "辽宁省": {"aliases": ["Liaoning", "辽宁", "辽", "LN", ]},
        "吉林省": {"aliases": ["Jilin", "吉林", "吉", "JL"]},
        "黑龙江省": {"aliases": ["Heilongjiang", "黑龙江", "黑", "HL", "hlj"]},
        "上海市": {"aliases": ["Shanghai", "上海", "沪", "SH"]},
        "江苏省": {"aliases": ["Jiangsu", "江苏", "苏", "JS"]},
        "浙江省": {"aliases": ["Zhejiang", "浙江", "浙", "ZJ"]},
        "安徽省": {"aliases": ["Anhui", "安徽", "皖", "AH"]},
        "福建省": {"aliases": ["Fujian", "福建", "闽", "FJ"]},
        "江西省": {"aliases": ["Jiangxi", "江西", "赣", "JX"]},
        "山东省": {"aliases": ["Shandong", "山东", "鲁", "SD"]},
        "河南省": {"aliases": ["Henan", "河南", "豫", "HA"]},
        "湖北省": {"aliases": ["Hubei", "湖北", "鄂", "HB"]},
        "湖南省": {"aliases": ["Hunan", "湖南", "湘", "HN"]},
        "广东省": {"aliases": ["Guangdong", "广东", "粤", "GD"]},
        "广西壮族自治区": {"aliases": ["Guangxi", "广西", "桂", "GX"]},
        "海南省": {"aliases": ["Hainan", "海南", "琼", "HI"]},
        "重庆市": {"aliases": ["Chongqing", "重庆", "渝", "CQ"]},
        "四川省": {"aliases": ["Sichuan", "四川", "川", "蜀", "SC"]},
        "贵州省": {"aliases": ["Guizhou", "贵州", "黔", "GZ"]},
        "云南省": {"aliases": ["Yunnan", "云南", "云", "滇", "YN"]},
        "西藏自治区": {"aliases": ["Tibet", "西藏", "藏", "Xizang", "XZ"]},
        "陕西省": {"aliases": ["Shaanxi", "陕西", "陕", "SN", "秦"]},
        "甘肃省": {"aliases": ["Gansu", "甘肃", "甘", "GS", "陇"]},
        "青海省": {"aliases": ["Qinghai", "青海", "青", "QH"]},
        "宁夏回族自治区": {"aliases": ["Ningxia", "宁夏", "宁", "NX"]},
        "台湾省": {"aliases": ["Taiwan", "台湾", "TW", "台"]},
        "香港特别行政区": {"aliases": ["Hongkong", "香港", "HK", "Hong Kong", "Xianggang", "港"]},
        "澳门特别行政区": {"aliases": ["Macau", "澳门", "MO", "Aomen", "澳"]},
        "新疆维吾尔族自治区": {"aliases": ["Xinjiang", "新疆", "XJ", "新"]},
        '彰化县': {'aliases': ['Changhua County', '彰化', 'zhanghua', 'ch', 'CHA']},
        '嘉义市': {'aliases': ['Chiayi City', 'CYI', "嘉义市"]},
        '嘉义县': {'aliases': ['Chiayi County', "嘉义县", 'cyc', 'cy', 'CYQ']},
        '新竹市': {'aliases': ['Hsinchu City', 'hci', 'HSZ']},
        '新竹县': {'aliases': ['Hsinchu County', 'hcc', 'xinzhu', 'hc', 'HSQ']},
        '花莲县': {'aliases': ['Hualien County', '花莲', 'hualian', 'HUA']},
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
        '云林县': {'aliases': ['Yunlin County', '云林', 'yunlin', 'yl', 'yu']}
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
    "us": {
        "Alabama": {"aliases": ["Alabama", "AL", "Ala.", "阿拉巴马", "阿拉巴馬"]},
        "Alaska": {"aliases": ["Alaska", "AK", "阿拉斯加"]},
        "Arizona": {"aliases": ["Arizona", "AZ", "亞利桑那"]},
        "Arkansas": {"aliases": ["Arkansas", "AR", "阿肯色"]},
        "California": {"aliases": ["California", "CA", "Cali", "加利福尼亚", "加州", "加利福尼亞"]},
        "Colorado": {"aliases": ["Colorado", "CO", "科羅拉多", "科罗拉多"]},
        "Connecticut": {"aliases": ["Connecticut", "CT", "康涅狄格"]},
        "Delaware": {"aliases": ["Delaware", "DE", "特拉华", "特拉華"]},
        "Florida": {"aliases": ["Florida", "FL", "佛罗里达", "佛羅里達", "佛州"]},
        "Georgia": {"aliases": ["Georgia", "GA", "喬治亞", "乔治亚", "佐治亞", "佐治亚"]},
        "Hawaii": {"aliases": ["Hawaii", "HI", "夏威夷"]},
        "Idaho": {"aliases": ["Idaho", "ID", "愛達荷", "爱达荷"]},
        "Illinois": {"aliases": ["Illinois", "IL", "伊利诺伊", "伊利諾伊"]},
        "Indiana": {"aliases": ["Indiana", "IN", "印第安纳", "印第安納"]},
        "Iowa": {"aliases": ["Iowa", "IA", "艾奥瓦", "艾奧瓦", "爱荷华"]},
        "Kansas": {"aliases": ["Kansas", "KS", "堪萨斯", "堪薩斯"]},
        "Kentucky": {"aliases": ["Kentucky", "KY", "肯塔基", "肯塔基"]},
        "Louisiana": {"aliases": ["Louisiana", "LA", "路易斯安那"]},
        "Maine": {"aliases": ["Maine", "ME", "緬因", "缅因"]},
        "Maryland": {"aliases": ["Maryland", "MD", "馬里蘭", "马里兰"]},
        "Massachusetts": {"aliases": ["Massachusetts", "MA", "麻省", "麻薩諸塞", "马萨诸塞"]},
        "Michigan": {"aliases": ["Michigan", "MI", "密歇根", "密西根"]},
        "Minnesota": {"aliases": ["Minnesota", "MN", "明尼蘇達", "明尼苏达"]},
        "Mississippi": {"aliases": ["Mississippi", "MS", "密西西比"]},
        "Missouri": {"aliases": ["Missouri", "MO", "密蘇里", "密苏里"]},
        "Montana": {"aliases": ["Montana", "MT", "蒙大拿"]},
        "Nebraska": {"aliases": ["Nebraska", "NE", "內布拉斯加"]},
        "Nevada": {"aliases": ["Nevada", "NV", "內華達", "内华达"]},
        "New Hampshire": {"aliases": ["New Hampshire", "NH", "新罕布什尔"]},
        "New Jersey": {"aliases": ["New Jersey", "NJ", "新澤西", "新泽西"]},
        "New Mexico": {"aliases": ["New Mexico", "NM", "新墨西哥"]},
        "New York": {"aliases": ["New York", "NY", "紐約", "纽约"]},
        "North Carolina": {"aliases": ["North Carolina", "NC", "北卡罗来纳"]},
        "North Dakota": {"aliases": ["North Dakota", "ND", "北达科他"]},
        "Ohio": {"aliases": ["Ohio", "OH", "俄亥俄"]},
        "Oklahoma": {"aliases": ["Oklahoma", "OK", "俄克拉荷马"]},
        "Oregon": {"aliases": ["Oregon", "OR", "俄勒冈"]},
        "Pennsylvania": {"aliases": ["Pennsylvania", "PA", "宾夕法尼亚", "賓夕法尼亞"]},
        "Rhode Island": {"aliases": ["Rhode Island", "RI", "羅得島", "罗得岛"]},
        "South Carolina": {"aliases": ["South Carolina", "SC", "南卡罗来纳", "南卡羅來納"]},
        "South Dakota": {"aliases": ["South Dakota", "SD", "南达科他", "南達科他"]},
        "Tennessee": {"aliases": ["Tennessee", "TN", "田纳西", "田納西"]},
        "Texas": {"aliases": ["Texas", "TX", "德克萨斯", "德克薩斯", "德州", "得州", "得克萨斯"]},
        "Utah": {"aliases": ["Utah", "UT", "猶他", "犹他"]},
        "Vermont": {"aliases": ["Vermont", "VT", "佛蒙特"]},
        "Virginia": {"aliases": ["Virginia", "VA", "弗吉尼亚", "弗吉尼亞"]},
        "Washington": {"aliases": ["Washington", "WA", "华盛顿"]},
        "West Virginia": {"aliases": ["West Virginia", "WV", "西弗吉尼亚", "西弗吉尼亞"]},
        "Wisconsin": {"aliases": ["Wisconsin", "WI", "威斯康星", "威斯康辛"]},
        "Wyoming": {"aliases": ["Wyoming", "WY", "怀俄明"]},
        "District of Columbia": {"aliases": ["District of Columbia", "DC"]},
    },
    "kr": {
        "Seoul": {
            "aliases": ["Seoul", "se", "so", "11"]
        },
        "Busan": {
            "aliases": ["Busan", "BS", "bu", "pu", "26"]
        },
        "Incheon": {
            "aliases": ["Incheon", "IC", "in", "28"]
        },
        "Daegu": {
            "aliases": ["Daegu", "DG", "da", "27"]
        },
        "Daejeon": {
            "aliases": ["Daejeon", "DJ", "de", "tj", "30"]
        },
        "Gwangju": {
            "aliases": ["Gwangju", "GJ", "gw", "kj", "29"]
        },
        "Ulsan": {
            "aliases": ["Ulsan", "UL", "31"]
        },
        "Gyeonggi": {
            "aliases": ["Gyeonggi", "GG", "kg", "41"]
        },
        "Gangwon": {
            "aliases": ["Gangwon", "ga", "kw", "42"]
        },
        "Chungcheongbuk": {
            "aliases": ["Chungcheongbuk", "CB", "ccb", "hb", "ch", "43"]
        },
        "Chungcheongnam": {
            "aliases": ["Chungcheongnam", "ccn", "hn", "44"]
        },
        "Jeollabuk": {
            "aliases": ["Jeollabuk", "JB", "cb", "jlb", "45"]
        },
        "Jeollanam": {
            "aliases": ["Jeollanam", "JN", "jln", "cn", "46"]
        },
        "Gyeongsangbuk": {
            "aliases": ["Gyeongsangbuk", "gsb", "gy", "kb", "47"]
        },
        "Gyeongsangnam": {
            "aliases": ["Gyeongsangnam", "gs", "gsn", "kn", "48"]
        },
        "Jeju": {
            "aliases": ["Jeju", "JJ", "je", "cj", "49"]
        },
        "Sejong": {
            "aliases": ["Sejong", "SJ", "50"]
        },
    },
    "world": {
        "China": {"aliases": ["China", "CN", "中国", "MO", "HK", "TW"]},
        "Russia": {"aliases": ["Russia", "RU", "俄罗斯"]},
        "United States": {"aliases": ["United States", "US", "VI", "AS", "GU", "MP", "PR", "美国"]},
        "Brazil": {"aliases": ["Brazil", "BR", "巴西"]},
        "Japan": {"aliases": ["Japan", "JP", "日本"]},
        "Germany": {"aliases": ["Germany", "DE", "德国"]},
        "United Kingdom": {"aliases": ["United Kingdom", "GB", "UK", "JE", "IM", "PN", "英国"]},
        "France": {"aliases": ["France", "FR", "法国", "MQ", "Martinique", "Réunion", "Reunion",
                               "RE", "留尼汪", "Saint Pierre and Miquelon", "PM"]},
        "Monaco": {"aliases": ["Monaco", "MC", "摩纳哥"]},
        "São Tomé and Príncipe": {"aliases": ["Sao Tome and Principe", "ST", "圣多美和普林西比", ]},
        "Mexico": {"aliases": ["Mexico", "MX", "墨西哥"]},
        "Canada": {"aliases": ["Canada", "CA", "加拿大"]},
        "Australia": {"aliases": ["Australia", "AU", "澳大利亚", "CC", "CX"]},
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
        "Finland": {"aliases": ["Finland", "FI", "AX", "芬兰"]},
        "Switzerland": {"aliases": ["Switzerland", "CH", "瑞士"]},
        "Austria": {"aliases": ["Austria", "AT", "奥地利"]},
        "Netherlands": {"aliases": ["Netherlands", "NL", "CW", "荷兰", "Curacao"]},
        "Czech Republic": {"aliases": ["Czech Republic", "CZ", "捷克"]},
        "Slovakia": {"aliases": ["Slovakia", "SK", "斯洛伐克"]},
        "Romania": {"aliases": ["Romania", "RO", "罗马尼亚"]},
        "Portugal": {"aliases": ["Portugal", "PT", "葡萄牙"]},
        "Greece": {"aliases": ["Greece", "GR", "希腊"]},
        "Cyprus": {"aliases": ["Cyprus", "CY", "塞浦路斯"]},
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
        "United Arab Emirates": {"aliases": ["United Arab Emirates", "AE", "阿联酋"]},
        "Dominican Republic": {"aliases": ["Dominican Republic", "DO", "多尼米加"]},
        "Rwanda": {"aliases": ["Rwanda", "RW", "卢旺达"]},
        "Tanzania": {"aliases": ["Tanzania", "TZ", "坦桑尼亚"]},
        "Mozambique": {"aliases": ["Mozambique", "MZ", "莫桑比克"]},
        "Zimbabwe": {"aliases": ["Zimbabwe", "ZW", "津巴布韦"]},
        "Zambia": {"aliases": ["Zambia", "ZM", "赞比亚"]},
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
