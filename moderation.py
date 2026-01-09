"""
Module de modération du chat Twitch
Copyright (c) 2024 Tosachii et LaCabaneVirtuelle
"""

import time
import asyncio
from datetime import datetime, timezone
from collections import defaultdict, deque
from config import (
    DISCORD_WEBHOOK_URL, FLOOD_MAX_MSG, FLOOD_WINDOW_S,
    LINK_REGEX, BANNED_WORDS_REGEX,
    SAFE_MODE, SCAM_REGEX, ACCOUNT_AGE_THRESHOLD_DAYS, WARNING_LEVELS,
    LINK_OBFUSCATION_REGEX
)
from utils import is_link_whitelisted


class Moderator:
    """Gère la modération du chat Twitch."""
    
    def __init__(self, bot):
        self.bot = bot
        # Historique des messages par user pour détecter le flood
        self.historique_flood = defaultdict(lambda: deque())
        # Compteur de warns par user (pour l'escalade)
        self.compteur_warns = defaultdict(int)
        # Cache de la date de création des comptes
        self.cache_date_creation = {}

    async def check_message(self, message) -> bool:
        """
        Vérifie un message pour spam/liens/mots interdits.
        Retourne True si le message est bloqué, False sinon.
        """
        auteur = message.author.name if message.author else "unknown"
        contenu = message.content or ""

        # Ignore les modérateurs et le broadcaster
        if message.author and (message.author.is_mod or message.author.is_broadcaster):
            return False
        
        if await self._verifier_scam(message, auteur, contenu):
            return True

        # Anti-flood
        if await self._verifier_flood(message, auteur, contenu):
            await self._escalader_sanction(message, auteur, "Flood/Spam")
            return True
        
        # Anti-liens
        if await self._verifier_liens(message, auteur, contenu):
            await self._escalader_sanction(message, auteur, "Lien interdit")
            return True
        
        # Mots interdits
        if await self._verifier_mots_bannis(message, auteur, contenu):
            await self._escalader_sanction(message, auteur, "Langage interdit")
            return True
        
        return False

    async def _verifier_scam(self, message, auteur: str, contenu: str) -> bool:
        """Détection heuristique de scam/bot."""
        # Critère 1: Lien (ou lien caché) + Mot clé scam
        a_un_lien = bool(LINK_REGEX.search(contenu))
        a_un_lien_cache = bool(LINK_OBFUSCATION_REGEX.search(contenu))
        a_mot_cle_scam = bool(SCAM_REGEX.search(contenu))

        # Si mot clé "streamboo" ou "remove the space" -> on considère que c'est un lien caché implicite
        if (a_un_lien or a_un_lien_cache) and a_mot_cle_scam:
            await self._appliquer_ban(message, auteur, "SCAM DETECTED (Lien/Obfuscation + Mot clé)")
            return True
        
        # Cas spécial : Mot clé très fort seul (ex: streamboo) -> BAN DIRECT
        if "streamboo" in contenu.lower():
             await self._appliquer_ban(message, auteur, "SCAM DETECTED (Blacklisted Domain)")
             return True
        
        # Critère 2: Lien (ou lien caché) + Compte très récent
        if a_un_lien or a_un_lien_cache:
            est_nouveau_compte = await self._est_compte_recent(auteur)
            if est_nouveau_compte:
                await self._appliquer_ban(message, auteur, f"SCAM DETECTED (Lien + Compte < {ACCOUNT_AGE_THRESHOLD_DAYS}j)")
                return True
            
        return False

    async def _est_compte_recent(self, username: str) -> bool:
        """Vérifie l'âge du compte via API Twitch (avec cache)."""
        maintenant = datetime.now(timezone.utc)
        
        # 1. Check cache
        if username in self.cache_date_creation:
            date_creation = self.cache_date_creation[username]
        else:
            # 2. Fetch API
            try:
                users = await self.bot.fetch_users(names=[username])
                if not users:
                    return False  # Impossible de vérifier, on laisse le bénéfice du doute
                
                user = users[0]
                date_creation = user.created_at  # datetime aware utc
                self.cache_date_creation[username] = date_creation
            except Exception as e:
                print(f"[MOD] Erreur fetch_users({username}): {e}")
                return False

        age_compte = maintenant - date_creation
        return age_compte.days < ACCOUNT_AGE_THRESHOLD_DAYS

    async def _escalader_sanction(self, message, auteur: str, raison: str):
        """Applique l'escalade de sanction (Warn -> Timeout -> Ban)."""
        niveau_actuel = self.compteur_warns[auteur]
        
        # On cap au niveau max configuré
        if niveau_actuel >= len(WARNING_LEVELS):
            config_sanction = WARNING_LEVELS[-1]
        else:
            config_sanction = WARNING_LEVELS[niveau_actuel]
        
        action = config_sanction["action"]
        duree = config_sanction["duration"]
        
        # Incrémenter pour la prochaine fois
        self.compteur_warns[auteur] += 1
        
        if action == "warn":
            await message.channel.send(f"@{auteur} ⚠️ Avertissement ({raison}). Prochaine fois : Timeout.")
            self._log_background(f"⚠️ WARN | @{auteur} | {raison}")
            
        elif action == "timeout":
            if SAFE_MODE:
                await message.channel.send(f"@{auteur} [SAFE_MODE] Simulation Timeout {duree}s ({raison})")
                self._log_background(f"🚫 [SAFE MODE] TIMEOUT {duree}s | @{auteur} | {raison}")
            else:
                try:
                    await message.channel.send(f"/timeout {auteur} {duree} {raison}")
                    await message.channel.send(f"@{auteur} 🔇 Timeout {duree}s ({raison})")
                    self._log_background(f"🔇 TIMEOUT {duree}s | @{auteur} | {raison}")
                except Exception as e:
                    print(f"[MOD] Timeout error: {e}")

        elif action == "ban":
            await self._appliquer_ban(message, auteur, raison)

    async def _appliquer_ban(self, message, auteur: str, raison: str):
        """Applique un ban définitif (ou simule en SAFE_MODE)."""
        if SAFE_MODE:
            await message.channel.send(f"@{auteur} [SAFE_MODE] Simulation BAN ({raison})")
            self._log_background(f"🚨 [SAFE MODE] BAN | @{auteur} | {raison}")
        else:
            await message.channel.send(f"/ban {auteur} {raison}")
            self._log_background(f"🚨 BAN | @{auteur} | {raison}")

    async def _verifier_flood(self, message, auteur: str, contenu: str) -> bool:
        """Vérifie si l'utilisateur flood (trop de messages en peu de temps)."""
        maintenant = time.time()
        historique = self.historique_flood[auteur]
        historique.append(maintenant)
        
        # On retire les messages trop vieux
        while historique and maintenant - historique[0] > FLOOD_WINDOW_S:
            historique.popleft()
        
        # Si trop de messages dans la fenêtre = flood
        if len(historique) > FLOOD_MAX_MSG:
            return True
        return False

    async def _verifier_liens(self, message, auteur: str, contenu: str) -> bool:
        """Vérifie les liens non autorisés."""
        if LINK_REGEX.search(contenu) and not is_link_whitelisted(contenu):
            await self._supprimer_message(message)
            return True
        return False

    async def _verifier_mots_bannis(self, message, auteur: str, contenu: str) -> bool:
        """Vérifie les mots interdits."""
        if BANNED_WORDS_REGEX.search(contenu):
            await self._supprimer_message(message)
            return True
        return False

    async def _supprimer_message(self, message) -> bool:
        """Supprime un message via /delete <id>."""
        msg_id = getattr(message, "id", None)
        
        if not msg_id:
            tags = getattr(message, "tags", {})
            msg_id = tags.get("id") if isinstance(tags, dict) else None
        
        if msg_id:
            await message.channel.send(f"/delete {msg_id}")
            return True
        return False

    def _log_background(self, texte: str):
        """Lance le log en arrière-plan pour ne pas bloquer."""
        asyncio.create_task(self._log(texte))

    async def _log(self, texte: str):
        """Envoie un log dans le webhook Discord."""
        if not DISCORD_WEBHOOK_URL:
            return
        
        session = getattr(self.bot, "http_session", None)
        if not session:
            return

        try:
            async with session.post(DISCORD_WEBHOOK_URL, json={"content": texte}, timeout=5) as resp:
                if not (200 <= resp.status < 300):
                    err_text = await resp.text()
                    print(f"[LOG] Erreur Discord {resp.status}: {err_text}")
        except Exception as e:
            print(f"[LOG] Erreur: {e}")
