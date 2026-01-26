"""
Configuration du bot RyosaChii
Copyright (c) 2024 Tosachii et LaCabaneVirtuelle

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

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_BOT_ID = os.getenv("TWITCH_BOT_ID")
TWITCH_REFRESH_TOKEN = os.getenv("TWITCH_REFRESH_TOKEN")

# Fichier de persistance des tokens
TOKEN_STORE_FILE = "token_store.json"

# ══════════════════════════════════════════════════════════════════════════════
#                              DISCORD
# ══════════════════════════════════════════════════════════════════════════════

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")      # Logs modération
DISCORD_ANNOUNCE_URL = os.getenv("DISCORD_ANNOUNCE_URL")    # Annonces stream
DISCORD_ROLE_ID = os.getenv("DISCORD_ROLE_ID")              # ID du rôle @Membre
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")                  # Token du Bot Discord (Requis pour bot interactif)
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")          # ID Client Discord


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


# ══════════════════════════════════════════════════════════════════════════════
#                          MODERATION V2 (SCAM & ESCALADE)
# ══════════════════════════════════════════════════════════════════════════════

SAFE_MODE = False  # False = Ban réel activé !

# Mots-clés SCAM (déclenchent un BAN si lien ou compte récent)
SCAM_KEYWORDS = [
    "buy viewers", "big follows", "cheap viewers", "best viewers",
    "fame", "followers", "promotion", "twitch services", "best prices",
    "streamboo", "remove the space", "doge", "viewers for cheap",
    "viewers on", "follows on", "prices on", "quality viewers"
]
SCAM_REGEX = re.compile(r"|".join(re.escape(w) for w in SCAM_KEYWORDS), re.IGNORECASE)

# Regex pour détecter les liens "cachés" (ex: streamboo .com, discord .gg)
LINK_OBFUSCATION_REGEX = re.compile(
    r"\w+\s+\.(?:com|fr|tv|gg|net|org|io)|"  # domaine .com
    r"\(remove the space\)",                  # phrase typique
    re.IGNORECASE
)

# Seuil d'âge du compte pour être considéré comme "suspect" (jours)
ACCOUNT_AGE_THRESHOLD_DAYS = 7

# Système d'escalade des sanctions
# level 0 = 1er avertissement, level 1 = 2eme, etc.
WARNING_LEVELS = [
    {"action": "warn", "duration": 0},          # 1ère offense : Warning verbal
    {"action": "timeout", "duration": 60},      # 2ème : Timeout 1 min
    {"action": "timeout", "duration": 600},     # 3ème : Timeout 10 min
    {"action": "ban", "duration": 0}            # 4ème : Ban
]


# ══════════════════════════════════════════════════════════════════════════════
#                          AUTO MESSAGES (CHAT)
# ══════════════════════════════════════════════════════════════════════════════

AUTO_MSG_INTERVAL = 600  # 10 minutes en secondes
AUTO_MSG_THRESHOLD = 10   # Nombre de messages min. entre deux alertes
AUTO_MSG_TEXT = "📢 Rejoignez notre Discord : https://discord.gg/WjBfgXmEdU !\n\n📢 Le planning, les actus et si tu veux trouver des mates tout est dessus !!!"
