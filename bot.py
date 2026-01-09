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

from config import TWITCH_TOKEN, TWITCH_CHANNEL, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_BOT_ID, TWITCH_NICK
from announcer import StreamAnnouncer
from moderation import Moderator
from dashboard import Dashboard
from chat_alerts import ChatAlerter


class Bot(commands.Bot):
    """Bot principal RyosaChii."""
    
    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            client_id=TWITCH_CLIENT_ID,
            client_secret=TWITCH_CLIENT_SECRET,
            bot_id=TWITCH_BOT_ID,
            prefix="!",
            initial_channels=[TWITCH_CHANNEL],
        )
        self.http_session: aiohttp.ClientSession | None = None
        self.announcer = StreamAnnouncer(self)
        self.moderator = Moderator(self)
        self.dashboard = Dashboard(self)  # Nouveau module Dashboard
        self.chat_alerter = ChatAlerter(self)  # Alertes auto chat

    # ─────────────────────────── LIFECYCLE ───────────────────────────

    async def event_ready(self):
        """Appelé quand le bot est connecté."""
        print(f"✅ Connecté en tant que {TWITCH_NICK} | sur #{TWITCH_CHANNEL}")
        
        if self.http_session is None:
            self.http_session = aiohttp.ClientSession()
        
        await self.announcer.start()
        await self.dashboard.start()  # Démarrage du site web
        await self.chat_alerter.start()  # Démarrage alertes chat
        self.moderator._log_background(f"✅ **Bot RyosaChii démarré** sur #{TWITCH_CHANNEL}")

    async def close(self):
        """Fermeture propre du bot."""
        await self.announcer.stop()
        await self.dashboard.stop()
        await self.chat_alerter.stop()
        if self.http_session:
            # On utilise await pour être sûr que le log part avant la fermeture
            await self.moderator._log("🛑 **Bot RyosaChii arrêté.**")
            await self.http_session.close()
        await super().close()

    # ─────────────────────────── EVENTS ───────────────────────────

    async def event_message(self, message):
        """Gère chaque message du chat."""
        if message.echo:
            return
        
        # Compteur pour alertes auto
        self.chat_alerter.compter_message()
        
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
        if message.content.startswith("!"):
            print(f"[CMD] {message.author.name}: {message.content}")
        
        await self.handle_commands(message)

    # ─────────────────────────── COMMANDES ───────────────────────────

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Commande !ping pour tester le bot."""
        await ctx.send("pong")

    @commands.command(name="clip")
    async def clip_command(self, ctx: commands.Context):
        """Commande !clip pour créer un clip."""
        print(f"[CLIP] Création demandée par {ctx.author.name}")
        try:
            # 1. Récupérer le broadcaster
            users = await self.fetch_users(names=[TWITCH_CHANNEL])
            if not users:
                await ctx.send("❌ Erreur : Diffuseur introuvable.")
                return
            
            broadcaster = users[0]
            
            # 2. Créer le clip
            # On laisse TwitchIO gérer le token (Access Token auto-refresh)
            clip = await broadcaster.create_clip()
            
            # 3. Réponse Chat
            clip_url = f"https://clips.twitch.tv/{clip.id}"
            await ctx.send(f"🎬 Clip créé par @{ctx.author.name} ! lien : {clip_url}")
            
            # 4. Log Discord
            self.moderator._log_background(f"🎬 CLIP | Créé par @{ctx.author.name} | {clip_url}")

        except Exception as e:
            # Gestion d'erreur (ex: Stream offline)
            err_msg = str(e)
            if "offline" in err_msg.lower():
                await ctx.send("❌ Impossible de créer un clip : Le stream est hors ligne.")
            else:
                await ctx.send(f"❌ Erreur lors de la création du clip.")
                print(f"[CLIP] Erreur : {e}")
            
            self.moderator._log_background(f"❌ CLIP ERROR | @{ctx.author.name} | {e}")


# ══════════════════════════════════════════════════════════════════════════════
#                                   LANCEMENT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    Bot().run()
