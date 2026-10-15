import json
import os
import platform

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Try loading .env if python-dotenv is present
try:
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
except ImportError:
    pass

DEFAULT_CONFIG = {
    "wake_word": "jarvis",
    "strict_wake_word": False,
    "microphone_device": None,
    "user_name": "Boss",
    "default_city": "",
    "voice_rate": 180,
    "voice_volume": 1.0,
    "sound_feedback": True,
    "notes_file": os.path.join(os.path.expanduser("~"), "jarvis_notes.txt"),
    "todo_file": os.path.join(os.path.expanduser("~"), "jarvis_todo.json"),
    "ai_provider": "auto",  # auto, gemini, claude, openai, ollama, offline
    "ai_model": os.environ.get("JARVIS_MODEL", ""),
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3",
    "sites": {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "whatsapp": "https://web.whatsapp.com",
        "linkedin": "https://www.linkedin.com",
        "stack overflow": "https://stackoverflow.com",
        "maps": "https://maps.google.com",
        "chatgpt": "https://chatgpt.com",
        "claude": "https://claude.ai",
        "reddit": "https://reddit.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "netflix": "https://netflix.com",
        "spotify": "https://open.spotify.com"
    },
    "apps": {
        "notepad": {"Windows": "notepad", "Darwin": "TextEdit", "Linux": "gedit"},
        "calculator": {"Windows": "calc", "Darwin": "Calculator", "Linux": "gnome-calculator"},
        "chrome": {"Windows": "chrome", "Darwin": "Google Chrome", "Linux": "google-chrome"},
        "vs code": {"Windows": "code", "Darwin": "Visual Studio Code", "Linux": "code"},
        "paint": {"Windows": "mspaint", "Darwin": "Preview", "Linux": "gimp"},
        "file explorer": {"Windows": "explorer", "Darwin": "Finder", "Linux": "nautilus"},
        "terminal": {"Windows": "cmd", "Darwin": "Terminal", "Linux": "gnome-terminal"},
        "powershell": {"Windows": "powershell", "Darwin": "Terminal", "Linux": "gnome-terminal"},
        "word": {"Windows": "winword", "Darwin": "Microsoft Word", "Linux": "libreoffice --writer"},
        "excel": {"Windows": "excel", "Darwin": "Microsoft Excel", "Linux": "libreoffice --calc"},
        "powerpoint": {"Windows": "powerpnt", "Darwin": "Microsoft PowerPoint", "Linux": "libreoffice --impress"},
        "task manager": {"Windows": "taskmgr", "Darwin": "Activity Monitor", "Linux": "gnome-system-monitor"},
        "settings": {"Windows": "ms-settings:", "Darwin": "System Preferences", "Linux": "gnome-control-center"},
        "control panel": {"Windows": "control", "Darwin": "System Preferences", "Linux": "gnome-control-center"},
        "spotify": {"Windows": "spotify", "Darwin": "Spotify", "Linux": "spotify"},
        "antigravity": {
            "Windows": "C:\\Users\\Sagar H C\\Desktop\\Antigravity.lnk",
            "Darwin": "Antigravity",
            "Linux": "antigravity"
        },
        "mongodb compass": {
            "Windows": "C:\\Users\\Sagar H C\\Desktop\\MongoDB Compass.lnk",
            "Darwin": "MongoDB Compass",
            "Linux": "mongodb-compass"
        },
        "mongodb": {
            "Windows": "C:\\Users\\Sagar H C\\Desktop\\MongoDB Compass.lnk",
            "Darwin": "MongoDB Compass",
            "Linux": "mongodb-compass"
        },
        "compass": {
            "Windows": "C:\\Users\\Sagar H C\\Desktop\\MongoDB Compass.lnk",
            "Darwin": "MongoDB Compass",
            "Linux": "mongodb-compass"
        },
        "the last of us": {
            "Windows": "C:\\Users\\Public\\Desktop\\The Last of Us - Part II Remastered.lnk"
        },
        "last of us": {
            "Windows": "C:\\Users\\Public\\Desktop\\The Last of Us - Part II Remastered.lnk"
        },
        "discord": {
            "Windows": "C:\\Users\\Sagar H C\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Discord Inc\\Discord.lnk",
            "Darwin": "Discord",
            "Linux": "discord"
        },
        "brave": {
            "Windows": "C:\\Users\\Sagar H C\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Brave.lnk",
            "Darwin": "Brave Browser",
            "Linux": "brave-browser"
        },
        "steam": {
            "Windows": "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Steam\\Steam.lnk",
            "Darwin": "Steam",
            "Linux": "steam"
        },
        "vlc": {
            "Windows": "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\VideoLAN\\VLC media player.lnk",
            "Darwin": "VLC",
            "Linux": "vlc"
        }
    }
}


class Config:
    def __init__(self):
        self.data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.data.update(saved)
            except Exception as e:
                print(f"[Config] Error loading config.json: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[Config] Error saving config.json: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()


config = Config()
OS = platform.system()  # "Windows", "Darwin", "Linux"
