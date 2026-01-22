"""
Module de commandes générales pour RyosaChii
"""

import datetime
from twitchio.ext import commands
from config import TWITCH_CHANNEL

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stream_start_time = None

    @commands.Cog.event()
    async def event_ready(self):
        """Met à jour le temps de lancement si le stream est déjà on."""
        # On pourrait vérifier l'API ici, mais pour faire simple on init à None
        # Le mieux est d'utiliser l'event_stream_online si on veut être précis
        pass

    @commands.command(name="uptime")
    async def uptime(self, ctx: commands.Context):
        """Affiche depuis combien de temps le stream est lancé."""
        try:
            streams = await self.bot.fetch_streams(user_logins=[TWITCH_CHANNEL])
            if not streams:
                await ctx.send("❌ Le stream est hors ligne !")
                return

            stream = streams[0]
            # Twitch renvoie started_at en UTC
            uptime = datetime.datetime.now(datetime.timezone.utc) - stream.started_at
            
            heures = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            secondes = uptime.seconds % 60
            
            await ctx.send(f"🕒 Live depuis : **{heures}h {minutes}m {secondes}s**")
        except Exception as e:
            print(f"[UPTIME] Erreur: {e}")
            await ctx.send("❌ Impossible de récupérer l'uptime.")

    @commands.command(name="so")
    async def shoutout(self, ctx: commands.Context, pseudo: str = None):
        """Fait une pub pour un streamer (!so @pseudo)."""
        # Vérification permissions (Broadcaster ou Mod)
        if not ctx.author.is_mod and not ctx.author.is_broadcaster:
            return

        if not pseudo:
            await ctx.send("⚠️ Utilisation : !so @pseudo")
            return

        # Nettoyage du @ si présent
        pseudo = pseudo.lstrip('@')

        try:
            users = await self.bot.fetch_users(names=[pseudo])
            if not users:
                await ctx.send(f"❌ Streamer {pseudo} introuvable.")
                return

            user = users[0]
            
            # On essaie de choper le dernier jeu joué
            channel_info = await self.bot.fetch_channels(broadcaster_ids=[user.id])
            game_name = channel_info[0].game_name if channel_info else "Inconnu"

            await ctx.send(f"💜 Allez donner de la force à @{user.name} ! "
                           f"Ils jouaient à **{game_name}** dernièrement. "
                           f"Go follow 👉 https://twitch.tv/{user.name}")
        except Exception as e:
            print(f"[SO] Erreur: {e}")

    @commands.command(name="lurk")
    async def lurk(self, ctx: commands.Context):
        """Petit message de lurk."""
        await ctx.send(f"🫣 @{ctx.author.name} part se cacher dans l'ombre... Merci d'être là ! 💜")

    @commands.command(name="commandes", aliases=["help", "cmds"])
    async def commandes(self, ctx: commands.Context):
        """Affiche la liste dynamique des commandes disponibles."""
        # 1. Commandes hardcodées (Cogs + Bot)
        cmd_list = []
        for cmd in self.bot.commands.values():
            # On cache les commandes 'cachées' si besoin, ici on prend tout
            cmd_list.append(f"!{cmd.name}")

        # 2. Commandes personnalisées (Custom commands)
        # On accède au manager via le bot (qui a été attaché dans bot.py -> self.dashboard.cmd_manager)
        if hasattr(self.bot, 'dashboard') and self.bot.dashboard:
            custom_cmds = self.bot.dashboard.cmd_manager.get_all()
            for c in custom_cmds:
                cmd_list.append(f"!{c['name']}")

        # Tri et affichage
        cmd_list.sort()
        msg = "📜 **Commandes dispo** : " + ", ".join(cmd_list)
        
        # Twitch a une limite de 500 caractères, on tronque si besoin
        if len(msg) > 500:
            msg = msg[:497] + "..."
            
        await ctx.send(msg)

    # Commandes Admin pour changer titre/catégorie
    
    @commands.command(name="title")
    async def set_title(self, ctx: commands.Context, *, new_title: str = None):
        """Change le titre du stream (Mod only)."""
        if not ctx.author.is_mod and not ctx.author.is_broadcaster:
            return
            
        if not new_title:
            await ctx.send("⚠️ Utilisation : !title <Nouveau Titre>")
            return

        try:
            # Besoin du token utilisateur avec scope channel:manage:broadcast
            # On utilise le token du bot (qui doit être broadcaster ou modérateur avec token éditeur)
            # En V2 c'est un peu touchy, il faut modify_channel sur le broadcaster
            broadcaster = (await self.bot.fetch_users(names=[TWITCH_CHANNEL]))[0]
            await self.bot.modify_channel(broadcaster.id, title=new_title, token=self.bot._http.token)
            await ctx.send(f"✅ Titre mis à jour : **{new_title}**")
        except Exception as e:
            await ctx.send(f"❌ Erreur modif titre : {e}")

    @commands.command(name="game")
    async def set_game(self, ctx: commands.Context, *, new_game: str = None):
        """Change la catégorie du stream (Mod only)."""
        if not ctx.author.is_mod and not ctx.author.is_broadcaster:
            return
            
        if not new_game:
            await ctx.send("⚠️ Utilisation : !game <Nom du jeu>")
            return

        try:
            # Il faut trouver l'ID du jeu d'abord
            games = await self.bot.fetch_games(names=[new_game])
            if not games:
                await ctx.send("❌ Jeu introuvable sur Twitch.")
                return
            
            game_id = games[0].id
            real_name = games[0].name
            
            broadcaster = (await self.bot.fetch_users(names=[TWITCH_CHANNEL]))[0]
            await self.bot.modify_channel(broadcaster.id, game_id=game_id, token=self.bot._http.token)
            await ctx.send(f"✅ Catégorie mise à jour : **{real_name}**")
        except Exception as e:
            await ctx.send(f"❌ Erreur modif jeu : {e}")

def prepare(bot):
    bot.add_cog(GeneralCommands(bot))
