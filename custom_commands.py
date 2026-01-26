"""
Gestionnaire des commandes personnalisées
"""
import json
import os

COMMANDS_FILE = "commands.json"

class CommandManager:
    def __init__(self):
        self.commands = {}
        self.load()

    def load(self):
        """Charge les commandes depuis le fichier JSON."""
        if os.path.exists(COMMANDS_FILE):
            try:
                with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
                    self.commands = json.load(f)
            except Exception as e:
                print(f"[CMD] Erreur chargement: {e}")
                self.commands = {}
        else:
            self.commands = {}

    def save(self):
        """Sauvegarde les commandes dans le fichier JSON."""
        try:
            with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.commands, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[CMD] Erreur sauvegarde: {e}")

    def add_command(self, name: str, response: str) -> bool:
        """Ajoute ou modifie une commande."""
        name = name.lower().strip()
        if not name.startswith("!"):
            name = "!" + name
        
        self.commands[name] = response
        self.save()
        return True

    def remove_command(self, name: str) -> bool:
        """Supprime une commande."""
        name = name.lower().strip()
        if not name.startswith("!"):
            name = "!" + name
            
        if name in self.commands:
            del self.commands[name]
            self.save()
            return True
        return False

    def get_response(self, message_content: str) -> str | None:
        """Cherche si le message correspond à une commande."""
        # Check if file changed
        if os.path.exists(COMMANDS_FILE):
            try:
                mtime = os.path.getmtime(COMMANDS_FILE)
                if not hasattr(self, '_last_mtime') or mtime > self._last_mtime:
                    self.load()
                    self._last_mtime = mtime
            except Exception:
                pass

        cmd = message_content.split()[0].lower()
        return self.commands.get(cmd)

    def get_all(self):
        """Retourne toutes les commandes."""
        return self.commands
