# 🤖 RyosaChii Bot

Bot Twitch de modération + annonces Discord automatiques + Clips + Alertes.
Développé par **Tosachii et LaCabaneVirtuelle**.

## ✨ Fonctionnalités

- **Annonces Discord** : Notifie automatiquement quand le stream passe en live
  - Détecte `[TOSA]`, `[ICHI]`, `[TOSA&ICHI]` dans le titre pour personnaliser le message
  - Ping le rôle @Membre
  - Affiche la catégorie et le titre du stream

- **Modération Chat** :
  - **Anti-flood** : Limite messages rapides (configurable)
  - **Anti-liens** : Bloque les liens non whitelistés (+ détection liens cachés)
  - **Anti-scam** : Bloque les bots connus (streamboo, etc.) et les mots-clés d'arnaque
  - **Logs Discord** : Remonte toutes les actions de modération + Succès/Echecs de Clips + Démarrage/Arrêt du bot

- **Commandes** :
  - `!clip` : Crée un clip instantané, crédite l'utilisateur dans le chat, log le résultat sur Discord.

- **Auto-Messages** :
  - Poste automatiquement un message (ex: lien Discord) toutes les 5 minutes si le chat est actif.

## 📁 Structure

```
Ryosa/
├── .env              # Secrets (Token, IDs)
├── bot.py            # Point d'entrée principal
├── config.py         # Configuration générale
├── announcer.py      # Module Annonces Stream
├── chat_alerts.py    # Module Messages Autos Chat
├── moderation.py     # Module Modération & Logs
└── utils.py          # Fonctions utilitaires
```

## 🚀 Installation

```bash
# Créer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

## ⚙️ Configuration

Remplir le fichier `.env` :

```env
TWITCH_NICK=[Compte bot Name]
TWITCH_CHANNEL=[Channel Name]
TWITCH_TOKEN=oauth:xxxxxxxxxxxxxxx
TWITCH_CLIENT_ID=...
TWITCH_CLIENT_SECRET=...
TWITCH_REFRESH_TOKEN=...

DISCORD_WEBHOOK_URL=...      # Pour les logs modération/système
DISCORD_ANNOUNCE_URL=...     # Pour les annonces live
DISCORD_ROLE_ID=...          # ID du rôle à ping
```

## 📜 Licence

Copyright © 2026 **Tosachii et LaCabaneVirtuelle**.
Projet privé. Toute reproduction interdite sans autorisation.

## 🚀 Lancement (Déploiement)

Le projet est maintenant séparé en deux processus distincts à lancer en parallèle sur ta VM :

1. **Le Bot (Ryosa)** : Gère le chat, la modération, les clips et les annonces.
2. **Le Dashboard** : Site web pour configurer les commandes et les alertes.

### 1️⃣ Lancer le Bot
```bash
python run.py
```
_Note : `run.py` lance Ryosa (Twitch) et le module Discord s'il est configuré._

### 2️⃣ Lancer le Dashboard (Site Web)
Ouvre un **nouveau terminal** (ou utilise `screen`/`systemd`) et lance :
```bash
python dashboard.py
```

Les deux communiquent via les fichiers `commands.json` et `dashboard_config.json`.
Le bot envoie un "heartbeat" (ping) sur Discord toutes les 10 minutes pour dire qu'il est en vie.
