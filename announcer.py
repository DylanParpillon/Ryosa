"""
Module d'annonces Discord pour les streams
"""

import asyncio
import aiohttp
from config import (
    TWITCH_CHANNEL, DISCORD_ANNOUNCE_URL, DISCORD_ROLE_ID,
    POLL_INTERVAL_S, ANNOUNCE_MESSAGES
)
from utils import detect_streamer, clean_title


class StreamAnnouncer:
    """Gère la détection du stream et les annonces Discord."""
    
    def __init__(self, bot):
        self.bot = bot
        self._stream_was_live = False
        self._poll_task = None

    async def start(self):
        """Démarre la surveillance du stream."""
        if self._poll_task is None:
            self._poll_task = asyncio.create_task(self._poll_loop())
            print(f"📡 Surveillance du stream activée (toutes les {POLL_INTERVAL_S}s)")

    async def stop(self):
        """Arrête la surveillance du stream."""
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

    async def _poll_loop(self):
        """Boucle de vérification du statut du stream."""
        await asyncio.sleep(5)
        
        while True:
            try:
                await self._check_stream()
            except Exception as e:
                print(f"[POLL] Erreur: {e}")
            await asyncio.sleep(POLL_INTERVAL_S)

    async def _check_stream(self):
        """Vérifie si le stream est live et envoie l'annonce."""
        try:
            streams = await self.bot.fetch_streams(user_logins=[TWITCH_CHANNEL])
        except Exception as e:
            print(f"[POLL] Erreur API: {e}")
            return
        
        is_live = len(streams) > 0
        
        # Nouveau stream
        if is_live and not self._stream_was_live:
            stream = streams[0]
            title = stream.title or "Sans titre"
            category = stream.game_name or "Aucune catégorie"
            
            print(f"[LIVE] 🟢 Stream détecté ! {category} | {title}")
            
            streamer = detect_streamer(title)
            template = ANNOUNCE_MESSAGES.get(streamer, ANNOUNCE_MESSAGES["DEFAULT"])
            message = template.format(title=clean_title(title), category=category)
            
            if DISCORD_ROLE_ID:
                message = f"<@&{DISCORD_ROLE_ID}> {message}"
            
            await self._send_announce(message)
            self._stream_was_live = True
        
        # Stream terminé
        elif not is_live and self._stream_was_live:
            print("[LIVE] 🔴 Stream terminé")
            self._stream_was_live = False

    async def _send_announce(self, text: str):
        """Envoie une annonce Discord."""
        if not DISCORD_ANNOUNCE_URL or not self.bot.http:
            print("[ANNOUNCE] Webhook non configuré")
            return
        try:
            payload = {
                "content": text,
                "allowed_mentions": {"parse": ["roles"]}
            }
            await self.bot.http.post(DISCORD_ANNOUNCE_URL, json=payload)
            print("[ANNOUNCE] ✅ Annonce envoyée !")
        except Exception as e:
            print(f"[ANNOUNCE] ❌ Erreur: {e}")
