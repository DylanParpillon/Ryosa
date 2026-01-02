"""
Fonctions utilitaires pour le bot RyosaChii
"""

import re
from config import LINK_REGEX, LINK_WHITELIST, STREAMER_TAG_REGEX


def is_link_whitelisted(text: str) -> bool:
    """Vérifie si tous les liens du texte sont dans la whitelist."""
    if not LINK_WHITELIST:
        return False
    for match in re.finditer(LINK_REGEX, text):
        link = match.group(0).lower()
        if not any(re.search(pattern, link, re.IGNORECASE) for pattern in LINK_WHITELIST):
            return False
    return True


def detect_streamer(title: str) -> str:
    """Détecte le streamer via [ICHI], [TOSA], [TOSA&ICHI] dans le titre."""
    t = title.upper()
    if "[TOSA&ICHI]" in t or "[ICHI&TOSA]" in t:
        return "TOSA&ICHI"
    elif "[ICHI]" in t:
        return "ICHI"
    elif "[TOSA]" in t:
        return "TOSA"
    return "DEFAULT"


def clean_title(title: str) -> str:
    """Retire les tags [TOSA], [ICHI], [TOSA&ICHI] du titre."""
    return STREAMER_TAG_REGEX.sub('', title).strip()
