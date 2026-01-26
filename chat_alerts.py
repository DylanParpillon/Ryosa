import asyncio
import json
import os
import config

CONFIG_FILE = "dashboard_config.json"

class ChatAlerter:
    """Gère l'envoi de messages automatiques dans le chat."""

    def __init__(self, bot):
        self.bot = bot
        self.compteur_messages = 0
        self._tache = None
        
        # Valeurs par défaut (chargées depuis config.py ou le JSON)
        self.interval = config.AUTO_MSG_INTERVAL
        self.threshold = config.AUTO_MSG_THRESHOLD
        self.text = config.AUTO_MSG_TEXT
        self.enabled = True
        self.load_config()

    def load_config(self):
        """Charge la config depuis le JSON partagé."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.interval = data.get('auto_msg_interval', self.interval)
                    self.threshold = data.get('auto_msg_threshold', self.threshold)
                    self.text = data.get('auto_msg_text', self.text)
                    self.enabled = data.get('enabled', True)
            except Exception as e:
                print(f"[ALERT] Erreur lecture config: {e}")

    async def start(self):
        """Démarre la boucle."""
        if self._tache is None:
            self._tache = asyncio.create_task(self._boucle_alertes())
            print(f"📢 Alertes chat démarrées")

    async def stop(self):
        """Arrête la boucle."""
        if self._tache:
            self._tache.cancel()
            try:
                await self._tache
            except asyncio.CancelledError:
                pass
            self._tache = None

    def compter_message(self):
        """Incrémente le compteur à chaque message user."""
        self.compteur_messages += 1

    async def _boucle_alertes(self):
        """Boucle principale."""
        # Premier délai pour ne pas spammer
        await asyncio.sleep(10) 
        
        while True:
            # Recharger la config à chaque itération (ou presque)
            self.load_config()
            
            if not self.enabled:
                await asyncio.sleep(60)
                continue

            # Attendre l'intervalle configuré
            # On découpe l'attente pour être réactif aux changements (ex: toutes les 10s)
            wait_time = self.interval
            while wait_time > 0:
                step = min(10, wait_time)
                await asyncio.sleep(step)
                wait_time -= step
                # Si désactivé entre temps
                self.load_config()
                if not self.enabled:
                    break
            
            if not self.enabled:
                continue

            if self.compteur_messages >= self.threshold:
                await self._envoyer_alerte()
                self.compteur_messages = 0

    async def _envoyer_alerte(self):
        """Envoie le message."""
        try:
            channel = self.bot.get_channel(config.TWITCH_CHANNEL)
            if channel:
                await channel.send(self.text)
                print(f"[ALERT] Message auto envoyé ({self.compteur_messages} msgs)")
            else:
                # Si bot pas encore prêt ou channel pas trouvé
                pass
        except Exception as e:
            print(f"[ALERT] Erreur envoi: {e}")
