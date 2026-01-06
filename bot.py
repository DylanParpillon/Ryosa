"""
RyosaChii Bot - Bot Twitch de modération + annonces Discord + Dashboard
TwitchIO v2.10.0 | Python 3.13

Structure:
  - config.py      : Configuration
  - utils.py       : Fonctions utilitaires
  - announcer.py   : Annonces Discord
  - moderation.py  : Modération du chat
  - dashboard.py   : 🌍 Interface web de gestion (NOUVEAU)
  - bot.py         : Point d'entrée principal
"""

import aiohttp
from twitchio.ext import commands

from config import TWITCH_TOKEN, TWITCH_CHANNEL, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_BOT_ID
from announcer import StreamAnnouncer
from moderation import Moderator
from dashboard import Dashboard


class Bot(commands.Bot):
    """Bot principal RyosaChii."""
    
    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            prefix="!",
            initial_channels=[TWITCH_CHANNEL],
        )
        self.http: aiohttp.ClientSession | None = None
        self.announcer = StreamAnnouncer(self)
        self.moderator = Moderator(self)
        self.dashboard = Dashboard(self)  # Nouveau module Dashboard

    # ─────────────────────────── LIFECYCLE ───────────────────────────

    async def event_ready(self):
        """Appelé quand le bot est connecté."""
        print(f"✅ Connecté en tant que {self.nick} | sur #{TWITCH_CHANNEL}")
        
        if self.http is None:
            self.http = aiohttp.ClientSession()
        
        await self.announcer.start()
        await self.dashboard.start()  # Démarrage du site web

    async def close(self):
        """Fermeture propre du bot."""
        await self.announcer.stop()
        await self.dashboard.stop()
        if self.http:
            await self.http.close()
        await super().close()

    # ─────────────────────────── EVENTS ───────────────────────────

    async def event_message(self, message):
        """Gère chaque message du chat."""
        if message.echo:
            return
        
        # 1. Modération
        if await self.moderator.check_message(message):
            return
        
        # 2. Commandes Personnalisées (Dashboard)
        # On vérifie si le message correspond à une commande enregistrée
        response = self.dashboard.cmd_manager.get_response(message.content)
        if response:
            await message.channel.send(response)
            return
        
        # 3. Commandes Hardcodées (!ping, etc.)
        await self.handle_commands(message)

    # ─────────────────────────── COMMANDES ───────────────────────────

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Commande !ping pour tester le bot."""
        await ctx.send("pong")


# ══════════════════════════════════════════════════════════════════════════════
#                                   LANCEMENT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    Bot().run()
