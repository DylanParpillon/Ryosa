import discord
import logging
import os
from dotenv import load_dotenv

load_dotenv()
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

class Ryosa(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith('!hello'):
            await message.channel.send(f'Hello {message.author}!')
        print(f'Message from {message.author}: {message.content}')
        if message.content.lower().startswith('!memberslist'):
            for member in message.guild.members:
                print(f'Member: {member.name}, ID: {member.id}, Status: {member.status}')
                await message.channel.send(f'Member: {member.name}, ID: {member.id}, Status: {member.status}\n')

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
ryosa = Ryosa(intents=intents)


ryosa.run(token=os.getenv("TOKEN_RYOSA"), log_handler=handler)


