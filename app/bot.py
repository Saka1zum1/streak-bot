import discord
from app.config import STREAK_CHANNELS
from app.commands.streak import StreakGame   # 引入 streak 游戏逻辑

intents = discord.Intents.all()
intents.messages = True
intents.members = True
client = discord.Client(intents=intents)
Game = StreakGame()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.id in STREAK_CHANNELS:
        if client.user.mentioned_in(message):
            if any(word in message.content.lower() for word in ["hello", "hi"]):
                await message.channel.send(f"Hi 😁 <@{message.author.id}> Wanna try a streak game?")
        elif any(symbol in message.content for symbol in [";", "!", "/"]):
            await Game.handle_message(message)  # 调用 streak 处理逻辑
