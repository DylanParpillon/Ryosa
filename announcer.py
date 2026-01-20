"""
Module d'annonces Discord pour les streams
Copyright (c) 2024 Tosachii et LaCabaneVirtuelle
"""

import asyncio
import time
from config import (
    TWITCH_CHANNEL, DISCORD_ANNOUNCE_URL, DISCORD_ROLE_ID,
    POLL_INTERVAL_S, ANNOUNCE_MESSAGES
)
from utils import detect_streamer, clean_title


class StreamAnnouncer:
    """Gère la détection du stream et les annonces Discord."""
    
    def __init__(self, bot):
        self.bot = bot
        self._etait_en_live = False
        self._tache_surveillance = None

    async def start(self):
        """Démarre la surveillance du stream."""
        if self._tache_surveillance is None:
            self._tache_surveillance = asyncio.create_task(self._boucle_surveillance())
            print(f"📡 Surveillance du stream activée (toutes les {POLL_INTERVAL_S}s)")

    async def stop(self):
        """Arrête la surveillance du stream."""
        if self._tache_surveillance:
            self._tache_surveillance.cancel()
            try:
                await self._tache_surveillance
            except asyncio.CancelledError:
                pass

    async def _boucle_surveillance(self):
        """Boucle de vérification du statut du stream."""
        # Petit délai au démarrage
        await asyncio.sleep(5)
        
        while True:
            try:
                await self._verifier_stream()
            except Exception as e:
                print(f"[POLL] Erreur: {e}")
            await asyncio.sleep(POLL_INTERVAL_S)

    async def _verifier_stream(self):
        """Vérifie si le stream est live et envoie l'annonce avec image."""
        try:
            streams = await self.bot.fetch_streams(user_logins=[TWITCH_CHANNEL])
        except Exception as e:
            print(f"[POLL] Erreur API: {e}")
            return
        
        est_en_live = len(streams) > 0
        
        # Nouveau stream détecté
        if est_en_live and not self._etait_en_live:
            stream = streams[0]
            titre = stream.title or "Sans titre"
            categorie = stream.game_name or "Aucune catégorie"
            
            # On récupère l'image du stream (1280x720)
            # On ajoute "?t=" avec le temps actuel pour forcer Discord à recharger l'image (cache-buster)
            try:
                # TwitchIO v2.x utilise parfois .thumbnail_url ou .thumbnail
                url_template = getattr(stream, "thumbnail_url", getattr(stream, "thumbnail", None))
                
                if url_template:
                    image_url = url_template.format(width=1280, height=720)
                    image_url += f"?t={int(time.time())}"
                else:
                    print(f"[DEBUG] Image introuvable. Attributs: {dir(stream)}")
                    image_url = "https://static-cdn.jtvnw.net/ttv-static/404_preview-1280x720.jpg"
            except Exception as e:
                print(f"[POLL] Erreur formatage image: {e}")
                image_url = "https://static-cdn.jtvnw.net/ttv-static/404_preview-1280x720.jpg"
            
            print(f"[LIVE] 🟢 Stream détecté ! {categorie} | {titre}")
            
            streamer = detect_streamer(titre)
            template = ANNOUNCE_MESSAGES.get(streamer, ANNOUNCE_MESSAGES["DEFAULT"])
            texte_annonce = template.format(title=clean_title(titre), category=categorie)
            
            # Mention du rôle + Petit message
            role_ping = f"<@&{DISCORD_ROLE_ID}>" if DISCORD_ROLE_ID else "@everyone"
            mention = f"Coucou {role_ping} ! Tosachii est en stream !!"
            
            # On prépare l'Embed (le joli encadré)
            embed = {
                "title": f"🔴 LIVE : {titre}",
                "description": texte_annonce,
                "color": 0x9146FF,  # Violet Twitch
                "image": {"url": image_url},
                "fields": [
                    {"name": "Catégorie", "value": categorie, "inline": True},
                    {"name": "Lien", "value": f"[Regarder sur Twitch](https://twitch.tv/{TWITCH_CHANNEL})", "inline": True}
                ],
                "footer": {"text": "RyosaChii Bot • Annonce Automatique"}
            }
            
            await self._envoyer_annonce_riche(mention, embed)
            self._etait_en_live = True
        
        # Stream terminé
        elif not est_en_live and self._etait_en_live:
            print("[LIVE] 🔴 Stream terminé")
            self._etait_en_live = False

    async def _envoyer_annonce_riche(self, mention: str, embed: dict):
        """Envoie une annonce Discord avec un Embed et une image."""
        if not DISCORD_ANNOUNCE_URL:
            print("[ANNOUNCE] Webhook non configuré")
            return
            
        session = getattr(self.bot, "http_session", None)
        if not session:
            print("[ANNOUNCE] Pas de session HTTP")
            return

        try:
            payload = {
                "content": mention,
                "embeds": [embed],
                "allowed_mentions": {"parse": ["roles"]}
            }
            async with session.post(DISCORD_ANNOUNCE_URL, json=payload, timeout=5) as resp:
                if 200 <= resp.status < 300:
                    print("[ANNOUNCE] ✅ Annonce avec image envoyée !")
                else:
                    err_text = await resp.text()
                    print(f"[ANNOUNCE] ❌ Erreur Discord {resp.status}: {err_text}")
        except Exception as e:
            print(f"[ANNOUNCE] ❌ Erreur: {e}")
