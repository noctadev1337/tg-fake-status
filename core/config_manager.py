import json
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

load_dotenv(os.path.join(BASE_DIR, ".env"))

class ConfigManager:
    def __init__(self):
        with open(CONFIG_PATH, "r") as f:
            self._data = json.load(f)
        os.makedirs(TEMPLATES_DIR, exist_ok=True)

    def save(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @property
    def api_id(self): return int(os.getenv("API_ID", 2040))
    @property
    def api_hash(self): return os.getenv("API_HASH", "b18441a1ff607e10a989891a5462e627")
    @property
    def session_path(self): return os.getenv("SESSION_PATH", "/root/tg-activity/session")

    @property
    def timezone_offset(self): return self._data.get("timezone_offset", 3)

    def set_timezone(self, offset):
        self._data["timezone_offset"] = int(offset)
        self.save()

    @property
    def current_schedule(self):
        return self._data["schedules"].get("current", [])

    def set_current_schedule(self, sessions):
        self._data["schedules"]["current"] = sessions
        self.save()

    def clear_current(self):
        self._data["schedules"]["current"] = []
        self.save()

    def list_templates(self):
        return sorted([f[:-5] for f in os.listdir(TEMPLATES_DIR) if f.endswith(".json")])

    def save_template(self, name, sessions=None):
        if sessions is None:
            sessions = self.current_schedule
        with open(os.path.join(TEMPLATES_DIR, f"{name}.json"), "w") as f:
            json.dump({"sessions": sessions}, f, indent=2)

    def load_template(self, name):
        path = os.path.join(TEMPLATES_DIR, f"{name}.json")
        if not os.path.exists(path): return None
        with open(path) as f:
            return json.load(f).get("sessions", [])

    def apply_template(self, name):
        sessions = self.load_template(name)
        if sessions is None: return False
        self.set_current_schedule(sessions)
        return True

    def delete_template(self, name):
        path = os.path.join(TEMPLATES_DIR, f"{name}.json")
        if os.path.exists(path):
            os.remove(path); return True
        return False

    def is_saved_as_template(self):
        current = self.current_schedule
        return any(self.load_template(n) == current for n in self.list_templates())
