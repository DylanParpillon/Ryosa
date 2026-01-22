"""
Client Discord pour RyosaChii.
Gère les interactions chat et l'hébergement du bot Discord.
"""
import discord
import asyncio
from config import DISCORD_ROLE_ID

class RyosaDiscordBot(discord.Client):
    def __init__(self):
        # Les "intents" sont les permissions d'événements
        intents = discord.Intents.default()
        intents.message_content = True  # Nécessaire pour lire les messages
        intents.members = True          # Nécessaire pour voir les membres
        
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"✅ [DISCORD] Connecté en tant que {self.user} (ID: {self.user.id})")
        print(f"   📊 Connecté à {len(self.guilds)} serveur(s)")

    async def on_message(self, message):
        # Ne pas répondre à soi-même
        if message.author == self.user:
            return

        # Simple réponse "coucou" si on mentionne Ryosa
        content = message.content.lower()
        if "ryosa" in content and ("coucou" in content or "salut" in content or "hello" in content):
            await message.channel.send(f"Coucou {message.author.mention} ! Ravie de te voir 🌸")
        
        # Commande !ping spécifique Discord
        if message.content == "!ping":
            await message.channel.send(f"Pong ! 🏓 ({round(self.latency * 1000)}ms)")

    # Tu pourras ajouter plein d'autres événements ici !
