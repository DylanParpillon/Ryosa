"""
RyosaChii Bot - Bot Twitch de modération + annonces Discord
Copyright (c) 2024 Tosachii et LaCabaneVirtuelle

TwitchIO v2.10.0 | Python 3.13

Structure:
  - config.py      : Configuration (variables, regex, messages)
  - utils.py       : Fonctions utilitaires
  - announcer.py   : Annonces Discord des streams
  - chat_alerts.py : Messages automatiques dans le chat
  - moderation.py  : Modération du chat
  - bot.py         : Point d'entrée principal
"""

import aiohttp
from twitchio.ext import commands

import json
import os
import time
import asyncio
from typing import Optional, Dict, Any

from config import (
    TWITCH_TOKEN, TWITCH_CHANNEL,
    TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_REFRESH_TOKEN, TOKEN_STORE_FILE
)
from announcer import StreamAnnouncer
from moderation import Moderator
from chat_alerts import ChatAlerter


class TokenManager:
    """Gère l'authentification et le refresh token Twitch."""
    
    def __init__(self):
        self.access_token = TWITCH_TOKEN.replace("oauth:", "")
        self.refresh_token = TWITCH_REFRESH_TOKEN
        self.client_id = TWITCH_CLIENT_ID
        self.client_secret = TWITCH_CLIENT_SECRET
        
        # Charger depuis le fichier si existant (priorité sur .env pour le refresh token à jour)
        self._load_from_store()

    def _load_from_store(self):
        if os.path.exists(TOKEN_STORE_FILE):
            try:
                with open(TOKEN_STORE_FILE, "r") as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token", self.access_token)
                    self.refresh_token = data.get("refresh_token", self.refresh_token)
                    print("🔑 Tokens chargés depuis le stockage local.")
            except Exception as e:
                print(f"⚠️ Erreur chargement tokens: {e}")

    def _save_to_store(self):
        try:
            with open(TOKEN_STORE_FILE, "w") as f:
                json.dump({
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token
                }, f)
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde tokens: {e}")

    async def refresh(self, session: aiohttp.ClientSession) -> bool:
        """Tente de rafraîchir le token."""
        print("🔄 Refresh du token Twitch...")
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            async with session.post(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.access_token = data["access_token"]
                    self.refresh_token = data.get("refresh_token", self.refresh_token) # Optionnel parfois
                    self._save_to_store()
                    print("✅ Token rafraîchi avec succès !")
                    return True
                else:
                    text = await resp.text()
                    print(f"❌ Erreur refresh token ({resp.status}): {text}")
                    return False
        except Exception as e:
            print(f"❌ Exception refresh token: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        return {
            "Client-Id": self.client_id,
            "Authorization": f"Bearer {self.access_token}"
        }


class Bot(commands.Bot):
    """Bot principal RyosaChii."""
    
    def __init__(self):
        super().__init__(
            token=TWITCH_TOKEN,
            prefix="!",
            initial_channels=[TWITCH_CHANNEL],
        )
        self.http_session: aiohttp.ClientSession | None = None
        self.tokens = TokenManager()
        self.announcer = StreamAnnouncer(self)
        self.moderator = Moderator(self)
        self.alerter = ChatAlerter(self)
        self.broadcaster_id: str | None = None

    # ─────────────────────────── LIFECYCLE ───────────────────────────

    async def event_ready(self):
        """Appelé quand le bot est connecté."""
        print(f"✅ Connecté en tant que {self.nick} | sur #{TWITCH_CHANNEL}")
        
        if self.http_session is None:
            # Timeout global de 10s pour éviter de bloquer sur des webhooks lents
            timeout = aiohttp.ClientTimeout(total=10)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            # On injecte la session dans le bot.http pour compatibilité si besoin, 
            # mais TwitchIO gère son propre http interne pour command handling.
            # Ici on utilise self.http_session pour nos appels API custom.
        
        # Récupérer l'ID du broadcaster (nécessaire pour les clips)
        if not self.broadcaster_id:
            try:
                users = await self.fetch_users(names=[TWITCH_CHANNEL])
                if users:
                    self.broadcaster_id = str(users[0].id)
                    print(f"🆔 Broadcaster ID: {self.broadcaster_id}")
            except Exception as e:
                print(f"⚠️ Impossible de récupérer broadcaster_id: {e}")

        # Correction: On N'ecrase PLUS self.http.
        # TwitchIO utilise self.http pour ses propres trucs interne.
        # On utilise self.http_session pour NOS webhooks.
        
        await self.announcer.start()
        await self.alerter.start()
        await self.moderator._log("🟢 **RyosaChii Démarrée** | Prête à modérer !")

    async def close(self):
        """Fermeture propre du bot."""
        print("🔴 Arrêt du bot...")
        if self.moderator:
            await self.moderator._log("🔴 **RyosaChii Arrêtée**")
        
        # D'abord on coupe les services annexes
        await self.announcer.stop()
        await self.alerter.stop()
        
        # Ensuite on ferme la session
        if self.http_session:
            await self.http_session.close()
        
        # Enfin on ferme le bot (qui nettoie aussi ses trucs)
        await super().close()

    # ─────────────────────────── EVENTS ───────────────────────────

    async def event_message(self, message):
        """Gère chaque message du chat."""
        if message.echo:
            return
        
        # Compteur pour alertes auto
        self.alerter.on_message()

        # Modération (si bloqué, on arrête)
        if await self.moderator.check_message(message):
            return
        
        await self.handle_commands(message)

    # ─────────────────────────── COMMANDES ───────────────────────────

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Commande !ping pour tester le bot."""
        await ctx.send("pong")

    # ─────────────────────────── HELIX API ───────────────────────────

    async def _helix_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Wrapper pour appels Helix avec retry sur 401."""
        url = f"https://api.twitch.tv/helix/{endpoint}"
        
        for attempt in range(2):
            headers = self.tokens.get_headers()
            # Fusion avec headers existants si fournis
            if "headers" in kwargs:
                headers.update(kwargs["headers"])
                del kwargs["headers"]
            
            async with self.http_session.request(method, url, headers=headers, **kwargs) as resp:
                if resp.status == 401 and attempt == 0:
                    print("⚠️ 401 lors de l'appel API -> Refresh Token")
                    if await self.tokens.refresh(self.http_session):
                        continue # Retry
                    else:
                        raise Exception("Echec refresh token")
                
                if resp.status not in (200, 201, 202):
                    text = await resp.text()
                    raise Exception(f"API Error {resp.status}: {text}")
                
                return await resp.json()

    # ─────────────────────────── CLIPS ───────────────────────────

    @commands.command()
    @commands.cooldown(1, 60, commands.Bucket.channel)
    async def clip(self, ctx: commands.Context):
        """Crée un clip du stream actuel."""
        # Vérif permissions (Mod ou Broadcaster)
        if not ctx.author.is_mod and not ctx.author.is_broadcaster:
            return

        if not self.broadcaster_id:
            await ctx.send("❌ Erreur interne: Broadcaster ID inconnu.")
            return

        try:
            # 1. Demande de création
            # has_delay=true ajoute un délai pour capturer ce qu'on vient de voir
            data = await self._helix_request("POST", "clips", params={
                "broadcaster_id": self.broadcaster_id,
                "has_delay": "true"
            })
            
            # API retourne une liste avec une entrée "id" et "edit_url"
            clip_id = data["data"][0]["id"]
            edit_url = data["data"][0]["edit_url"]
            
            # L'URL "edit_url" permet d'accéder, mais pour les viewers on veut l'URL publique.
            # Souvent l'ID suffit: https://clips.twitch.tv/{id}
            # Mais le clip n'est pas dispo instantanément pour visionnage.
            
            print(f"🎬 Clip créé: {clip_id}. Attente disponibilité...")
            
            # 2. Polling pour vérifier la dispo
            clip_url = f"https://clips.twitch.tv/{clip_id}"
            found_url = None
            
            for _ in range(10): # 10 essais de 2s = 20s max
                await asyncio.sleep(2)
                try:
                    cdata = await self._helix_request("GET", "clips", params={"id": clip_id})
                    if cdata and cdata["data"]:
                        # Le clip est indexé
                        info = cdata["data"][0]
                        found_url = info.get("url") # URL publique
                        break
                except Exception:
                    pass
            
            final_url = found_url or clip_url
            await ctx.send(f"🎬 @{ctx.author.name} vient de créer le clip ! {final_url}")
            await self.moderator._log(f"🎬 CLIP | Créé par @{ctx.author.name} | {final_url}")

        except Exception as e:
            err_msg = str(e)
            if "broadcaster is not live" in err_msg.lower():
                await ctx.send("❌ Impossible de clipper : Le stream ne semble pas en ligne.")
                await self.moderator._log(f"⚠️ CLIP FAILED | @{ctx.author.name} | Stream offline")
            elif "scopts" in err_msg.lower() or "permission" in err_msg.lower():
                await ctx.send("❌ Erreur permissions (scope manquant pour clips).")
                await self.moderator._log(f"⚠️ CLIP ERROR | @{ctx.author.name} | Permissions/Scope missing: {e}")
            else:
                print(f"❌ Erreur Clip: {e}")
                # On évite de spammer le chat avec l'erreur technique précise
                await ctx.send("❌ Erreur lors de la création du clip.") 
                await self.moderator._log(f"❌ CLIP ERROR | @{ctx.author.name} | {err_msg}")


# ══════════════════════════════════════════════════════════════════════════════
#                                   LANCEMENT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    Bot().run()
