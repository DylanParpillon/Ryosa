"""
Module de modération du chat Twitch
"""

import time
from collections import defaultdict, deque
from config import (
    DISCORD_WEBHOOK_URL, FLOOD_MAX_MSG, FLOOD_WINDOW_S,
    LINK_REGEX, BANNED_WORDS_REGEX
)
from utils import is_link_whitelisted


# Stockage anti-flood par utilisateur
user_msgs = defaultdict(lambda: deque())


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
        
        # Anti-flood
        if await self._check_flood(message, author, content):
            return True
        
        # Anti-liens
        if await self._check_links(message, author, content):
            return True
        
        # Mots interdits
        if await self._check_banned_words(message, author, content):
            return True
        
        return False

    async def _check_flood(self, message, author: str, content: str) -> bool:
        """Vérifie le flood."""
        now = time.time()
        dq = user_msgs[author]
        dq.append(now)
        
        while dq and now - dq[0] > FLOOD_WINDOW_S:
            dq.popleft()
        
        if len(dq) > FLOOD_MAX_MSG:
            await message.channel.send(f"@{author} stop spam.")
            await self._log(f"🛡️ FLOOD | @{author} | {len(dq)} msgs/{FLOOD_WINDOW_S}s")
            return True
        return False

    async def _check_links(self, message, author: str, content: str) -> bool:
        """Vérifie les liens non autorisés."""
        if LINK_REGEX.search(content) and not is_link_whitelisted(content):
            deleted = await self._delete_message(message)
            if deleted:
                await message.channel.send(f"@{author} pas de liens ici.")
                await self._log(f"🗑️ LIEN | @{author} | {content}")
            else:
                await self._log(f"⚠️ LIEN (delete impossible) | @{author} | {content}")
            return True
        return False

    async def _check_banned_words(self, message, author: str, content: str) -> bool:
        """Vérifie les mots interdits."""
        if BANNED_WORDS_REGEX.search(content):
            await message.channel.send(f"@{author} langage interdit.")
            await self._log(f"⛔ MOT | @{author} | {content}")
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
