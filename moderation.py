"""
Module de modération du chat Twitch
"""

import time
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from config import (
    DISCORD_WEBHOOK_URL, FLOOD_MAX_MSG, FLOOD_WINDOW_S,
    DISCORD_WEBHOOK_URL, FLOOD_MAX_MSG, FLOOD_WINDOW_S,
    LINK_REGEX, BANNED_WORDS_REGEX,
    SAFE_MODE, SCAM_REGEX, ACCOUNT_AGE_THRESHOLD_DAYS, WARNING_LEVELS,
    LINK_OBFUSCATION_REGEX
)
from utils import is_link_whitelisted


# Stockage anti-flood par utilisateur
user_msgs = defaultdict(lambda: deque())

# Stockage Warnings : user -> count
user_warnings = defaultdict(int)

# Cache âge compte : user -> timestamp création
user_created_cache = {}


class Moderator:
    """Gère la modération du chat Twitch."""
    
    def __init__(self, bot):
        self.bot = bot

    async def check_message(self, message) -> bool:
        """
        Vérifie un message pour spam/liens/mots interdits.
        Retourne True si le message est bloqué, False sinon.
        """
        author = message.author.name if message.author else "unknown"
        content = message.content or ""

        # Ignore les modérateurs et le broadcaster
        if message.author and (message.author.is_mod or message.author.is_broadcaster):
            return False
        
        if await self._check_scam(message, author, content):
            return True

        # Anti-flood
        if await self._check_flood(message, author, content):
            await self._escalate_user(message, author, "Flood/Spam")
            return True
        
        # Anti-liens
        if await self._check_links(message, author, content):
            # Le _check_links supprime déjà, on ajoute une escalade
            await self._escalate_user(message, author, "Lien interdit")
            return True
        
        # Mots interdits
        if await self._check_banned_words(message, author, content):
            await self._escalate_user(message, author, "Langage interdit")
            return True
        
        return False

    async def _check_scam(self, message, author: str, content: str) -> bool:
        """Détection heuristique de scam/bot."""
        # Critère 1: Lien (ou lien caché) + Mot clé scam
        has_link = bool(LINK_REGEX.search(content))
        has_obfuscated_link = bool(LINK_OBFUSCATION_REGEX.search(content))
        has_scam_keyword = bool(SCAM_REGEX.search(content))

        # Si mot clé "streamboo" ou "remove the space" -> on considère que c'est un lien caché implicite
        # Ou si lien détecté + mot clé
        if (has_link or has_obfuscated_link) and has_scam_keyword:
            await self._apply_ban(message, author, "SCAM DETECTED (Lien/Obfuscation + Mot clé)")
            return True
        
        # Cas spécial : Mot clé très fort seul (ex: streamboo) -> BAN DIRECT
        if "streamboo" in content.lower():
             await self._apply_ban(message, author, "SCAM DETECTED (Blacklisted Domain)")
             return True
        
        # Critère 2: Lien (ou lien caché) + Compte très récent
        if has_link or has_obfuscated_link:
            is_new_account = await self._is_account_recent(author)
            if is_new_account:
                await self._apply_ban(message, author, f"SCAM DETECTED (Lien + Compte < {ACCOUNT_AGE_THRESHOLD_DAYS}j)")
                return True
            
        return False

    async def _is_account_recent(self, username: str) -> bool:
        """Vérifie l'âge du compte via API Twitch (avec cache)."""
        now = datetime.now(timezone.utc)
        
        # 1. Check cache
        if username in user_created_cache:
            created_at = user_created_cache[username]
        else:
            # 2. Fetch API
            try:
                users = await self.bot.fetch_users(names=[username])
                if not users:
                    return False # Impossible de vérifier, on laisse le bénéfice du doute
                
                user = users[0]
                created_at = user.created_at # datetime aware utc
                user_created_cache[username] = created_at
            except Exception as e:
                print(f"[MOD] Erreur fetch_users({username}): {e}")
                return False

        age = now - created_at
        return age.days < ACCOUNT_AGE_THRESHOLD_DAYS

    async def _escalate_user(self, message, author: str, reason: str):
        """Applique l'escalade de sanction (Warn -> Timeout -> Ban)."""
        current_level = user_warnings[author]
        
        # On cap au niveau max configuré
        if current_level >= len(WARNING_LEVELS):
            config = WARNING_LEVELS[-1]
        else:
            config = WARNING_LEVELS[current_level]
        
        action = config["action"]
        duration = config["duration"]
        
        # Incrémenter pour la prochaine fois
        user_warnings[author] += 1
        
        if action == "warn":
            await message.channel.send(f"@{author} ⚠️ Avertissement ({reason}). Prochaine fois : Timeout.")
            await self._log(f"⚠️ WARN | @{author} | {reason}")
            
        elif action == "timeout":
            if SAFE_MODE:
                await message.channel.send(f"@{author} [SAFE_MODE] Simulation Timeout {duration}s ({reason})")
                await self._log(f"🚫 [SAFE MODE] TIMEOUT {duration}s | @{author} | {reason}")
            else:
                try:
                    # TwitchIO v2.10: ctx.timeout ou utiliser channel.timeout ?
                    # message.channel est un Channel object.
                    # Pour timeout il faut souvent passer par self.bot.user.timeout ou via API
                    # Mais TwitchIO v2 a une méthode helper sur le user ou channel si on a les droits
                    # Le plus simple en message context : /timeout
                    await message.channel.send(f"/timeout {author} {duration} {reason}")
                    await message.channel.send(f"@{author} 🔇 Timeout {duration}s ({reason})")
                    await self._log(f"🔇 TIMEOUT {duration}s | @{author} | {reason}")
                except Exception as e:
                    print(f"[MOD] Timeout error: {e}")

        elif action == "ban":
            await self._apply_ban(message, author, reason)

    async def _apply_ban(self, message, author: str, reason: str):
        """Applique un ban définitif (ou simule)."""
        if SAFE_MODE:
            await message.channel.send(f"@{author} [SAFE_MODE] Simulation BAN ({reason})")
            await self._log(f"🚨 [SAFE MODE] BAN | @{author} | {reason}")
        else:
            await message.channel.send(f"/ban {author} {reason}")
            await self._log(f"🚨 BAN | @{author} | {reason}")

    async def _check_flood(self, message, author: str, content: str) -> bool:
        """Vérifie le flood."""
        now = time.time()
        dq = user_msgs[author]
        dq.append(now)
        
        while dq and now - dq[0] > FLOOD_WINDOW_S:
            dq.popleft()
        
        if len(dq) > FLOOD_MAX_MSG:
            # Le message à l'utilisateur est géré par _escalate_user désormais
            return True
        return False

    async def _check_links(self, message, author: str, content: str) -> bool:
        """Vérifie les liens non autorisés."""
        if LINK_REGEX.search(content) and not is_link_whitelisted(content):
            await self._delete_message(message)
            return True
        return False

    async def _check_banned_words(self, message, author: str, content: str) -> bool:
        """Vérifie les mots interdits."""
        if BANNED_WORDS_REGEX.search(content):
            await self._delete_message(message)
            return True
        return False

    async def _delete_message(self, message) -> bool:
        """Supprime un message via /delete <id>."""
        msg_id = getattr(message, "id", None)
        
        if not msg_id:
            tags = getattr(message, "tags", {})
            msg_id = tags.get("id") if isinstance(tags, dict) else None
        
        if msg_id:
            await message.channel.send(f"/delete {msg_id}")
            return True
        return False

    async def _log(self, text: str):
        """Envoie un log dans le webhook Discord."""
        if not DISCORD_WEBHOOK_URL or not self.bot.http:
            return
        try:
            await self.bot.http.post(DISCORD_WEBHOOK_URL, json={"content": text})
        except Exception as e:
            print(f"[LOG] Erreur: {e}")
