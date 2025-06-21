import discord
from discord.ext import commands
from discord.ext.commands import BucketType, CommandOnCooldown
from regions import REGIONS, RegionFlatmap
from asyncio import Queue, create_task, gather
import os
import io
import asyncio
import random
from typing import Optional, List
from models import GameManager, Pano, Round
from geoguessr import GeoGuessr
import logging
import numpy as np
import sqlite3
import json
from datetime import datetime, UTC
from PIL import Image
import time
from config import *
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler('streaks.log'),
    logging.StreamHandler()
])

load_dotenv()
DISCORD_TOKEN=os.getenv("DISCORD_TOKEN")

class PanoProcessor:
    def __init__(self, max_concurrent: int = 3):
        self.queue: Queue = Queue()
        self.max_concurrent = max_concurrent
        self.active_tasks: List[create_task] = []

    async def add_pano(self, pano: Pano, heading: float, pitch: float) -> None:
        await self.queue.put((pano, heading, pitch))

    async def process_pano(self, pano: Pano, heading: float, pitch: float) -> Optional[np.ndarray]:

        try:
            numpy_result = await pano.get_panorama(heading, pitch)
            if numpy_result is None:
                return None
            pano.img = Pano.add_compass(numpy_result,
                                        heading if len(pano.pano_id) == 22 or not pano.driving_direction
                                        else pano.driving_direction)
            return pano.img
        except Exception as e:
            logging.error(f"Error processing pano {pano.pano_id}: {e}")
            return None

    async def worker(self):
        while True:
            pano, heading, pitch = await self.queue.get()
            try:
                await self.process_pano(pano, heading, pitch)
            finally:
                self.queue.task_done()

    async def start(self):
        self.active_tasks = [
            create_task(self.worker())
            for _ in range(self.max_concurrent)
        ]

    async def stop(self):
        # Cancel all workers
        for task in self.active_tasks:
            task.cancel()
        # Wait for all tasks to complete
        await gather(*self.active_tasks, return_exceptions=True)


class GeoGuessrBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=['!', '/w PlonkIt !'], intents=intents, case_insensitive=True,
                         help_command=None,
                         proxy="http://127.0.0.1:7890")

        # Managers
        self.geoguessr_games = {}  # channel_id -> GeoGuessr
        self.game_manager = GameManager(RegionFlatmap(REGIONS[DEFAULT_MAP['map_code']]))
        self.pano_processor = PanoProcessor(max_concurrent=3)
        self.add_commands()
        self.streak_mode = "state"

    async def setup_hook(self):
        await self.pano_processor.start()

    async def on_ready(self):
        logging.info(f"{self.user} has connected.")

        for channel_id in ALLOWED_CHANNELS:
            channel = self.get_channel(channel_id)
            if channel:
                # Check if there's saved state in the DB
                if self.game_manager.has_saved_state(channel_id):
                    logging.debug("Restoring game for channel" + str(channel_id))
                    await self.restore_game(channel)
                else:
                    logging.debug("Starting new game for channel" + str(channel_id))
                    await self.start_new_game(channel)

    async def close(self):
        logging.info("Bot is shutting down, saving all game states...")

        for channel_id in self.geoguessr_games.keys():
            try:
                game = self.geoguessr_games[channel_id]
                self.game_manager.save_state(channel_id, game.game)
            except Exception as e:
                logging.error(f"Failed to save state for channel {channel_id}: {e}")

    async def on_error(self, event_method: str, *args, **kwargs):
        """Called when an event raises an uncaught exception"""
        logging.error(f"Error in {event_method}: {args}, {kwargs}")

        # If we can identify the channel from the event, save its state
        try:
            if args and hasattr(args[0], 'channel'):
                channel_id = args[0].channel.id
                if channel_id in self.geoguessr_games:
                    self.game_manager.save_state(channel_id)
        except Exception as e:
            logging.error(f"Failed to save state during error handling: {e}")

        # Log the actual error
        import traceback
        traceback.print_exc()

    async def on_command_error(self, ctx, error):
        """Called when a command raises an error"""
        try:
            if ctx.channel.id in self.geoguessr_games:
                self.game_manager.save_state(ctx.channel.id, self.geoguessr_games[ctx.channel.id].game)
        except Exception as e:
            logging.error(f"Failed to save state during command error: {e}")

        if isinstance(error, commands.CommandNotFound):
            logging.error("Command not found: " + str(ctx.message.content))
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to do that.")
        else:
            logging.error(f"Command error: {error}")

    async def restore_game(self, channel):
        """Restore a previously saved game state for a channel"""
        # Get saved state from db
        with sqlite3.connect(self.game_manager.db_path) as conn:
            row = conn.execute(
                "SELECT game_data, current_round, next_round, streak FROM game_state WHERE channel_id = ?",
                (channel.id,)
            ).fetchone()

        if not row:
            await self.start_new_game(channel)
            return

        game_data, current_round, next_round, streak = row

        if not game_data or not current_round:
            await self.start_new_game(channel)
            return

        # Reconstruct game state
        game_data = json.loads(game_data)
        self.geoguessr_games[channel.id] = GeoGuessr()
        self.geoguessr_games[channel.id].game = game_data

        if game_data.get("map") in WORLD_MAPS:
            self.streak_mode = 'country'
            self.game_manager.reset_subdivisions(RegionFlatmap(REGIONS["world"]))
        else:
            self.streak_mode = 'state'
            for map_id, names in MAPS.items():
                if game_data.get("map") == map_id:
                    self.game_manager.reset_subdivisions(RegionFlatmap(REGIONS[names[-1]]))
        # Restore round objects
        current = json.loads(current_round)
        next_r = json.loads(next_round)

        # Reconstruct Round objects and fetch their images
        self.game_manager.rounds[channel.id] = await Round.reconstruct_round(current, self.pano_processor)
        self.game_manager.next_rounds[channel.id] = await Round.reconstruct_round(next_r, self.pano_processor)

        # Restore game manager state
        self.game_manager.streak[channel.id] = streak
        self.game_manager.waiting_for_guess[channel.id] = True

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.channel.id not in ALLOWED_CHANNELS:
            return

        await self.process_commands(message)

    async def process_round(self, game_data: dict, round_index: int, channel=None) -> Round:
        """Process a specific round from the game data"""
        round_data = game_data['rounds'][round_index]
        round = Round(round_data)

        if game_data['map'] == 'baidu':
            await self.pano_processor.process_pano(round.pano, round.heading, round.pitch)
            round_data['lat'] = round.pano.lat
            round_data['lng'] = round.pano.lng

            await round.set_subdivision(round_data, self.streak_mode)

            logging.info(f"Finished set_subdivision for round {round_index}.")

        else:
            map_to_pano_id = {
                '65d37bc2d172e33f7ba44793': 'yandex',
                '65ce73b83267cf12aae3b604': 'yandex'
            }

            if game_data['map'] in map_to_pano_id and not round.pano.pano_id:
                round.pano.pano_id = map_to_pano_id[game_data['map']]
            tasks = await gather(
                self.pano_processor.process_pano(round.pano, round.heading, round.pitch),
                round.set_subdivision(round_data, self.streak_mode)
            )
            if any(task is None for task in tasks):
                logging.error(f"Error processing round {round_index}")
                await channel.send(f"Error processing round {round_index}. Use `!fix`")

        return round

    async def start_new_game(self, channel, map_id=None):
        """Start a new game in the specified channel"""
        logging.info(f"{channel.id}: Starting new game")
        self.game_manager.reset_5k_attempts(channel.id)

        if not map_id:
            if channel.id in self.geoguessr_games:
                logging.debug(f"Using current map from existing game")
                map_id = self.geoguessr_games[channel.id].game.get('map')

            if not map_id:
                with sqlite3.connect(self.game_manager.db_path) as conn:
                    result = conn.execute("""
                        SELECT map 
                        FROM rounds 
                        WHERE channel_id = ? 
                        AND map IS NOT NULL 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """, (channel.id,)).fetchone()
                    if result:
                        map_id = result[0]

        # Initialize with default map if needed
        if channel.id not in self.geoguessr_games:
            self.geoguessr_games[channel.id] = GeoGuessr()
            if not map_id:
                self.streak_mode = 'state'
                self.game_manager.reset_subdivisions(RegionFlatmap(REGIONS[DEFAULT_MAP['map_code']]))
            elif map_id in WORLD_MAPS:
                self.streak_mode = 'country'
                self.game_manager.reset_subdivisions(RegionFlatmap(REGIONS["world"]))
            else:
                self.streak_mode = 'state'
                for mapid, names in MAPS.items():
                    if mapid == map_id:
                        self.game_manager.reset_subdivisions(RegionFlatmap(REGIONS[names[-1]]))
            self.game_manager.streak[channel.id] = 0

        game = await self.geoguessr_games[channel.id].create_geoguessr_game(map_id)

        # Store the map name for display
        with sqlite3.connect(self.game_manager.db_path) as conn:
            result = conn.execute("""
                SELECT map_name FROM maps 
                WHERE map_id = ?
            """, (self.geoguessr_games[channel.id].map_id,)).fetchone()
            if result:
                self.geoguessr_games[channel.id].map_name = result[0]

        game = await self.geoguessr_games[channel.id].guess_and_advance()
        current_idx = game.get('round') - 2

        logging.info(f"{channel.id}: Processing rounds {current_idx} and {current_idx + 1}")
        tasks = [
            self.process_round(game, current_idx, channel),  # Current round
            self.process_round(game, current_idx + 1, channel)  # Next round
        ]

        results = await gather(*tasks)
        if not any(results):
            logging.error(f"{channel.id}: Error processing rounds")
            await channel.send("Error processing rounds. Use !fix.")
            return

        self.game_manager.rounds[channel.id] = results[0]
        self.game_manager.next_rounds[channel.id] = results[1]

        await self.show_round(channel)
        self.game_manager.waiting_for_guess[channel.id] = True

    async def start_new_round(self, channel):
        logging.info(f"{channel.id}: Starting new round")
        self.game_manager.reset_5k_attempts(channel.id)

        if channel.id not in self.geoguessr_games:
            await self.start_new_game(channel)
            return

        geoguessr = self.geoguessr_games[channel.id]
        if channel.id in self.game_manager.next_rounds:
            logging.info(f"{channel.id}: Got prefetch for round {geoguessr.game.get('round')}")
            self.game_manager.rounds[channel.id] = self.game_manager.next_rounds[channel.id]
            del self.game_manager.next_rounds[channel.id]

            # Start the show_round immediately
            show_task = create_task(self.show_round(channel))

            # Start processing next round in background
            game = await geoguessr.guess_and_advance()
            if not game:
                logging.debug("WARNING: Game not found after advancing.")
                await self.start_new_game(channel)
                return

            current_idx = game.get('round') - 1
            if current_idx < len(game['rounds']):
                async def process_next():
                    next_round = await self.process_round(game, current_idx, channel)
                    if next_round:
                        self.game_manager.next_rounds[channel.id] = next_round

                create_task(process_next())

            await show_task
        else:
            await self.start_new_game(channel)

    async def show_round(self, channel):
        logging.info(f"{channel.id}: Showing round")

        try:
            if channel.id not in self.game_manager.rounds:
                embed = self.create_embed(3, channel.id, "**No active round available**.", color=discord.Color.red())
                await channel.send(embed=embed)
                return

            round_obj = self.game_manager.rounds[channel.id]
            map_name = self.geoguessr_games[channel.id].game.get('mapName', None)

            if round_obj.pano.img is None:
                return

            async def send_image():
                img_byte_arr = io.BytesIO()
                round_obj.pano.img.save(img_byte_arr, format='JPEG', quality=100)
                img_byte_arr.seek(0)

                embed = self.create_embed(2, channel.id, map_name if map_name else "Current Game",
                                          f"*Current Streak*: **{self.game_manager.streak[channel.id]}**",
                                          )

                # Send messages
                await channel.send(embed=embed)

                await channel.send(file=discord.File(img_byte_arr, 'round.jpg'))
                self.game_manager.waiting_for_guess[channel.id] = True

            create_task(send_image())

        except Exception as e:
            logging.error(f"{channel.id}: Error showing round: {e}")
            await channel.send("Unable to show image at this time.")

    async def notify_top_streak(self, ctx, streak_number: int):
        """
        Check if the ended streak is in any top 5 and notify the channel.
        """
        achievements = await self.game_manager.check_if_top_streak(ctx.channel.id, streak_number)

        if not achievements or streak_number <= 0:
            return

        # Format achievement message
        category_messages = []
        has_first_place = any(position == 1 for _, position in achievements)
        for category, position in achievements:
            position_text = {1: "1st", 2: "2nd", 3: "3rd"}.get(position, f"{position}th")
            if category == "all":
                category_messages.append(f"{position_text} place overall")
            else:
                category_messages.append(f"{position_text} place in {category}")

        achievement_text = " and ".join(category_messages)

        embed = self.create_embed(4, ctx, "🏆 New Server Record!" if has_first_place else "🏆 New Top 5 Streak!",
                                  f"Your streak of **{streak_number}** made it to {achievement_text}!",
                                  color=discord.Color.gold())

        await ctx.send(embed=embed)

    def create_embed(self, mode, ctx, title=None, content=None, round_obj=None, is_correct=None, streak_peak=None,
                     color=None):
        try:
            current_game = self.geoguessr_games[ctx.channel.id].game
        except:
            current_game = self.geoguessr_games[ctx].game

        if mode == 1:
            actual_name = self.game_manager.subdivisions.get_canonical_name(round_obj.subdivision)
            if not actual_name and round_obj.subdivision:
                actual_name = round_obj.subdivision.title()
            if is_correct:
                title = "**Correct**."
                content = (
                    f"It was indeed [**{actual_name}, {round_obj.adm_2}**]({round_obj.link})."
                    if round_obj.adm_2 else f"It was indeed [**{actual_name}**]({round_obj.link})."
                )
                color = discord.Color.green()
            else:
                if streak_peak is not None or streak_peak == 0:
                    region_name = next((REGIONS_NAMES[k]['plural'] for k, v in REGIONS_NAMES.items() if
                                        current_game.get('map') in REGIONS_NAMES[k]['maps']), 'regions')
                    title = "**Incorrect**." if streak_peak < 3 \
                        else f"Your streak ended after correctly guessing {streak_peak} {region_name}."

                    content = (
                        f"The right answer was [**{actual_name}, {round_obj.adm_2}**]({round_obj.link})."
                        if round_obj.adm_2 else f"The right answer was [**{actual_name}**]({round_obj.link})."
                    )
                    color = discord.Color.red()
                else:
                    title = "**Round skipped**."
                    content = (
                        f"The right answer was [**{actual_name}, {round_obj.adm_2}**]({round_obj.link})."
                        if round_obj.adm_2 else f"The right answer was [**{actual_name}**]({round_obj.link})."
                    )
                    color = discord.Color.yellow()
            embed = discord.Embed(title=title, description=content, color=color)
            if round_obj.locality:
                embed.set_footer(text=f"Locality: {round_obj.locality}")

            embed.set_image(url=round_obj.tile_link)

        elif mode == 2:
            if not color:
                color = discord.Color.blue()
            embed = discord.Embed(title=title, description=content, color=color)
            if current_game:
                region_name = next((k for k, v in REGIONS_NAMES.items() if
                                    current_game.get('map') in REGIONS_NAMES[k]['maps']), 'region')
                embed.set_footer(text=f"!g <{region_name}> to guess")

        elif mode == 3:
            embed = discord.Embed(title=title, description=content, color=color)
        else:
            embed = discord.Embed(title=title, description=content, color=color)
            embed.set_footer(text=f"{ctx.author.global_name}")

        return embed

    def add_commands(self):
        async def cooldown_error(ctx, error):
            if isinstance(error, CommandOnCooldown):
                if ctx.author.guild_permissions.administrator:
                    await ctx.reinvoke()
                else:
                    await ctx.message.add_reaction('⏳')

        @self.command(name='guess', aliases=['g', 'i'])
        @commands.cooldown(1, 0.5, BucketType.user)
        async def guess(ctx, *, guess_text: Optional[str]):
            # Use a lock per channel to ensure serial execution
            if not hasattr(self, 'guess_locks'):
                self.guess_locks = {}

            if ctx.channel.id not in self.guess_locks:
                self.guess_locks[ctx.channel.id] = asyncio.Lock()

            async with (self.guess_locks[ctx.channel.id]):
                # Are we waiting for a guess?
                if not self.game_manager.waiting_for_guess.get(ctx.channel.id, False):
                    logging.error(f"{ctx.message.id}: Not waiting for a guess right now.")
                    return

                self.game_manager.waiting_for_guess[ctx.channel.id] = False
                logging.info(f"{ctx.channel.id}: Guessed - " + str(guess_text))

                try:
                    # Is there a guess?
                    if not guess_text:
                        embed = discord.Embed(description="**Please provide a guess**.", color=discord.Color.red())
                        await ctx.send(embed=embed)
                        self.game_manager.waiting_for_guess[ctx.channel.id] = True  # Unlock if invalid
                        return

                    # Is there an active game?
                    if ctx.channel.id not in self.geoguessr_games:
                        await ctx.send("No active game in this channel. Use !start to begin one.")
                        return

                    # Does the game exist?
                    geoguessr = self.geoguessr_games[ctx.channel.id]
                    if not geoguessr.game:
                        await ctx.send("No game to guess for!")
                        return

                    coord_match = self.game_manager.check_5k_guess(guess_text)
                    if coord_match:
                        round_obj = self.game_manager.rounds[ctx.channel.id]
                        has_attempts, distance = self.game_manager.verify_5k_guess(
                            ctx.channel.id,
                            ctx.author.id,
                            coord_match,
                            round_obj
                        )

                        if not has_attempts:
                            await ctx.message.add_reaction('🛑')
                            self.game_manager.waiting_for_guess[ctx.channel.id] = True
                            return

                        if distance <= FIVE_K_DISTANCE:
                            embed = self.create_embed(4, ctx, f":dart: 5K!",
                                                      f"✓ You guessed the exact location ({distance:.0f}m away).",
                                                      is_correct=True, color=discord.Color.green())
                            embed.set_thumbnail(
                                url="https://www.iculture.nl/wp-content/uploads/mediacloud/2022/11/google-street-view-400x400.png")
                            self.game_manager.streak[ctx.channel.id] += 1

                            # Log the round first to get the ID
                            round_id = self.game_manager.log_round(
                                ctx.channel.id,
                                ctx.author.id,
                                round_obj,
                                round_obj.subdivision,
                                round_obj.subdivision,
                                True,
                                self.geoguessr_games[ctx.channel.id].game.get('map', None)
                            )

                            # Log the 5k with the round ID
                            with sqlite3.connect(self.game_manager.db_path) as conn:
                                conn.execute("INSERT INTO five_k_guesses (round_id) VALUES (?)", (round_id,))
                                conn.commit()

                            await ctx.send(embed=embed)
                            await self.start_new_round(ctx.channel)
                            return
                        else:
                            await ctx.message.add_reaction('❌')
                            self.game_manager.waiting_for_guess[ctx.channel.id] = True
                            return

                    if 'or' in guess_text:
                        guesses = guess_text.split(' or ')
                        if guesses and len(guesses) > 1:
                            guess_text = random.choice(guesses).strip()

                    if not self.game_manager.subdivisions.is_valid_location(guess_text) and \
                            guess_text not in self.game_manager.rounds[ctx.channel.id].pool:
                        embed = self.create_embed(2, ctx, "Invalid guess.",
                                                  color=discord.Color.yellow())
                        self.game_manager.waiting_for_guess[ctx.channel.id] = True
                        await ctx.send(embed=embed)
                        return

                    # Is the guess correct?
                    round_obj = self.game_manager.rounds[ctx.channel.id]

                    actual = round_obj.subdivision
                    actual_name = self.game_manager.subdivisions.get_canonical_name(actual)
                    guess_name = self.game_manager.subdivisions.get_canonical_name(guess_text)

                    is_correct = self.game_manager.subdivisions.verify_guess(guess_text, self.game_manager.rounds[
                        ctx.channel.id].subdivision, round_obj.pool)

                    if is_correct:
                        self.game_manager.streak[ctx.channel.id] += 1
                        embed = self.create_embed(1, ctx, None, None, round_obj, True,
                                                  self.game_manager.streak[ctx.channel.id], )
                    else:
                        ended_streak = self.game_manager.streak[ctx.channel.id]
                        embed = self.create_embed(1, ctx, None, None, round_obj, False,
                                                  ended_streak)

                        self.game_manager.streak[ctx.channel.id] = 0
                        await self.notify_top_streak(ctx, ended_streak)

                    self.game_manager.log_round(
                        ctx.channel.id,
                        ctx.author.id,
                        round_obj,
                        guess_name,
                        actual_name,
                        is_correct,
                        self.geoguessr_games[ctx.channel.id].game.get('map', None)
                    )

                    await ctx.send(embed=embed)

                    await self.start_new_round(ctx.channel)
                except Exception as e:
                    self.game_manager.waiting_for_guess[ctx.channel.id] = True
                    logging.error(f"Error processing guess: {e}")
                    raise e

        @self.command(name='start')
        @commands.has_permissions(administrator=True)
        async def start(ctx):
            """Start a new game and show first round"""
            self.game_manager.streak[ctx.channel.id] = 0
            await self.start_new_game(ctx.channel)

        @self.command(name='pic', aliases=['picture'])
        @commands.cooldown(1, 5, BucketType.user)
        async def show_picture(ctx):
            """Show the current round's picture again"""
            await self.show_round(ctx.channel)

        @self.command(name='streak', aliases=['s'])
        @commands.cooldown(1, 1, BucketType.user)
        async def show_streak(ctx):
            """Show the current round's picture again"""
            map_id = self.geoguessr_games[ctx.channel.id].game.get('map', None)
            map_name = MAPS[map_id][0]

            embed = self.create_embed(2, ctx, map_name if map_name else "Current Game",
                                      f"*Current Streak*: **{self.game_manager.streak[ctx.channel.id]}**")

            await ctx.send(embed=embed)

        @self.command(name='skip')
        @commands.cooldown(1, 0.5, BucketType.user)
        async def skip(ctx):
            """Skips the current round."""
            if ctx.channel.id not in self.geoguessr_games:
                await ctx.send("No active game in this channel. Use !start to begin one.")
                return

            round_obj = self.game_manager.rounds[ctx.channel.id]
            embed = self.create_embed(1, ctx, None, None, round_obj, False)

            await ctx.send(embed=embed)

            if not self.game_manager.waiting_for_guess[ctx.channel.id]:
                logging.error("Not waiting for a guess right now.")
                return

            self.game_manager.streak[ctx.channel.id] = 0
            self.game_manager.waiting_for_guess[ctx.channel.id] = False
            await self.start_new_round(ctx.channel)

        @self.command(name='reset')
        @commands.has_permissions(administrator=True)
        async def reset(ctx, keep_streak: bool = False):
            """Reset the current game"""
            if ctx.channel.id not in self.geoguessr_games:
                await ctx.send("No active game in this channel. Use !start to begin one.")
                return

            if not keep_streak:
                self.game_manager.end_streak(ctx.channel.id)

            await self.start_new_game(ctx.channel)

        @self.command(name='setstreak')
        @commands.has_permissions(administrator=True)
        async def set_streak(ctx, streak: int):
            """Set the current streak"""
            self.game_manager.streak[ctx.channel.id] = streak
            logging.info(f"Streak set to {streak}")

        @self.command(name='edit')
        @commands.has_permissions(administrator=True)
        async def edit_map(ctx, map_name: str = None, map_id: str = None):
            """
            编辑地图的 map_id 并保存到 maps.json
            用法: !edit [map_name] [map_id]
            """
            if not map_name or not map_id:
                embed = discord.Embed(
                    description="Please provide a valid map_name and a map_id!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            json_path = "maps.json"
            # 读取现有JSON
            try:
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        maps_data = json.load(f)
                else:
                    maps_data = {}
            except Exception as e:
                await ctx.send(f"读取 maps.json 失败: {e}")
                return

            # 支持简写（别名）查找
            found_name = None
            for k, v in MAPS.items():
                if map_name.lower() == v[0].lower() or map_name.lower() in [alias.lower() for alias in v[1:]]:
                    found_name = v[0]
                    break
            if not found_name:
                await ctx.send("未找到该地图名，请检查输入。")
                return

            maps_data[found_name] = map_id

            # 保存回JSON
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(maps_data, f, ensure_ascii=False, indent=2)
                await ctx.send(f"已将地图 **{found_name}** 的 map_id 修改为 `{map_id}` 并保存。")
            except Exception as e:
                await ctx.send(f"保存 maps.json 失败: {e}")

        @self.command(name='map')
        @commands.cooldown(1, 0.5, BucketType.user)
        async def map_link(ctx):
            await ctx.send("Here you go!\nhttps://chatguessr.com/map/PlonkIt", suppress_embeds=True)

        @self.command(name='help', aliases=['h'])
        async def help(ctx):
            """Show help information about bot commands"""
            embed = discord.Embed(
                title="Tuxuncord Streak Bot",
                color=discord.Color.blue()
            )

            # Game Commands
            embed.add_field(
                name="Guess commands",
                value=(
                    "`!guess [subdivision]` - Make a guess for the current round\n"
                    "`!pic` - Show the current round's picture again\n"
                    "`!compass` - Show the compass direction for the current round\n"
                    "`!aliases [subdivision/all]` - Show all aliases for a given subdivision\n"
                    "`!participants` - Show all participants in the current streak\n"
                    "`!s2 [map]` - Switch to another map\n"
                    "`!skip` - Skip the current round (resets the streak)\n"
                    "`!map` - Get a link to the ChatGuessr map"
                ),
                inline=False
            )

            # Stats Commands
            embed.add_field(
                name="Stat commands",
                value=(
                    "`!stats` - Show your personal statistics\n"
                    "`!stats global` - Show global statistics"
                    "`!stats subdivisions` - Show your best/worst subdivisions\n"
                    "`!stats global subdivisions` - Show global subdivision statistics"
                    "`!leaderboard` or `!lb` - Show top streaks\n"
                    "→ Add `solo` or `assisted` or `map:[map]`to filter\n"
                    "→ Add `all` to show only all streaks (not top per player)"
                    "`!5k` - Show your 5K statistics"
                ),
                inline=False
            )

            await ctx.send(embed=embed)

        @self.group(name='stats', aliases=['acc', 'accuracy'], invoke_without_command=True)
        @commands.cooldown(1, 1, BucketType.user)
        async def stats(ctx, *args):
            # 1. 提取 map 参数
            map_filter = None
            map_name = None
            map_args = [a for a in args if a.startswith("map:")]
            if map_args:
                map_input = map_args[0][4:].lower()
                for map_id, names in MAPS.items():
                    real_name = names[0]
                    aliases = [real_name.lower()] + [alias.lower() for alias in names[1:]]
                    if map_input in aliases:
                        map_filter = map_id
                        map_name = real_name
                        break

            # 2. 连接数据库并查询 stats
            with sqlite3.connect(self.game_manager.db_path) as conn:
                params = [ctx.author.id]
                query = """
                    SELECT total_guesses, correct_guesses, accuracy, 
                           best_solo_streak, best_assisted_streak, avg_solo_streak
                    FROM player_stats
                    WHERE user_id = ?
                """
                if map_filter:
                    query += " AND map = ?"
                    params.append(map_filter)

                stats = conn.execute(query, params).fetchone()

                if map_filter:
                    world_record_query = """
                        WITH valid_streaks AS (
                            SELECT DISTINCT s.id AS streak_id
                            FROM streaks s
                            JOIN rounds r ON r.streak_id = s.id
                            WHERE r.map = ?
                        ),
                        solo_streaks AS (
                            SELECT s.number
                            FROM streaks s
                            JOIN streak_participants sp ON sp.streak_id = s.id
                            WHERE s.id IN (SELECT streak_id FROM valid_streaks)
                            GROUP BY s.id
                            HAVING COUNT(sp.user_id) = 1
                        )
                        SELECT MAX(number) FROM solo_streaks;
                    """
                    world_record = conn.execute(world_record_query, (map_filter,)).fetchone()[0]
                else:
                    world_record_query = """
                        WITH streak_counts AS (
                            SELECT streak_id, COUNT(*) as participant_count
                            FROM streak_participants
                            GROUP BY streak_id
                            HAVING participant_count = 1
                        )
                        SELECT MAX(s.number)
                        FROM streaks s
                        JOIN streak_counts sc ON s.id = sc.streak_id;
                    """
                    world_record = conn.execute(world_record_query).fetchone()[0]

            # 3. 构造 Embed 输出
            if not stats or stats[0] == 0:
                await ctx.send("No stats recorded yet!")
                return

            total, correct, accuracy, best_solo, best_assisted, avg_solo = stats
            world_record_chance = (accuracy / 100) ** (world_record + 1) * 100

            title = f"Stats for {ctx.author.display_name}"
            if map_name:
                title += f" on **{map_name}**"

            embed = discord.Embed(title=title, color=discord.Color.blue())
            description = [
                f"**Guesses**: {correct}/{total}",
                f"**Accuracy**: {accuracy:.1f}%",
            ]
            if best_solo > 0:
                description.append(f"**Best Solo Streak**: {best_solo}")
            if best_assisted > 0:
                description.append(f"**Best Assisted Streak**: {best_assisted}")
            if avg_solo > 0:
                description.append(f"**Average Solo Streak**: {avg_solo:.2f}")
            description.append(f"Chance of world record: {world_record_chance:.4f}% (**{world_record}**)")

            embed.description = "\n".join(description)
            await ctx.send(embed=embed)

        @stats.command(name='subdivisions', aliases=['subs', 'subdivision', 's'])
        async def personal_stats(ctx, *args):
            # 解析 map: 参数
            map_filter = None
            map_name = None
            map_args = [a for a in args if a.startswith("map:")]
            if map_args:
                map_input = map_args[0][4:].lower()
                for map_id, names in MAPS.items():
                    real_name = names[0]
                    aliases = [real_name.lower()] + [alias.lower() for alias in names[1:]]
                    if map_input in aliases:
                        map_filter = map_id
                        map_name = real_name
                        break

            with sqlite3.connect(self.game_manager.db_path) as conn:
                params = [ctx.author.id]
                where_clause = "user_id = ?"
                if map_filter:
                    where_clause += " AND map = ?"
                    params.append(map_filter)

                # 1. Hardest
                hardest = conn.execute(f"""
                    SELECT actual_location, times_seen, times_correct, accuracy_rate
                    FROM player_subdivision_stats
                    WHERE {where_clause} AND hardest_rank <= 10
                    ORDER BY hardest_rank
                """, params).fetchall()

                # 2. Easiest
                easiest = conn.execute(f"""
                    SELECT actual_location, times_seen, times_correct, accuracy_rate
                    FROM player_subdivision_stats
                    WHERE {where_clause} AND easiest_rank <= 10
                    ORDER BY easiest_rank
                """, params).fetchall()

                # 3. Common Mistakes — 依然从 rounds 表查
                mistake_params = [ctx.author.id]
                mistake_where = "user_id = ? AND NOT is_correct AND guessed_location != '5k guess'"
                if map_filter:
                    mistake_where += " AND map = ?"
                    mistake_params.append(map_filter)

                mistakes = conn.execute(f"""
                    SELECT actual_location, guessed_location,
                           COUNT(*) as mistake_count
                    FROM rounds
                    WHERE {mistake_where}
                    GROUP BY actual_location, guessed_location
                    HAVING mistake_count >= 2
                    ORDER BY mistake_count DESC
                    LIMIT 5
                """, mistake_params).fetchall()

            if not hardest and not easiest:
                await ctx.send("Not enough data yet! You need at least 3 guesses for a subdivision to be ranked.")
                return

            title = f"Subdivisions for {ctx.author.global_name}"
            if map_name:
                title += f" on **{map_name}**"

            embeds = []
            embed = discord.Embed(title=title, color=discord.Color.blue())
            length_so_far = len(title)

            if hardest:
                hard_text = [f"**{loc}** - {correct}/{seen} ({acc}%)" for loc, seen, correct, acc in hardest]
                length_so_far = safe_add_field(embed, "💀 Hardest", hard_text, length_so_far)
                embed, length_so_far = maybe_new_embed(embeds, embed, length_so_far)

            if easiest:
                easy_text = [f"**{loc}** - {correct}/{seen} ({acc}%)" for loc, seen, correct, acc in easiest]
                length_so_far = safe_add_field(embed, "🎯 Easiest", easy_text, length_so_far)
                embed, length_so_far = maybe_new_embed(embeds, embed, length_so_far)

            if mistakes:
                mistake_text = [f"**{actual}** mistaken for **{guess}** ({count} times)" for actual, guess, count in
                                mistakes]
                length_so_far = safe_add_field(embed, "❌ Common Mistakes", mistake_text, length_so_far)
                embed, length_so_far = maybe_new_embed(embeds, embed, length_so_far)

            embeds.append(embed)

            for em in embeds:
                await ctx.send(embed=em)

        @stats.group(name='global', aliases=['g'], invoke_without_command=True)
        async def global_stats(ctx, *args):
            # 解析 map 参数
            map_filter, map_name = None, None
            map_args = [a for a in args if a.startswith("map:")]
            if map_args:
                map_input = map_args[0][4:].lower()
                for map_id, names in MAPS.items():
                    real_name = names[0]
                    aliases = [real_name.lower()] + [alias.lower() for alias in names[1:]]
                    if map_input in aliases:
                        map_filter = map_id
                        map_name = real_name
                        break

            with sqlite3.connect(self.game_manager.db_path) as conn:
                # 构造 SQL
                map_condition = "WHERE map = ?" if map_filter else ""
                params = (map_filter,) if map_filter else ()

                stats = conn.execute(f"""
                    WITH streak_counts AS (
                        SELECT streak_id, COUNT(*) as participant_count
                        FROM streak_participants
                        GROUP BY streak_id
                    ),
                    streak_stats AS (
                        SELECT 
                            AVG(CASE WHEN sc.participant_count = 1 THEN s.number ELSE 0 END) as avg_solo_streak
                        FROM streaks s
                        JOIN streak_counts sc ON s.id = sc.streak_id
                        JOIN rounds r ON r.streak_id = s.id
                        {map_condition}
                    )
                    SELECT 
                        COUNT(*) as total_guesses,
                        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END),
                        ROUND(AVG(CASE WHEN is_correct THEN 100.0 ELSE 0 END), 1),
                        ROUND((SELECT avg_solo_streak FROM streak_stats), 2)
                    FROM rounds
                    {map_condition}
                """, params * 2).fetchone()

            if not stats or stats[0] == 0:
                await ctx.send("No stats recorded yet!")
                return

            total, correct, accuracy, avg_solo_streak = stats
            title = "Global Stats"
            if map_name:
                title += f" on **{map_name}**"

            embed = discord.Embed(title=title, color=discord.Color.blue())
            embed.description = "\n".join([
                f"**Guesses**: {correct}/{total}",
                f"**Accuracy**: {accuracy}%",
                f"**Average Solo Streak**: {avg_solo_streak:.2f}" if avg_solo_streak > 0 else ""
            ])
            await ctx.send(embed=embed)

        @global_stats.command(name='subdivisions', aliases=['subs', 'subdivision', 's'])
        async def global_subdivision_stats(ctx, *args):
            map_filter, map_name = None, None
            map_args = [a for a in args if a.startswith("map:")]
            if map_args:
                map_input = map_args[0][4:].lower()
                for map_id, names in MAPS.items():
                    real_name = names[0]
                    aliases = [real_name.lower()] + [alias.lower() for alias in names[1:]]
                    if map_input in aliases:
                        map_filter = map_id
                        map_name = real_name
                        break

            with sqlite3.connect(self.game_manager.db_path) as conn:
                params = (map_filter,) if map_filter else ()
                condition = "WHERE map = ?" if map_filter else ""

                hardest = conn.execute(f"""
                    SELECT actual_location, COUNT(*), SUM(CASE WHEN is_correct THEN 1 ELSE 0 END), 
                        ROUND(AVG(CASE WHEN is_correct THEN 100.0 ELSE 0 END), 1)
                    FROM rounds
                    {condition}
                    GROUP BY actual_location
                    HAVING COUNT(*) >= 10
                    ORDER BY 4 ASC
                    LIMIT 10
                """, params).fetchall()

                easiest = conn.execute(f"""
                    SELECT actual_location, COUNT(*), SUM(CASE WHEN is_correct THEN 1 ELSE 0 END), 
                        ROUND(AVG(CASE WHEN is_correct THEN 100.0 ELSE 0 END), 1)
                    FROM rounds
                    {condition}
                    GROUP BY actual_location
                    HAVING COUNT(*) >= 10
                    ORDER BY 4 DESC
                    LIMIT 10
                """, params).fetchall()

                mistakes = conn.execute(f"""
                    SELECT actual_location, guessed_location, COUNT(*) 
                    FROM rounds
                    WHERE NOT is_correct AND guessed_location != '5k guess'
                    {f"AND map = ?" if map_filter else ""}
                    GROUP BY actual_location, guessed_location
                    HAVING COUNT(*) >= 3
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """, params).fetchall()

            title = "Global Subdivision Statistics"
            if map_name:
                title += f" on **{map_name}**"

            embeds = []
            embed = discord.Embed(title=title, color=discord.Color.blue())
            length_so_far = len(title)

            if hardest:
                hard_text = [f"**{loc}** - {correct}/{seen} ({acc}%)" for loc, seen, correct, acc in hardest]
                length_so_far = safe_add_field(embed, "💀 Hardest", hard_text, length_so_far)
                embed, length_so_far = maybe_new_embed(embeds, embed, length_so_far)

            if easiest:
                easy_text = [f"**{loc}** - {correct}/{seen} ({acc}%)" for loc, seen, correct, acc in easiest]
                length_so_far = safe_add_field(embed, "🎯 Easiest", easy_text, length_so_far)
                embed, length_so_far = maybe_new_embed(embeds, embed, length_so_far)

            if mistakes:
                mistake_text = [f"**{actual}** mistaken for **{guess}** ({count} times)" for actual, guess, count in
                                mistakes]
                length_so_far = safe_add_field(embed, "❌ Common Mistakes", mistake_text, length_so_far)
                embed, length_so_far = maybe_new_embed(embeds, embed, length_so_far)

            embeds.append(embed)

            for em in embeds:
                await ctx.send(embed=em)

        @self.command(name='aliases', aliases=['a'])
        @commands.cooldown(1, 0.5, BucketType.user)
        async def aliases(ctx, *, subdivision: Optional[str] = None):
            """Show all aliases for a given subdivision"""
            if not subdivision:
                embed = discord.Embed(
                    description="Please provide a subdivision to look up.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            elif subdivision == "all":
                all_aliases = []
                for sub in self.game_manager.subdivisions.get_all_subdivisions():
                    aliases = self.game_manager.subdivisions.get_all_aliases(sub)
                    all_aliases.append(f"**{sub}**: {', '.join(aliases)}\n")
                if all_aliases:
                    file_content = "\n".join(all_aliases)
                    file_stream = io.BytesIO(file_content.encode('utf-8'))  # 将文本转换为字节流

                    # 发送文件
                    file_stream.seek(0)  # 将文件流指针重置到开头
                    await ctx.send("Here are all the subdivisions and their aliases:",
                                   file=discord.File(file_stream, filename="subdivisions_aliases.txt"))
                    return

            aliases = self.game_manager.subdivisions.get_all_aliases(subdivision)

            if not aliases:
                embed = discord.Embed(
                    description="Invalid subdivision name.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title=aliases[0],
                description=", ".join(aliases[1:]),
                color=discord.Color.blue()
            )

            await ctx.send(embed=embed)

        @self.command(name='participants', aliases=['p'])
        async def participants(ctx):
            """Show all participants in the current streak"""
            with sqlite3.connect(self.game_manager.db_path) as conn:
                participants = conn.execute("""
                    SELECT sp.user_id, sp.guesses_count
                    FROM streak_participants sp
                    JOIN streaks s ON sp.streak_id = s.id
                    WHERE s.channel_id = ? AND s.end_timestamp IS NULL
                    ORDER BY sp.guesses_count DESC
                """, (ctx.channel.id,)).fetchall()

            if not participants:
                await ctx.send("No active streak or no participants.")
                return

            # Format participants as mentions with their guess counts
            mentions = [f"<@{user_id}> ({guesses})" for user_id, guesses in participants]
            participants_list = ", ".join(mentions)

            embed = discord.Embed(
                title="Streak Participants",
                description=participants_list,
                color=discord.Color.light_grey()
            )

            await ctx.send(embed=embed)

        @self.command(name='compass', aliases=['c'])
        @commands.cooldown(1, 1, BucketType.user)
        async def compass(ctx):
            """Show the compass direction for the current round"""
            if ctx.channel.id not in self.game_manager.rounds:
                await ctx.send("No active round!")
                return

            round_obj = self.game_manager.rounds[ctx.channel.id]
            compass_img = Image.open('compass.png')

            rotated_compass = compass_img.rotate(round_obj.heading, expand=False, resample=Image.Resampling.BICUBIC)

            final_size = (100, 100)
            resized_compass = rotated_compass.resize(final_size, Image.Resampling.LANCZOS)

            img_byte_arr = io.BytesIO()
            resized_compass.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            await ctx.send(file=discord.File(img_byte_arr, 'compass.png'))

        @self.command(name='fix')
        @commands.has_any_role(*MOD_ROLE_NAMES)
        async def fix(ctx):
            """Attempt to fix a broken round by reprocessing it or starting a new game if necessary"""
            logging.info("Attempting to fix...")
            # TODO: remains to be seen if this is best
            await self.start_new_game(ctx.channel)

        @self.command(name='leaderboard', aliases=['lb', 'top', 'record', 'records'])
        @commands.cooldown(1, 1, BucketType.user)
        async def leaderboard(ctx, *args):
            args = [a.lower() for a in args]
            show_all = any(a in ["all", "a", "e", "every"] for a in args)
            streak_type = next((a for a in args if a in ["solo", "assisted"]), None)

            map_filter = None
            map_name = None
            map_args = [a for a in args if a.startswith("map:")]
            if map_args:
                map_input = map_args[0][4:]
                for map_id, names in MAPS.items():
                    real_name = names[0]
                    if map_input == real_name.lower() or map_input in [alias.lower() for alias in names[1:]]:
                        map_filter = map_id
                        map_name = real_name
                        break

            with sqlite3.connect(self.game_manager.db_path) as conn:
                if map_filter:
                    base_query = """
                        WITH valid_streaks AS (
                            -- First find all streaks that have at least one round from the specified map
                            SELECT DISTINCT s.id as streak_id
                            FROM streaks s
                            JOIN rounds r ON r.streak_id = s.id
                            WHERE r.map = ?
                        ),
                        streak_counts AS (
                            SELECT 
                                sp.streak_id,
                                COUNT(DISTINCT sp.user_id) as participant_count,
                                GROUP_CONCAT(sp.user_id) as participant_group
                            FROM streak_participants sp
                            JOIN valid_streaks vs ON sp.streak_id = vs.streak_id
                            GROUP BY sp.streak_id
                        )
                    """
                else:
                    base_query = """
                        WITH streak_counts AS (
                            SELECT 
                                streak_id,
                                COUNT(DISTINCT user_id) as participant_count,
                                GROUP_CONCAT(user_id) as participant_group
                            FROM streak_participants
                            GROUP BY streak_id
                        )
                    """

                title_prefix, participant_filter = "", ""
                if streak_type == "solo":
                    participant_filter = "AND sc.participant_count = 1"
                    title_prefix = "Solo "
                elif streak_type == "assisted":
                    participant_filter = "AND sc.participant_count > 1"
                    title_prefix = "Assisted "
                if show_all:
                    title_prefix = "All " + title_prefix
                else:
                    title_prefix = "Best " + title_prefix

                if map_filter:
                    title_prefix = f"{title_prefix}{map_name} "

                if not show_all:
                    query = base_query + f"""
                        SELECT s.number as streak, s.start_timestamp,
                            GROUP_CONCAT(sp.user_id) as users,
                            GROUP_CONCAT(sp.guesses_count) as guesses
                        FROM streaks s
                        JOIN streak_participants sp ON s.id = sp.streak_id
                        JOIN streak_counts sc ON s.id = sc.streak_id
                        WHERE s.number > 0 {participant_filter}
                        AND s.number = (
                            SELECT MAX(s2.number)
                            FROM streaks s2
                            JOIN streak_counts sc2 ON s2.id = sc2.streak_id
                            WHERE sc2.participant_group = sc.participant_group
                        )
                        AND (sc.participant_group, s.number, s.start_timestamp) IN (
                            SELECT sc3.participant_group, s3.number, MAX(s3.start_timestamp)
                            FROM streaks s3
                            JOIN streak_counts sc3 ON s3.id = sc3.streak_id
                            GROUP BY sc3.participant_group, s3.number
                        )
                        GROUP BY s.id
                        ORDER BY s.number DESC, s.start_timestamp DESC
                        LIMIT 5
                    """
                else:
                    query = base_query + f"""
                        SELECT s.number as streak, s.start_timestamp,
                            GROUP_CONCAT(sp.user_id) as users,
                            GROUP_CONCAT(sp.guesses_count) as guesses
                        FROM streaks s
                        JOIN streak_participants sp ON s.id = sp.streak_id
                        JOIN streak_counts sc ON s.id = sc.streak_id
                        WHERE s.number > 0 {participant_filter}
                        GROUP BY s.id
                        ORDER BY s.number DESC, s.start_timestamp DESC
                        LIMIT 5
                    """

                embed_title = f"{title_prefix}Streaks"

                if map_filter:
                    top_streaks = conn.execute(query, (map_filter,)).fetchall()
                else:
                    top_streaks = conn.execute(query).fetchall()

                if not top_streaks:
                    await ctx.send(f"No streaks found.")
                    return

                medals = {
                    "1": ":trophy:",
                    "2": ":second_place:",
                    "3": ":third_place:",
                    "4": ":four:",
                    "5": ":five:",
                }
                description = ""
                for i, record in enumerate(top_streaks, 1):
                    try:
                        streak, timestamp, users, guesses = record
                        timestamp_utc = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').replace(tzinfo=UTC)
                        discord_time = f"<t:{int(timestamp_utc.timestamp())}:d>"

                        if ',' in users:  # Check for multiple users regardless of guesses
                            user_list = users.split(',')
                            mentions = [f"<@{user}>" for user in user_list]
                            if guesses:
                                guess_list = guesses.split(',')
                                mentions = [f"<@{user}> ({guess})" for user, guess in zip(user_list, guess_list)]
                            description += f"{medals[str(i)] if i < 6 else i} {', '.join(mentions)} - **{streak}** streak on {discord_time}\n"
                        else:  # Solo streaks
                            mention = f"<@{users}>"
                            description += f"{medals[str(i)] if i < 6 else i} {mention} - **{streak}** streak on {discord_time}\n"
                    except Exception as e:
                        mention = f"<@{users}>"
                        description += f"{medals[str(i)] if i < 6 else i} {mention} - {streak} streak\n"

                embed = discord.Embed(title=embed_title, color=discord.Color.dark_gold())
                embed.description = description
                await ctx.send(embed=embed)

        @self.command(name='antenna')
        @commands.has_any_role(*MOD_ROLE_NAMES)
        async def antenna(ctx):
            """Shows ONLY the antenna portion of the image (in Gen 3 locations) for the current round."""
            if ctx.channel.id not in self.game_manager.rounds:
                await ctx.send("No active round!")
                return

            round_obj = self.game_manager.rounds[ctx.channel.id]
            if round_obj.pano.img is None:
                return

            # Check if this is Gen 3 (width = 6656)
            if round_obj.pano.dimensions[1] != 6656:
                await ctx.message.add_reaction('❌')
                return

            back_angle = (round_obj.pano.driving_direction + 180) % 360

            back_view = await round_obj.pano.get_panorama(
                heading=back_angle,
                pitch=-30,
                FOV=25
            )
            back_img = Image.fromarray(back_view)

            width, height = back_img.size
            crop_width = int(width * 0.2)
            left_margin = (width - crop_width) // 2
            back_img = back_img.crop((left_margin, 0, left_margin + crop_width, height))

            img_byte_arr = io.BytesIO()
            back_img.save(img_byte_arr, format='JPEG', quality=100)
            img_byte_arr.seek(0)

            await ctx.send(file=discord.File(img_byte_arr, 'antenna.jpg'))

        @self.command(name='car')
        @commands.has_any_role(*MOD_ROLE_NAMES)
        async def car(ctx):
            """Shows ONLY the car portion of the image for the current round."""
            if ctx.channel.id not in self.game_manager.rounds:
                await ctx.send("No active round!")
                return

            round_obj = self.game_manager.rounds[ctx.channel.id]
            if not round_obj.pano:
                return

            embed = discord.Embed(color=discord.Color.orange())

            if (round_obj.pano.pano_id)[0:6] == "BAIDU:":
                car_image_url = (
                    f"https://mapsv0.bdimg.com/?qt=pr3d&fovy=125&quality=100&panoid={(round_obj.pano.pano_id)[6:]}"
                    f"&heading={round_obj.pano.origin_heading}&pitch=-90&width=300&height=720")
            elif (round_obj.pano.pano_id)[0:8] == "TENCENT:":
                back_view = await round_obj.pano.get_panorama(
                    heading=round_obj.pano.driving_direction,
                    pitch=-90,
                    FOV=125
                )
                back_img = Image.fromarray(back_view)

                width, height = back_img.size
                crop_width = int(width * 0.4)
                left_margin = (width - crop_width) // 2
                back_img = back_img.crop((left_margin, 0, left_margin + crop_width, height))

                img_byte_arr = io.BytesIO()
                back_img.save(img_byte_arr, format='JPEG', quality=100)
                img_byte_arr.seek(0)
                await ctx.send(file=discord.File(img_byte_arr, 'car.jpg'))
                return
            else:
                car_image_url = f"https://streetviewpixels-pa.googleapis.com/v1/thumbnail?panoid={round_obj.pano.pano_id}&cb_client=maps_sv.tactile.gps&w=400&h=600&yaw={round_obj.pano.driving_direction}&pitch=90&thumbfov=100"
            embed.set_image(url=car_image_url)
            await ctx.channel.send(embed=embed)

        @self.command(name='copyright', aliases=['cr'])
        async def watermark(ctx):
            """Shows ONLY the copyright portion of the image for the current round."""
            if ctx.channel.id not in self.game_manager.rounds:
                await ctx.send("No active round!")
                return

            round_obj = self.game_manager.rounds[ctx.channel.id]
            if not round_obj.pano:
                return
            # Check if this is Gen 4 (width = 8192)
            if round_obj.pano.dimensions[1] != 8192 or not round_obj.pano.pano_id or len(round_obj.pano.pano_id) != 22:
                await ctx.message.add_reaction('❌')
                return
            embed = discord.Embed(color=discord.Color.blue())
            embed.set_image(
                url=f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=apiv3&panoid={round_obj.pano.pano_id}&output=tile&x=18&y=13&zoom=5&nbt=1&fover=2")
            await ctx.channel.send(embed=embed)

        @self.command(name='5k')
        @commands.cooldown(1, 1, BucketType.user)
        async def five_k_stats(ctx):
            """Show user's 5K statistics"""
            with sqlite3.connect(self.game_manager.db_path) as conn:
                five_ks = conn.execute("""
                    SELECT r.actual_location, COUNT(*) as count
                    FROM rounds r
                    JOIN five_k_guesses f ON r.id = f.round_id
                    WHERE r.user_id = ?
                    GROUP BY r.actual_location
                    ORDER BY count DESC
                """, (ctx.author.id,)).fetchall()

            if not five_ks:
                await ctx.send("You haven't gotten any 5Ks yet!")
                return

            total = sum(count for _, count in five_ks)

            embed = discord.Embed(
                title=f"5Ks for {ctx.author.global_name}",
                description=f"Total: **{total}**",
                color=discord.Color.blue()
            )

            locations = "\n".join(f"**{loc}**: {count}" for loc, count in five_ks)
            embed.add_field(name="Locations", value=locations, inline=False)

            await ctx.send(embed=embed)

        for command in self.commands:
            if not command.has_error_handler():
                command.error(cooldown_error)

        @self.command(name='switchmap', aliases=['s2'])
        @commands.cooldown(1, 3, BucketType.user)
        async def switch_map(ctx, *, map_name: Optional[str] = None):
            """Switch to a different map or show available maps"""
            if not map_name and map_name != 'random':
                # Show list of available maps using the real names (first name in the list)
                globe_maps = {
                    map_id: info
                    for map_id, info in MAPS.items()
                    if len(info) < 3
                }
                non_globe_maps = {
                    map_id: info
                    for map_id, info in MAPS.items()
                    if len(info) > 2
                }
                embed_globe = discord.Embed(
                    title="World Maps List :world_map:",
                    description="\n".join([
                        f":{'globe_with_meridians'}: {info[0]} [({info[1].upper()})]({'https://www.geoguessr.com/maps/' + map_id if map_id not in ['baidu', 'qq'] else 'https://tuxun.fun/maps'})"
                        for map_id, info in globe_maps.items()
                    ]),
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed_globe)

                embed_non_globe = discord.Embed(
                    title="Country Maps List :map:",
                    description="\n".join([
                        f":{'flag_' + info[2] if len(info) > 2 else 'globe_with_meridians'}: {info[0]} [({info[1].upper()})]({'https://www.geoguessr.com/maps/' + map_id if map_id not in ['baidu', 'qq'] else 'https://tuxun.fun/maps'})"
                        for map_id, info in non_globe_maps.items()
                    ]),
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed_non_globe)
                return

            # Check cooldown manually
            bucket = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.channel)
            retry_after = bucket.get_bucket(ctx.message).update_rate_limit()
            if retry_after:
                await ctx.message.add_reaction('⏳')
                return

            map_input = map_name.lower()

            # Find the map_id and real name by checking against all aliases
            target_map_id = None
            target_map_name = None
            if map_input == 'random':
                target_map_id = random.choice(list(MAPS.keys()))
                target_map_name = MAPS[target_map_id][0]
            else:
                for map_id, names in MAPS.items():
                    real_name = names[0]  # First name is the real name
                    if map_input == real_name.lower() or map_input in [alias.lower() for alias in names[1:]]:
                        target_map_id = map_id
                        target_map_name = real_name
                        break

            if not target_map_id:
                embed = discord.Embed(
                    description="Invalid map name. Use `!switchmap` to see available maps and their aliases.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            if ctx.channel.id in self.geoguessr_games:
                round_obj = self.game_manager.rounds[ctx.channel.id]
                embed = self.create_embed(1, ctx, None, None, round_obj, False)

                await ctx.send(embed=embed)
                if target_map_id in WORLD_MAPS:
                    FIVE_K_DISTANCE = 185
                    self.streak_mode = 'country'
                    self.game_manager.reset_subdivisions(RegionFlatmap(REGIONS["world"]))
                else:
                    FIVE_K_DISTANCE = 50
                    self.streak_mode = 'state'
                    for map_id, names in MAPS.items():
                        if target_map_id == map_id:
                            self.game_manager.reset_subdivisions(RegionFlatmap(REGIONS[names[-1]]))
                self.game_manager.end_streak(ctx.channel.id)

                await self.start_new_game(ctx.channel, target_map_id)

                embed = self.create_embed(3, ctx, None, f"Switched to **{target_map_name}**",
                                          color=discord.Color.purple())

                await ctx.send(embed=embed)
            else:
                await ctx.send("No active game in this channel. Use !start to begin one.")

        def safe_add_field(embed, name, content, length_so_far):
            field_texts = []
            field_text = "\n".join(content)

            if len(field_text) <= 1024:
                field_texts.append((name, field_text))
            else:
                # 拆分大字段为多个小段
                for i in range(0, len(content), 5):
                    chunk = "\n".join(content[i:i + 5])
                    field_texts.append((f"{name}" if i == 0 else f"{name} (cont'd)", chunk))

            for field_name, field_val in field_texts:
                embed.add_field(name=field_name, value=field_val, inline=False)
                length_so_far += len(field_val)

            return length_so_far

        def maybe_new_embed(embeds, embed, length_so_far, max_len=6000):
            if length_so_far >= max_len:
                embeds.append(embed)
                return discord.Embed(color=discord.Color.blue()), 0
            return embed, length_so_far


def main():
    bot = GeoGuessrBot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
