"""
Module d'alertes automatiques dans le chat Twitch
Copyright (c) 2026 Tosachii et LaCabaneVirtuelle
"""

import asyncio
from config import TWITCH_CHANNEL, AUTO_MSG_INTERVAL, AUTO_MSG_THRESHOLD, AUTO_MSG_TEXT


class ChatAlerter:
    """Gère l'envoi de messages automatiques dans le chat."""

    def __init__(self, bot):
        self.bot = bot
        self.compteur_messages = 0
        self._tache_boucle = None

    async def start(self):
        """Démarre la boucle d'alertes."""
        if self._tache_boucle is None:
            self._tache_boucle = asyncio.create_task(self._boucle_alertes())
            print(f"📢 Alertes chat activées (toutes les {AUTO_MSG_INTERVAL}s si > {AUTO_MSG_THRESHOLD} msgs)")

    async def stop(self):
        """Arrête la boucle."""
        if self._tache_boucle:
            self._tache_boucle.cancel()
            try:
                await self._tache_boucle
            except asyncio.CancelledError:
                pass

    def compter_message(self):
        """Incrémente le compteur à chaque message user."""
        self.compteur_messages += 1

    async def _boucle_alertes(self):
        """Boucle principale des alertes automatiques."""
        # Premier délai pour ne pas spammer au démarrage
        await asyncio.sleep(AUTO_MSG_INTERVAL)
        
        while True:
            if self.compteur_messages >= AUTO_MSG_THRESHOLD:
                await self._envoyer_alerte()
                # On reset le compteur après l'envoi
                self.compteur_messages = 0
            
            # Attente avant prochaine vérif
            await asyncio.sleep(AUTO_MSG_INTERVAL)

    async def _envoyer_alerte(self):
        """Envoie le message dans le chat."""
        try:
            channel = self.bot.get_channel(TWITCH_CHANNEL)
            if channel:
                await channel.send(AUTO_MSG_TEXT)
                print(f"[ALERT] Message auto envoyé ({self.compteur_messages} msgs récents)")
            else:
                print(f"[ALERT] Channel {TWITCH_CHANNEL} introuvable (bot déconnecté ?)")
        except Exception as e:
            print(f"[ALERT] Erreur envoi: {e}")
