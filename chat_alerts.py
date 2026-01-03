"""
Module d'alertes automatiques dans le chat Twitch
"""

import asyncio
from config import TWITCH_CHANNEL, AUTO_MSG_INTERVAL, AUTO_MSG_THRESHOLD, AUTO_MSG_TEXT

class ChatAlerter:
    """Gère l'envoi de messages automatiques dans le chat."""

    def __init__(self, bot):
        self.bot = bot
        self.msg_count = 0
        self._task = None

    async def start(self):
        """Démarre la boucle d'alertes."""
        if self._task is None:
            self._task = asyncio.create_task(self._loop())
            print(f"📢 Alertes chat activées (toutes les {AUTO_MSG_INTERVAL}s si > {AUTO_MSG_THRESHOLD} msgs)")

    async def stop(self):
        """Arrête la boucle."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def on_message(self):
        """Incrémente le compteur à chaque message user."""
        self.msg_count += 1

    async def _loop(self):
        """Boucle principale."""
        # Premier délai pour ne pas spammer au boot
        await asyncio.sleep(AUTO_MSG_INTERVAL)
        
        while True:
            if self.msg_count >= AUTO_MSG_THRESHOLD:
                await self._send_alert()
                # On reset le compteur après l'envoi
                self.msg_count = 0
            
            # Attente avant prochaine vérif
            await asyncio.sleep(AUTO_MSG_INTERVAL)

    async def _send_alert(self):
        """Envoie le message dans le chat."""
        try:
            # get_channel retourne le channel s'il est dans le cache
            channel = self.bot.get_channel(TWITCH_CHANNEL)
            if channel:
                await channel.send(AUTO_MSG_TEXT)
                print(f"[ALERT] Message auto envoyé ({self.msg_count} msgs récents)")
            else:
                print(f"[ALERT] Channel {TWITCH_CHANNEL} introuvable (bot déconnecté ?)")
        except Exception as e:
            print(f"[ALERT] Erreur envoi: {e}")
