import datetime
import json
import os
import re
import threading
import time

from core.config import config

class ProductivityManager:
    def __init__(self, speech_fn=None):
        self.speech_fn = speech_fn
        self.notes_file = config.get("notes_file")
        self.todo_file = config.get("todo_file")
        self.active_timers = []

    def set_speech_function(self, fn):
        self.speech_fn = fn

    # ---------- Notes ----------
    def add_note(self, text):
        timestamp = datetime.datetime.now().strftime("%d %b %H:%M")
        entry = f"[{timestamp}] {text.strip()}\n"
        try:
            with open(self.notes_file, "a", encoding="utf-8") as f:
                f.write(entry)
            return True
        except Exception:
            return False

    def get_notes(self, count=5):
        if not os.path.exists(self.notes_file):
            return []
        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip()]
            return lines[-count:]
        except Exception:
            return []

    def search_notes(self, query):
        if not os.path.exists(self.notes_file):
            return []
        try:
            results = []
            with open(self.notes_file, "r", encoding="utf-8") as f:
                for line in f:
                    if query.lower() in line.lower():
                        results.append(line.strip())
            return results
        except Exception:
            return []

    def clear_notes(self):
        try:
            if os.path.exists(self.notes_file):
                os.remove(self.notes_file)
            return True
        except Exception:
            return False

    # ---------- To-Do List ----------
    def _load_todos(self):
        if not os.path.exists(self.todo_file):
            return []
        try:
            with open(self.todo_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_todos(self, items):
        try:
            with open(self.todo_file, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2)
            return True
        except Exception:
            return False

    def add_todo(self, task):
        todos = self._load_todos()
        todos.append({
            "task": task.strip(),
            "created": datetime.datetime.now().isoformat(),
            "done": False
        })
        return self._save_todos(todos)

    def get_todos(self, include_done=False):
        todos = self._load_todos()
        if not include_done:
            return [t["task"] for t in todos if not t.get("done")]
        return todos

    def complete_todo(self, query):
        todos = self._load_todos()
        matched = False
        for t in todos:
            if not t.get("done") and query.lower() in t["task"].lower():
                t["done"] = True
                matched = True
                break
        if matched:
            self._save_todos(todos)
        return matched

    # ---------- Timers & Reminders ----------
    def set_timer(self, seconds, message="Time is up!"):
        timer_id = len(self.active_timers) + 1
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)

        def _worker():
            time.sleep(seconds)
            if self.speech_fn:
                self.speech_fn(f"Reminder alert: {message}")
            if timer_id in self.active_timers:
                self.active_timers.remove(timer_id)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        self.active_timers.append(timer_id)
        return end_time

    @staticmethod
    def parse_duration(text):
        """Parse natural language like '5 minutes', '30 seconds', '1 hour' into seconds."""
        total_seconds = 0
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*(second|sec|minute|min|hour|hr)s?", text.lower())
        for amount, unit in matches:
            val = float(amount)
            if "sec" in unit:
                total_seconds += val
            elif "min" in unit:
                total_seconds += val * 60
            elif "hour" in unit or "hr" in unit:
                total_seconds += val * 3600

        if total_seconds == 0:
            # Check for just a raw number e.g. "for 10" assuming minutes
            m = re.search(r"\bfor\s+(\d+)\b", text.lower())
            if m:
                total_seconds = float(m.group(1)) * 60

        return int(total_seconds)


productivity = ProductivityManager()
