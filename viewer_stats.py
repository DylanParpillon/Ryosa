"""
Module de statistiques des viewers (Temps de visionnage, rangs, etc.)
Copyright (c) 2026 Tosachii et LaCabaneVirtuelle
"""

import json
import os
import asyncio
import time
from datetime import datetime
from twitchio.ext import commands, routines

DATA_FILE = "data/viewers.json"

class ViewerStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats = {}
        self.session_start = {}  # {user_id: timestamp} pour la session actuelle
        self._load_stats()
        self.verifier_presence.start()

    def _load_stats(self):
        """Charge les statistiques depuis le fichier JSON."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.stats = json.load(f)
            except Exception as e:
                print(f"[STATS] Erreur chargement: {e}")
                self.stats = {}
        
        # S'assurer que le dossier data existe
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    def _save_stats(self):
        """Sauvegarde les statistiques dans le fichier JSON."""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            print(f"[STATS] Erreur sauvegarde: {e}")

    def _update_user(self, user):
        """Met à jour les infos de base d'un viewer."""
        user_id = str(user.id)
        if user_id not in self.stats:
            self.stats[user_id] = {
                "username": user.name,
                "total_minutes": 0,
                "first_seen": time.time(),
                "last_seen": time.time()
            }
        else:
            self.stats[user_id]["username"] = user.name
            self.stats[user_id]["last_seen"] = time.time()

    @routines.routine(minutes=1)
    async def verifier_presence(self):
        """Vérifie les chatters présents et ajoute 1 minute à leur compteur."""
        # On ne compte que si le stream est (théoriquement) lancé ou si le bot détecte de l'activité
        # Pour simplifier ici, on compte pour tous les gens connectés au chat
        try:
            # Note: Pour TwitchIO, on récupère les chatters via le channel
            # Il faut que le bot ait rejoint le channel
            for channel in self.bot.connected_channels:
                chatters = channel.chatters
                if not chatters:
                    continue
                
                for chatter in chatters:
                    # Ignore le bot lui-même
                    if chatter.name.lower() == self.bot.nick.lower():
                        continue

                    self._update_user(chatter)
                    self.stats[str(chatter.id)]["total_minutes"] += 1
                
            self._save_stats()
        except Exception as e:
            print(f"[STATS] Erreur boucle présence: {e}")

    @commands.command(name="mytime")
    async def mytime(self, ctx: commands.Context):
        """Affiche le temps de visionnage du viewer et depuis quand il follow."""
        user_id = str(ctx.author.id)
        
        # 1. Temps de visionnage
        minutes = 0
        if user_id in self.stats:
            minutes = self.stats[user_id]["total_minutes"]
        
        heures = minutes // 60
        rest_minutes = minutes % 60
        temps_str = f"{heures}h{rest_minutes:02d}"
        
        # 2. Date de follow (Appel API Twitch)
        follow_text = "Pas de follow détecté"
        try:
            # On cherche le channel broadcaster
            broadcaster = (await self.bot.fetch_users(names=[ctx.channel.name]))[0]
            # On cherche le lien de follow entre l'auteur et le broadcaster
            # Note: fetch_followers est paginé, mais ici on veut juste un user spécifique
            # Malheureusement l'API Twitch v5 simple n'existe plus, il faut ruser
            # TwitchIO helper: 
            follow = await ctx.author.fetch_follow(to_user=broadcaster.id, token=self.bot._http.token)
            
            if follow:
                # Calcul de la durée
                now = datetime.now(follow.followed_at.tzinfo)
                diff = now - follow.followed_at
                jours = diff.days
                
                date_follow = follow.followed_at.strftime("%d/%m/%Y")
                follow_text = f"{jours} jours ({date_follow})"
            else:
                follow_text = "ne follow pas encore (HONTE !)"
                
        except Exception as e:
            # Souvent erreur si pas follow ou token scope manquant
            print(f"[STATS] Erreur check follow: {e}")
            follow_text = "donnée indisponible"

        await ctx.send(f"⏳ @{ctx.author.name} : Tu as regardé le stream pendant **{temps_str}** ! "
                       f"Tu es là depuis : **{follow_text}**.")

    @commands.command(name="ScoreTime")
    async def score_time(self, ctx: commands.Context):
        """Affiche le top 5 des viewers les plus fidèles."""
        # Trier par total_minutes décroissant
        sorted_users = sorted(
            self.stats.items(), 
            key=lambda item: item[1].get("total_minutes", 0), 
            reverse=True
        )
        
        top_5 = sorted_users[:5]
        msg_lines = ["🏆 **Top 5 Fidélité** 🏆"]
        
        for i, (uid, data) in enumerate(top_5, 1):
            mins = data["total_minutes"]
            h = mins // 60
            m = mins % 60
            pseudo = data.get("username", "Inconnu")
            msg_lines.append(f"{i}. **{pseudo}** : {h}h{m:02d}")
            
        await ctx.send(" | ".join(msg_lines))

def prepare(bot):
    bot.add_cog(ViewerStats(bot))
