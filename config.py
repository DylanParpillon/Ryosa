"""
Configuration du bot RyosaChii
Toutes les variables de configuration centralisées ici
"""

import os
import re
from dotenv import load_dotenv

load_dotenv()


# ══════════════════════════════════════════════════════════════════════════════
#                              TWITCH
# ══════════════════════════════════════════════════════════════════════════════

TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_NICK = os.getenv("TWITCH_NICK")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")

if not TWITCH_TOKEN or not TWITCH_NICK or not TWITCH_CHANNEL:
    raise SystemExit("❌ Manque TWITCH_TOKEN / TWITCH_NICK / TWITCH_CHANNEL dans .env")


# ══════════════════════════════════════════════════════════════════════════════
#                              DISCORD
# ══════════════════════════════════════════════════════════════════════════════

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")      # Logs modération
DISCORD_ANNOUNCE_URL = os.getenv("DISCORD_ANNOUNCE_URL")    # Annonces stream
DISCORD_ROLE_ID = os.getenv("DISCORD_ROLE_ID")              # ID du rôle @Membre


# ══════════════════════════════════════════════════════════════════════════════
#                          ANNONCES STREAM
# ══════════════════════════════════════════════════════════════════════════════

STREAM_URL = "https://www.twitch.tv/lacabanevirtuelle"
POLL_INTERVAL_S = 60  # Vérifie toutes les 60 secondes

# 👇 MODIFIE TES MESSAGES ICI 👇
# Variables : {title} = titre du stream, {category} = catégorie Twitch
ANNOUNCE_MESSAGES = {
    "TOSA&ICHI": "💜 Tosachii & Ichiro sont en live ensemble !\n\nCatégorie: **{category}**\nTitre: {title}\n\n👉 " + STREAM_URL,
    "TOSA":      "🩷 Tosachii est en live !\n\nCatégorie: **{category}**\nTitre: {title}\n\n👉 " + STREAM_URL,
    "ICHI":      "❤️ Ichiro est en live !\n\nCatégorie: **{category}**\nTitre: {title}\n\n👉 " + STREAM_URL,
    "DEFAULT":   "🎮 On est en live !\n\nCatégorie: **{category}**\nTitre: {title}\n\n👉 " + STREAM_URL,
}

# Regex pour détecter les tags de streamer
STREAMER_TAG_REGEX = re.compile(r'\[(?:TOSA&ICHI|ICHI&TOSA|TOSA|ICHI)\]\s*', re.IGNORECASE)


# ══════════════════════════════════════════════════════════════════════════════
#                              MODERATION
# ══════════════════════════════════════════════════════════════════════════════

# Anti-flood
FLOOD_MAX_MSG = 5       # Nombre max de messages
FLOOD_WINDOW_S = 7      # Dans cette fenêtre (secondes)

# Anti-liens - TLDs reconnus
COMMON_TLDS = (
    "com", "org", "net", "fr", "tv", "gg", "io", "co", "me", "be", "ly",
    "eu", "de", "uk", "ru", "info", "biz", "xyz", "online", "site", "app"
)

LINK_REGEX = re.compile(
    r"(?:https?://|www\.)[^\s]+"
    r"|"
    r"\b[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)*"
    r"(?:" + "|".join(COMMON_TLDS) + r")(?:/[^\s]*)?\b",
    re.IGNORECASE
)

# Domaines autorisés (décommenter pour activer)
LINK_WHITELIST = [
    # r"twitch\.tv/lacabanevirtuelle",
    # r"youtube\.com",
]

# Mots interdits
BANNED_WORDS = ["viagra", "crypto", "follow4follow"]
BANNED_WORDS_REGEX = re.compile(r"|".join(re.escape(w) for w in BANNED_WORDS), re.IGNORECASE)
