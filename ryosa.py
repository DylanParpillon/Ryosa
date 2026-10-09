import discord
import os
from dotenv import load_dotenv

load_dotenv()

class Ryosa(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith('!hello'):
            await message.channel.send(f'Hello {message.author}!')
        print(f'Message from {message.author}: {message.content}')


intents = discord.Intents.default()

intents.message_content = True
intents.members = True
ryosa = Ryosa(intents=intents)

ryosa.run(token=os.getenv("TOKEN_RYOSA"))


