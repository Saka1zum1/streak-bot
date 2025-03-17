import asyncio
import aiofiles
import requests
import discord
import json
import time
import os
import re
import random
import logging
from datetime import datetime
from app.utils.geoutil import haversine, get_tile_url
from app.utils.maps_api import make_request, get_address, reverse_geocode, get_qq_pano, get_google_pano, get_bd_pano, parse_meta
from app.utils.image_helper import get_perspective_pano, process_image
from app.config import GEOGUESSR_COOKIE, USER_AGENT, STREAK_MAPS, REGION_TYPES, MAPS_NAME
from iso3166 import countries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
base_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录的绝对路径
root_dir = os.path.abspath(os.path.join(base_dir, '..', '..'))  # 通过上移两级来获得项目根目录


def load_json(filename):
    data_file_path = os.path.join(root_dir, 'storage', filename)  # 构建绝对路径
    with open(data_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# 加载所有的 JSON 数据
state_code_refer = load_json('code_refer.json')
address_refer = load_json('address_refer.json')
baidu_seeds = load_json('baidu_seeds.json')
qq_seeds = load_json('qq_seeds.json')


class StreakGame:
    def __init__(self):
        self.last_save_time = time.time()
        self.streak_status = None
        self.guess_status = False
        self.current_map = None
        self.current_seed = None
        self.current_answer = None
        self.current_pano = None
        self.current_token = None
        self.current_mapId = None
        self.streak_mode = None
        self.game_mode = 'solo'
        self.current_guesses = []
        self.streak_maps = STREAK_MAPS
        self.streak_stats = load_json('streak_data.json')

    def get_pano_link(self):
        if self.current_map == 'baidu':
            return f"https://map.baidu.com/?newmap=1&shareurl=1&panoid={self.current_pano}&panotype=street&heading={self.current_seed['heading']}&pitch={self.current_seed['pitch']}&l=21&tn=B_NORMAL_MAP&sc=0&newmap=1&shareurl=1&pid={self.current_pano}"
        elif self.current_map == 'qq':
            return f"https://qq-map.netlify.app/#base=roadmap&zoom=18&center={self.current_seed['lat']}%2C{self.current_seed['lng']}&pano={self.current_pano}"
        return f"https://www.google.com/maps/@?api=1&map_action=pano&pano={self.current_pano}&heading={self.current_seed['heading']}"

    def get_description_text(self, is_streak, answer_title_0, answer_title_1, map_url):
        if is_streak:
            return f"It was indeed [**{answer_title_0}, {answer_title_1}**]({map_url})." if answer_title_1 else f"It was indeed [**{answer_title_0}**]({map_url})."
        return f"The right answer was [**{answer_title_0}, {answer_title_1}**]({map_url})." if answer_title_1 else f"The right answer was [**{answer_title_0}**]({map_url})."

    async def save_streak_data(self):
        """异步保存数据，避免频繁写文件。"""
        try:
            async with aiofiles.open('storage/streak_data.json', 'w') as f:
                await f.write(json.dumps(self.streak_stats, indent=4, ensure_ascii=False))
        except Exception as e:
            print(f"Error saving streak data: {e}")

    async def get_seed(self, tk):
        url = f"https://www.geoguessr.com/api/v3/games/{tk}"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Cookie": GEOGUESSR_COOKIE
        }

        data = make_request(url, method='GET', headers=headers)
        if data and data.get('rounds'):
            self.current_seed = data['rounds'][-1]
            if len(data['rounds']) < 4:
                await self.make_guess(tk)
            else:
                self.current_token = await self.create_game()

    async def create_game(self):
        url = "https://www.geoguessr.com/api/v3/games"
        headers = {
            "Content-Type": "application/json",
            "Cookie": GEOGUESSR_COOKIE,
            "User-Agent": USER_AGENT
        }
        payload = {
            "map": self.current_mapId,
            "type": "standard",
            "timeLimit": 0,
            "forbidMoving": False,
            "forbidZooming": False,
            "forbidRotating": False,
            "rounds": 5
        }

        data = make_request(url, method='POST', headers=headers, data=payload)
        if data:
            return data['token']

    async def make_guess(self, tk):
        url = f"https://www.geoguessr.com/api/v3/games/{tk}"
        headers = {
            "Content-Type": "application/json",
            "Cookie": GEOGUESSR_COOKIE,
            "User-Agent": USER_AGENT
        }
        payload = {
            "token": tk,
            "lat": round(random.uniform(-60, 60), 2),
            "lng": round(random.uniform(-180, 180), 2),
            "timedOut": False,
            "stepsCount": random.randint(2, 8)
        }

        make_request(url, method='POST', headers=headers, data=payload)

    async def get_answer(self):
        if self.streak_mode == 'country':
            self.current_answer = await self.get_country_answer()
        else:
            self.current_answer = await self.get_state_answer()
        logger.info(self.current_answer)

    async def get_country_answer(self):
        countrycode = self.current_seed['streakLocationCode']
        if countrycode in ['tw', 'hk', 'mo']:
            return {'pool': ['China', 'cn']}
        full_name = countries.get(countrycode)
        if full_name:
            return {'pool': [full_name.name.lower(), countrycode]}
        print('Failed to get country!')
        return {'pool': [countrycode, 'Unknown']}

    async def get_state_answer(self):
        try:
            if self.current_map in ['baidu', 'qq']:
                return reverse_geocode(self.current_seed['lng'], self.current_seed['lat'])
            return get_address(self.current_pano)
        except Exception as e:
            print(f"Failed to get answer address! {e}")
            return None

    async def process_guess(self, formatted_guess, guess, player, message):
        self.guess_status = False
        if self.game_mode == 'assist':
            player = 'assist'
        if self.streak_mode == 'state':
            self.current_answer = await self.correct_state_guess()

        if all(ans not in [guess, formatted_guess] for ans in self.current_answer['pool']):
            await self.handle_wrong_guess(player, message)
        else:
            await self.handle_correct_guess(player, message)

    async def correct_state_guess(self):
        try:
            correct_address = address_refer[self.current_map][self.current_answer['state'].lower()]
            self.current_answer['state'] = correct_address
            self.current_answer['pool'].append(correct_address)
        except KeyError:
            pass
        return self.current_answer

    async def handle_wrong_guess(self, player, message):
        streak_peak = self.streak_stats[str(player)][self.current_map]['current_streak']
        region_name = REGION_TYPES.get(self.current_map, "region")
        if self.streak_mode == 'state':
            wrong_text = f'**Your streak ended after correctly guessing {streak_peak} {region_name}{"s" if streak_peak > 1 else ""}!**'
        else:
            wrong_text = f'**Your streak ended after correctly guessing {streak_peak} {"countries" if streak_peak > 1 else "country"}!**'
        self.streak_stats[str(player)][self.current_map]['current_streak'] = 0
        self.streak_stats[str(player)][self.current_map]['total_guess'] += 1
        self.current_guesses.append(player)
        await message.add_reaction('❌')
        await self.send_embed_message(1, message, player, False, wrong_text if streak_peak > 2 else "**Incorrect.**")

    async def handle_correct_guess(self, player, message):
        self.streak_stats[str(player)][self.current_map]['total_guess'] += 1
        self.streak_stats[str(player)][self.current_map]['current_streak'] += 1
        self.streak_stats[str(player)][self.current_map]['total_streak'] += 1

        if self.streak_stats[str(player)][self.current_map]['best_streak'] < \
                self.streak_stats[str(player)][self.current_map]['current_streak']:
            self.streak_stats[str(player)][self.current_map]['best_streak'] += 1

        if self.streak_stats['record'][self.current_map]['count'] < self.streak_stats[str(player)][self.current_map][
            'current_streak']:
            self.streak_stats['record'][self.current_map]['count'] += 1
            self.streak_stats['record'][self.current_map]['players'] = [
                {"id": player,
                 "time": datetime.now().strftime("%Y-%m-%d"),
                "name": message.author.global_name}]

            if self.game_mode == 'assist':
                right_text = "**Congrats! You broke the assisted record.** :goat:"
            else:
                right_text = "**Congrats! You broke the record.** :goat:"

        elif self.streak_stats['record'][self.current_map]['count'] == \
                    self.streak_stats[str(player)][self.current_map]['current_streak']:
                if player not in self.streak_stats['record'][self.current_map]['players']:
                    current_time = datetime.now().strftime("%Y-%m-%d")
                    self.streak_stats['record'][self.current_map]['players'].append({
                        "id": player,
                        "time": current_time,
                        "name": message.author.global_name
                    })
                if self.game_mode == 'assist':
                    right_text = "**Congrats! You tied the assisted record.** :goat:"
                else:
                    right_text = "**Congrats! You tied the record.** :goat:"
        else:
            right_text = "**Correct.**"
        await self.send_embed_message(1, message, player, True, right_text)
        await asyncio.sleep(0.5)
        await self.send_embed_message(2, message, player, True, None)       

    async def send_embed_message(self, type, message, player, is_streak, content):
        embed = None
        answer_title_0, answer_title_1, answer_locality, map_url = None, None, None, None

        if self.current_answer:
            answer_title_0 = self.current_answer['state'].title() if self.streak_mode != 'country' else \
                self.current_answer['pool'][0].title()
            answer_title_1 = self.current_answer[
                'subdivision'].title() if 'subdivision' in self.current_answer else None
            answer_locality = self.current_answer.get('locality', None)
            map_url = self.get_pano_link()

        if type == 1:
            description_text = self.get_description_text(is_streak, answer_title_0, answer_title_1, map_url)
            embed_color = discord.Color.green() if is_streak else discord.Color.red()
            embed = discord.Embed(title=content, description=description_text, color=embed_color)

            if answer_locality:
                embed.set_footer(text=f"Locality: {answer_locality.title()}")

            tile_url = get_tile_url(self.current_seed['lat'], self.current_seed['lng'],
                                    self.current_map in ['baidu', 'qq'])
            embed.set_image(url=tile_url)

        elif type == 2:
            embed = discord.Embed(color=discord.Color.blue())
            fields = {
                ":dart:*Current Game*": f"`NMPZ {self.streak_mode.title()} Streak`",
                ":map:*Current Map*": f"`{MAPS_NAME.get(self.current_map, 'Unknown')}`",
                ":fire:*Current Streak*": f"`{self.streak_stats[str(player)][self.current_map]['current_streak']}`",
                ":trophy:*Best Streak*": f"`{self.streak_stats[str(player)][self.current_map]['best_streak']}`"
            }

            embed.set_footer(text=f"{message.author.global_name}")
            for name, value in fields.items():
                embed.add_field(name=name, value=value, inline=False)

        elif type == 3:
            embed = discord.Embed(title=f"**{MAPS_NAME.get(self.current_map, 'Unknown')}**",
                                  description=f"NMPZ {self.streak_mode.title()} Streak", color=discord.Color.blue())
            footer_text = "!i <country/countrycode> to guess" if self.streak_mode == 'country' else f"!i <{REGION_TYPES.get(self.current_map, 'region')}> to guess"
            embed.set_footer(text=footer_text)

        elif type == 4:
            description_text = None if is_streak else self.get_description_text(is_streak, answer_title_0,
                                                                                answer_title_1, map_url)
            embed = discord.Embed(title=f"**{content}**", description=description_text, color=discord.Color.yellow())

        elif type == 5:
            embed = discord.Embed(
                title=f"{MAPS_NAME.get(self.current_map, 'Unknown').title()}",
                description=f"**{self.streak_stats['record'][self.current_map]['count']}** Streaks",
                color=discord.Color.purple()
            )

            if self.game_mode != 'assist':
                for player in self.streak_stats['record'][self.current_map]['players']:
                    player_name = player.get('name', 'Unknown')
                    embed.add_field(name=f":medal: **{player_name}**", value=f"*{player['time']}*", inline=True)

        elif type == 6:
            embed = discord.Embed(
                title="5K!",
                description=content,
                color=discord.Color.green()
            )
            embed.set_thumbnail(
                url="https://www.iculture.nl/wp-content/uploads/mediacloud/2022/11/google-street-view-400x400.png")
            embed.set_footer(
                text=f"You have now pinpointed a total of {self.streak_stats[str(player)]['pinpointed']} "
                     f"{'rounds' if self.streak_stats[str(player)]['pinpointed'] > 1 else 'round'}."
            )

        if embed:
            await message.channel.send(embed=embed)

    async def send_streak_image(self, message):
        self.current_message = None

        if self.current_map == 'qq':
            random_seed = random.choice(qq_seeds['seeds'])
            self.current_seed = await get_qq_pano(random_seed)
        elif self.current_map == 'baidu':
            random_seed = random.choice(baidu_seeds['seeds'])
            self.current_seed = await get_bd_pano(random_seed)
        else:
            await self.get_seed(self.current_token)

        if self.current_map in ['qq', 'baidu'] and self.current_seed:
            self.current_pano = self.current_seed['panoId']
            self.current_seed['width'] = 8192
            self.current_seed['height'] = 4096
            await self.get_answer()
        else:
            metadata = get_google_pano("SingleImageSearch",
                                       {"lat": self.current_seed['lat'], "lng": self.current_seed['lng']}, None,
                                       None, 30)
            if metadata:
                self.current_pano = parse_meta(metadata)[0]
                self.current_seed['originHeading'] = parse_meta(metadata)[-1]
                self.current_seed['width'] = parse_meta(metadata)[2]
                self.current_seed['height'] = parse_meta(metadata)[3]
                await self.get_answer()
            else:
                print("Failed to parse metadata.")

        # 如果地址解析失败，重新挑选种子
        if not self.current_answer:
            time.sleep(0.5)
            print("Failed to get address information, retrying with a new seed...")
            await self.send_streak_image(message)
        else:
            if self.current_pano and self.current_seed:
                image_data = await get_perspective_pano(self.current_pano,
                                                        self.current_seed['width'],
                                                        self.current_seed['height'],
                                                        self.current_seed['heading'],
                                                        self.current_seed['originHeading'],
                                                        self.current_seed['pitch'])
                image_bytes = await asyncio.to_thread(process_image, image_data)

                if image_bytes:
                    file = discord.File(image_bytes, filename="streak.png")
                    self.current_message = await message.channel.send(file=file)
                    self.current_guesses = []
                    self.guess_status = True

                else:
                    print("Failed to fetch the image.")
                    await self.send_streak_image(message)

    async def process_pinpoint(self, message, lat, lng):
        player = message.author.id
        if self.current_seed and 'lat' in self.current_seed:
            distance = haversine((lat, lng), (self.current_seed['lat'], self.current_seed['lng']))
            if distance <= 50:
                await self.handle_pinpoint_correct(message, player, distance)
            else:
                await message.add_reaction('❌')

    async def handle_pinpoint_correct(self, message, player, distance):
        self.streak_stats[str(player)]['pinpointed'] += 1
        if self.streak_stats['record']['pinpointed']['count'] < self.streak_stats[str(player)]['pinpointed']:
            self.streak_stats['record']['pinpointed']['count'] += 1
            self.streak_stats['record']['pinpointed']['players'] = [
                {"id": player, "time": datetime.now().strftime("%Y-%m-%d")}]
        await self.send_embed_message(6, message, player, True,
                                      f"<@{str(player)}> guessed `{int(distance)}` metres from the correct location!")
        await asyncio.sleep(1)
        await self.process_guess(self.current_answer['pool'][0], self.current_answer['pool'][0], player, message)
        await self.keep_round_ongoing(message)

    async def keep_round_ongoing(self, message):
        """继续当前回合的逻辑，减少内存占用，延迟保存文件。"""
        if self.current_map == 'baidu' or self.current_map == 'qq':
            if self.current_answer and self.current_seed:
                await self.send_streak_image(message)
                self.streak_status = True

        else:
            if self.current_token:
                await self.send_streak_image(message)
                self.streak_status = True

        if time.time() - self.last_save_time > 3600:  # 60秒保存一次
            await self.save_streak_data()
            self.last_save_time = time.time()  # 更新保存时间

    async def handle_message(self, message):
        content = message.content.lower()

        if str(message.author.id) not in self.streak_stats.keys():
            self.streak_stats[str(message.author.id)] = {
            }
        for streak_map in self.streak_maps.keys():
            if streak_map not in self.streak_stats[str(message.author.id)].keys():
                self.streak_stats[str(message.author.id)][streak_map] = {
                    "total_guess": 0,
                    "current_streak": 0,
                    "best_streak": 0,
                    "total_streak": 0}
        if not self.streak_status:
            if "/;" in content:
                self.streak_mode = 'country'
            else:
                self.streak_mode = 'state'

        if ";end" in content and self.streak_status:
            self.streak_status = False
            self.guess_status = False
            if self.current_answer and self.current_seed:
                await self.send_embed_message(4, message, None, False,
                                              f"{self.streak_mode.title()} Streak ends up.")


        elif ";skip" in content and self.streak_status:
            self.streak_stats[str(message.author.id)][self.current_map]['current_streak'] = 0
            self.guess_status = False

            if self.current_answer and self.current_seed:
                await self.send_embed_message(4, message, None, False, "Round skipped.")

            await self.send_streak_image(message)
            self.guess_status = True

        elif ";_" in content:
            match = re.search(r'_(\S+)', content)
            if match:
                try:
                    code_text = f':flag_{match[1]}:'
                    target_country = state_code_refer[match[1]]
                    for state_code in target_country:
                        code_text += f"\n**{state_code}** :{target_country[state_code].title()}"
                    code_message = await message.channel.send(code_text)
                except:
                    code_message = await message.channel.send('Not exists!')
                await asyncio.sleep(60)
                await code_message.delete()
                await message.delete()

        elif ";pb" in content:
            pb_text = ''

            map_stats = self.streak_stats[str(message.author.id)][self.current_map]

            if map_stats['total_guess'] != 0:
                streak_rate = round(map_stats['total_streak'] * 100 /
                                    map_stats['total_guess'], 2)

                pb_text += (f"\n**{MAPS_NAME[self.current_map]}**\n*Best Streak*: **{map_stats['best_streak']}**\n"
                            f"*Rate*: **{streak_rate}%**\n*Total Streak*:**{map_stats['total_streak']}**\n"
                            f"*Total Guesses*:**{map_stats['total_guess']}**\n"
                            f"*5K*:**{self.streak_stats[str(message.author.id)]['pinpointed']}**"
                            )

            if pb_text != '':
                pb_message = await message.channel.send(f"<@{str(message.author.id)}>" + pb_text)
                await asyncio.sleep(60)
                await pb_message.delete()
                await message.delete()
            return

        elif ";record" in content:
            await self.send_embed_message(5, message, None, False, None)
            return

        elif ";assist" in content and self.streak_status:
            if self.game_mode != 'assist':
                self.game_mode = 'assist'
                await self.send_embed_message(4, message, None, True, 'Assist mode is now enabled.')
            else:
                self.game_mode = 'solo'
                await self.send_embed_message(4, message, None, True, 'Assist mode is now disable.')

        elif ";s2" in content and self.streak_status:
            if self.current_answer and self.current_seed:
                await self.send_embed_message(4, message, None, False, "Switching Map")
            self.guess_status = False
            match = re.search(r';s2(\S+)', content)
            if match:
                self.current_map = match.group(1).strip()

                if self.current_map in self.streak_maps.keys():
                    await self.send_embed_message(3, message, None, True, None)

                    self.current_mapId = self.streak_maps[self.current_map]
                    if self.current_map == 'baidu' or self.current_map == 'qq':
                        await self.send_streak_image(message)
                        self.streak_status = True
                    else:
                        self.current_token = await self.create_game()
                        if self.current_token:
                            await self.send_streak_image(message)
                            self.streak_status = True
                else:
                    await self.send_embed_message(4, message, None, True, "Sorry, we don't have this map.")

        elif "/w " in content and self.streak_status:
            pattern = r"(-?\d+\.\d+),\s*(-?\d+\.\d+)"

            match = re.search(pattern, content)
            if match:
                lat, lng = match.groups()
                await self.process_pinpoint(message, float(lat), float(lng))

        elif "!cg" in content and self.streak_status:
            await message.channel.send(f":map: [Map](https://chatguessr.com/map/PlonkIt)")
        else:
            if ';' in content or '/' in content:
                if self.streak_status:
                    await message.channel.send('There has been an ongoing streak!', reference=self.current_message)
                else:
                    match = re.search(r';(\S+)', content)
                    if match:
                        self.current_map = match.group(1).strip()
                        if self.current_map in self.streak_maps.keys():
                            await self.send_embed_message(3, message, None, True, None)

                            self.current_mapId = self.streak_maps[self.current_map]
                            if self.current_map == 'baidu' or self.current_map == 'qq':
                                await self.send_streak_image(message)
                                self.streak_status = True
                            else:
                                self.current_token = await self.create_game()
                                if self.current_token:
                                    await self.send_streak_image(message)
                                    self.streak_status = True
                        else:
                            await self.send_embed_message(4, message, None, True, "Sorry, we don't have this map.")

            elif ('!i' in content) and message.author.id not in self.current_guesses:

                if not self.guess_status or not self.streak_status:
                    return
                if 'or' in content:
                    parts = content.split('or')
                    parts = [part.strip() for part in parts]  # 去除空格

                    # 确保选择的部分包含 '!i'，否则手动加上
                    valid_parts = [part for part in parts if part.startswith("!i")]
                    content = random.choice(valid_parts) if valid_parts else f"!i {random.choice(parts)}"

                match = re.search(r'!i\s*(.*)', content)
                if match:
                    guess = match.group(1)

                    if self.streak_mode == 'state':
                        try:
                            formatted_guess = state_code_refer[self.current_map][guess].lower()
                        except:
                            formatted_guess = guess
                    else:
                        try:
                            formatted_guess = countries.get(guess).alpha2.lower()
                        except:
                            if guess in ['bolivia', 'bo']:
                                formatted_guess = 'bo'
                            elif guess == 'turkey':
                                formatted_guess = 'tr'
                            else:
                                return
                    await self.process_guess(formatted_guess, guess, message.author.id, message)

                    await self.keep_round_ongoing(message)
