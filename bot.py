"""
RyosaChii Bot - Bot Twitch de modération + annonces Discord
TwitchIO v2.10.0 | Python 3.13

Structure:
  - config.py      : Configuration (variables, regex, messages)
  - utils.py       : Fonctions utilitaires
  - announcer.py   : Annonces Discord des streams
  - moderation.py  : Modération du chat
  - bot.py         : Point d'entrée principal
"""

import aiohttp
from twitchio.ext import commands

from config import TWITCH_TOKEN, TWITCH_CHANNEL
from announcer import StreamAnnouncer
from moderation import Moderator


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

    # ─────────────────────────── LIFECYCLE ───────────────────────────

    async def event_ready(self):
        """Appelé quand le bot est connecté."""
        print(f"✅ Connecté en tant que {self.nick} | sur #{TWITCH_CHANNEL}")
        
        if self.http is None:
            self.http = aiohttp.ClientSession()
        
        await self.announcer.start()

    async def close(self):
        """Fermeture propre du bot."""
        await self.announcer.stop()
        if self.http:
            await self.http.close()
        await super().close()

    # ─────────────────────────── EVENTS ───────────────────────────

    async def event_message(self, message):
        """Gère chaque message du chat."""
        if message.echo:
            return
        
        # Modération (si bloqué, on arrête)
        if await self.moderator.check_message(message):
            return
        
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
