"""
Serveur Web pour le Dashboard RyosaChii (Mode Autonome)
"""

import os
import json
import socket
from aiohttp import web
from custom_commands import CommandManager

CONFIG_FILE = "dashboard_config.json"

class DashboardApp:
    def __init__(self):
        self.cmd_manager = CommandManager()
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Configuration des routes
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/api/commands', self.handle_get_commands)
        self.app.router.add_post('/api/commands', self.handle_add_command)
        self.app.router.add_delete('/api/commands', self.handle_delete_command)
        # Routes pour les alertes
        self.app.router.add_get('/api/alerts', self.handle_get_alerts)
        self.app.router.add_post('/api/alerts', self.handle_update_alerts)

    async def start(self):
        """Démarre le serveur web."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', 8080)
        await self.site.start()
        print("🌍 Dashboard accessible sur :")
        print("   👉 Local :   http://localhost:8080")
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"   👉 Réseau :  http://{local_ip}:8080")
        except:
            pass

    async def get_config(self):
        if os.path.exists(CONFIG_FILE):
             with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                 return json.load(f)
        return {
            "auto_msg_interval": 300,
            "auto_msg_threshold": 5,
            "auto_msg_text": "",
            "enabled": True
        }

    async def save_config(self, data):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    # --- Routes ---

    async def handle_index(self, request):
        """Sert la page principale HTML."""
        path = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
        with open(path, 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')

    async def handle_get_commands(self, request):
        """API: Récupère toutes les commandes."""
        return web.json_response(self.cmd_manager.get_all())

    async def handle_add_command(self, request):
        """API: Ajoute une commande."""
        data = await request.json()
        name = data.get('name')
        response = data.get('response')
        
        if name and response:
            self.cmd_manager.add_command(name, response)
            return web.json_response({'status': 'ok'})
        return web.json_response({'error': 'missing data'}, status=400)

    async def handle_delete_command(self, request):
        """API: Supprime une commande."""
        data = await request.json()
        name = data.get('name')
        
        if name:
            self.cmd_manager.remove_command(name)
            return web.json_response({'status': 'ok'})
        return web.json_response({'error': 'missing name'}, status=400)

    async def handle_get_alerts(self, request):
        """API: Récupère les paramètres d'alertes."""
        data = await self.get_config()
        return web.json_response({
            'interval': data.get('auto_msg_interval', 300),
            'threshold': data.get('auto_msg_threshold', 5),
            'text': data.get('auto_msg_text', ""),
            'enabled': data.get('enabled', True)
        })

    async def handle_update_alerts(self, request):
        """API: Met à jour les paramètres d'alertes."""
        data = await request.json()
        current_config = await self.get_config()
        
        if 'interval' in data:
            current_config['auto_msg_interval'] = int(data['interval'])
        if 'threshold' in data:
            current_config['auto_msg_threshold'] = int(data['threshold'])
        if 'text' in data:
            current_config['auto_msg_text'] = data['text']
            
        # Pas besoin de redémarrer le bot, le bot surveille le fichier JSON
        
        await self.save_config(current_config)
        return web.json_response({'status': 'ok'})

if __name__ == '__main__':
    import asyncio
    dashboard = DashboardApp()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(dashboard.start())
        print("Appuyez sur Ctrl+C pour arrêter.")
        loop.run_forever()
    except KeyboardInterrupt:
        pass
