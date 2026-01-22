"""
Script de lancement principal pour RyosaChii (Twitch + Discord).
Lance les deux bots en parallèle via asyncio.
"""
import asyncio
import os
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv()

from bot import Bot as TwitchBot
from discord_client import RyosaDiscordBot
from config import DISCORD_TOKEN

async def main():
    # 1. Instanciation des bots
    twitch_bot = TwitchBot()
    
    # Vérification du token Discord
    if not DISCORD_TOKEN:
        print("❌ [ERREUR] Pas de DISCORD_TOKEN trouvé dans .env !")
        print("   Le bot Twitch va démarrer seul, mais pas le bot Discord.")
        await twitch_bot.start()
        return

    discord_bot = RyosaDiscordBot()
    
    # 2. Lier les bots si besoin (pour qu'ils communiquent entre eux)
    # twitch_bot.discord_bot = discord_bot
    # discord_bot.twitch_bot = twitch_bot

    print("🚀 Démarrage de Ryosa (Twitch + Discord)...")

    # 3. Lancement parallèle
    # On utilise asyncio.gather pour lancer les deux boucles infinies
    try:
        await asyncio.gather(
            twitch_bot.start(),            # Démarrage Twitch
            discord_bot.start(DISCORD_TOKEN) # Démarrage Discord
        )
    except KeyboardInterrupt:
        # En cas d'arrêt manuel (Ctrl+C)
        print("🛑 Arrêt demandé...")
    finally:
        # Nettoyage propre
        if not discord_bot.is_closed():
            await discord_bot.close()
        # Le bot Twitch se ferme généralement tout seul via le signal, 
        # mais on peut forcer un save si besoin.

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
