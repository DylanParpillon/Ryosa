# 🤖 RyosaChii Bot

Bot Twitch de modération + annonces Discord automatiques.

## ✨ Fonctionnalités

- **Annonces Discord** : Notifie automatiquement quand le stream passe en live
  - Détecte `[TOSA]`, `[ICHI]`, `[TOSA&ICHI]` dans le titre pour personnaliser le message
  - Ping le rôle @Membre
  - Affiche la catégorie et le titre du stream

- **Modération Chat** :
  - Anti-flood (max 5 messages / 7 secondes)
  - Anti-liens (avec whitelist configurable)
  - Filtre de mots interdits
  - Logs vers Discord

## 📁 Structure

```
Ryosa/
├── .env              # Variables d'environnement (secrets)
├── bot.py            # Point d'entrée
├── config.py         # Configuration (messages, limites)
├── utils.py          # Fonctions utilitaires
├── announcer.py      # Annonces Discord
└── moderation.py     # Modération chat
```

## 🚀 Installation

```bash
# Créer l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux

# Installer les dépendances
pip install twitchio==2.10.0 python-dotenv aiohttp
```

## ⚙️ Configuration

Créer un fichier `.env` :

```env
TWITCH_NICK=RyosaChii
TWITCH_CHANNEL=lacabanevirtuelle
TWITCH_TOKEN=oauth:xxxxxxxxxxxxxxx

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...  # Logs modération
DISCORD_ANNOUNCE_URL=https://discord.com/api/webhooks/... # Annonces stream
DISCORD_ROLE_ID=123456789012345678                        # ID du rôle @Membre
```

## 🎮 Lancement

```bash
python bot.py
```

## 📝 Personnalisation

Modifier `config.py` pour :
- **Messages d'annonce** : lignes 42-47
- **URL du stream** : ligne 38
- **Limites anti-flood** : lignes 59-60
- **Mots interdits** : ligne 83
- **Whitelist liens** : lignes 76-79

## 📜 Licence

Projet privé - LaCabaneVirtuelle
