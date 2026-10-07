import discord
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
client = discord.Client(intents=discord.Intents.all())

client.run(token=os.getenv("TOKEN_RYOSA"))

@client.event
async def on_ready():
    print(f'{client.user} est connecté à Discord!')

@client.event
async def on_message(self, message):
        if message.author == self.user:
            return  

        if message.content.startswith('!hello'):
            await message.channel.send('Hello!')

client.run(token=os.getenv("TOKEN_RYOSA"))


