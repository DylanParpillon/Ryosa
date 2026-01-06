"""
Serveur Web pour le Dashboard RyosaChii
"""

import os
from aiohttp import web
from custom_commands import CommandManager

class Dashboard:
    def __init__(self, bot):
        self.bot = bot
        self.cmd_manager = CommandManager()
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Configuration des routes
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/api/commands', self.handle_get_commands)
        self.app.router.add_post('/api/commands', self.handle_add_command)
        self.app.router.add_delete('/api/commands', self.handle_delete_command)

    async def start(self):
        """Démarre le serveur web."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', 8080)
        await self.site.start()
        print("🌍 Dashboard accessible sur :")
        print("   👉 Local :   http://localhost:8080")
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"   👉 Réseau :  http://{local_ip}:8080")
        except:
            pass

    async def stop(self):
        """Arrête le serveur web."""
        if self.runner:
            await self.runner.cleanup()

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
