import ast
import datetime
import math
import operator
import os
import random
import re

from core.ai import ai
from core.config import config, OS
from core.productivity import productivity
from core.speech import speech
from core.system_tools import system_tools
from core.web_tools import web_tools

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "Why did the computer go to the doctor? It caught a virus.",
    "A SQL query walks into a bar, walks up to two tables and asks: can I join you?",
    "Why was the network engineer calm? He had a lot of bandwidth.",
    "How many programmers does it take to change a light bulb? None, that's a hardware problem.",
    "There's no place like 127.0.0.1.",
]

# Safe arithmetic evaluation
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

def safe_eval_math(expr):
    """Safely evaluate basic math expressions without using eval()."""
    try:
        clean_expr = expr.replace("x", "*").replace("times", "*").replace("divided by", "/").replace("^", "**")
        node = ast.parse(clean_expr, mode='eval').body

        def _eval(n):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                return n.value
            elif isinstance(n, ast.BinOp) and type(n.op) in OPERATORS:
                return OPERATORS[type(n.op)](_eval(n.left), _eval(n.right))
            elif isinstance(n, ast.UnaryOp) and type(n.op) in OPERATORS:
                return OPERATORS[type(n.op)](_eval(n.operand))
            raise ValueError("Unsupported operation")

        result = _eval(node)
        if isinstance(result, float) and result.is_integer():
            return int(result)
        return round(result, 4)
    except Exception:
        return None


class Brain:
    def __init__(self):
        productivity.set_speech_function(speech.speak)

    def process(self, raw_command):
        """Processes a single command. Returns True to continue, False to exit."""
        if not raw_command:
            return True

        wake_word = config.get("wake_word", "jarvis").lower()
        user_name = config.get("user_name", "Boss")

        c = raw_command.lower().strip()
        # Remove wake word if present at beginning
        if c.startswith(wake_word):
            c = c[len(wake_word):].strip()
        # Strip common courtesy prefixes
        c = re.sub(r"^(please|hey|ok|okay|could you|can you)\s+", "", c).strip()

        if not c:
            return True

        # --- 1. Exit & Sleep ---
        if c in ("exit", "quit", "bye", "goodbye", "stop", "go to sleep") or "goodbye" in c:
            speech.speak(f"Goodbye, {user_name}. Have a wonderful day.")
            return False

        # --- 2. System Power Actions ---
        if re.search(r"\b(shut ?down|turn off)\b.*\b(computer|pc|laptop|system)\b", c):
            if speech.confirm("Do you really want to shut down the computer?"):
                speech.speak("Shutting down in 15 seconds. Say cancel shutdown to abort.")
                system_tools.power_action("shutdown")
            else:
                speech.speak("Shutdown cancelled.")
            return True

        if re.search(r"\brestart\b.*\b(computer|pc|laptop|system)\b", c):
            if speech.confirm("Do you really want to restart the computer?"):
                speech.speak("Restarting the system in 15 seconds.")
                system_tools.power_action("restart")
            else:
                speech.speak("Restart cancelled.")
            return True

        if "cancel shutdown" in c:
            if system_tools.cancel_shutdown():
                speech.speak("Pending shutdown has been cancelled.")
            else:
                speech.speak("I can only cancel a pending shutdown on Windows.")
            return True

        if re.search(r"\block\b.*\b(computer|pc|laptop|screen|system)\b", c):
            speech.speak("Locking your screen.")
            system_tools.power_action("lock")
            return True

        if re.search(r"\bsleep\b.*\b(computer|pc|laptop|system)\b", c):
            speech.speak("Putting the system to sleep.")
            system_tools.power_action("sleep")
            return True

        # --- 3. System Telemetry & Volume ---
        if re.search(r"\b(system status|battery|cpu|ram|memory|specs|hardware)\b", c):
            status = system_tools.get_status()
            speech.speak(status)
            return True

        if "screenshot" in c:
            path = system_tools.take_screenshot()
            if path:
                speech.speak(f"Screenshot captured and saved to {os.path.basename(path)}.")
            else:
                speech.speak("I could not capture a screenshot right now.")
            return True

        m = re.search(r"\bvolume (up|down)|\b(mute|unmute)\b", c)
        if m:
            action = m.group(2) if m.group(2) else m.group(1)
            if system_tools.change_volume(action):
                speech.speak(f"Volume adjusted.")
            else:
                speech.speak("Volume control is unavailable.")
            return True

        m = re.match(r"^(?:close|kill|terminate)\s+(?:app\s+|program\s+)?(.+)", c)
        if m:
            target = m.group(1).strip()
            if system_tools.close_app(target):
                speech.speak(f"Closed {target}.")
            else:
                speech.speak(f"Could not find or close {target}.")
            return True

        # --- 4. Time, Date & Math ---
        if re.search(r"\b(what time is it|current time|the time)\b", c) or c == "time":
            curr_time = datetime.datetime.now().strftime("%I:%M %p").lstrip("0")
            speech.speak(f"It is {curr_time}.")
            return True

        if re.search(r"\b(date|what day is it|today's date)\b", c) or c == "date":
            curr_date = datetime.datetime.now().strftime("%A, %d %B %Y")
            speech.speak(f"Today is {curr_date}.")
            return True

        m = re.match(r"^(?:calculate|what is|compute)\s+([0-9\s\+\-\*\/\^\.\(\)]+)$", c)
        if m:
            res = safe_eval_math(m.group(1))
            if res is not None:
                speech.speak(f"The answer is {res}.")
                return True

        # --- 5. Weather & News ---
        if "weather" in c:
            m = re.search(r"weather(?:\s+(?:in|at|for))?\s*(.*)", c)
            city = m.group(1).strip() if m else ""
            report = web_tools.get_weather(city)
            if report:
                speech.speak(report)
            else:
                speech.speak("I couldn't fetch the weather right now.")
            return True

        if re.search(r"\b(news|headlines|what's happening)\b", c):
            speech.speak("Fetching the latest headlines.")
            headlines = web_tools.get_news(limit=3)
            if headlines:
                for i, hl in enumerate(headlines, 1):
                    speech.speak(f"Headline {i}: {hl}")
            else:
                speech.speak("No current headlines could be retrieved.")
            return True

        # --- 6. Notes ---
        if re.search(r"\b(show|read|get|what are|list|check)\b.*\bnotes?\b", c) or c in ("notes", "my notes", "show notes"):
            notes = productivity.get_notes(5)
            if notes:
                speech.speak(f"Here are your latest notes: " + ". ".join(notes))
            else:
                speech.speak("You have no notes saved.")
            return True

        if "clear notes" in c or "delete notes" in c:
            if speech.confirm("Are you sure you want to delete all notes?"):
                productivity.clear_notes()
                speech.speak("All notes have been cleared.")
            else:
                speech.speak("Action cancelled.")
            return True

        m = re.match(r"^(?:take a note|note down|note|remember|write down|save note)(?:\s+that)?\s+(.+)", c)
        if m:
            if productivity.add_note(m.group(1)):
                speech.speak("Note saved.")
            else:
                speech.speak("I was unable to save that note.")
            return True

        # --- 7. Timers & Reminders ---
        m = re.search(r"(?:set a timer for|timer for|remind me in)\s+(.+)", c)
        if m:
            raw_target = m.group(1)
            # Check if reminder message attached, e.g. "5 minutes to check oven"
            task_msg = "Time is up!"
            if "to " in raw_target:
                parts = raw_target.split("to ", 1)
                duration_str = parts[0].strip()
                task_msg = parts[1].strip()
            else:
                duration_str = raw_target.strip()

            secs = productivity.parse_duration(duration_str)
            if secs > 0:
                productivity.set_timer(secs, task_msg)
                speech.speak(f"Timer set for {duration_str}.")
            else:
                speech.speak("I couldn't understand the timer duration.")
            return True

        # --- 8. To-Do List & Tasks ---
        m = re.match(r"^(?:add to-?do|add task|create task|new task|todo|remind me to)\s+(.+)", c)
        if m:
            productivity.add_todo(m.group(1))
            speech.speak(f"Added to your to-do list: {m.group(1)}.")
            return True

        if re.search(r"\b(show|read|list|what are|what is|get|check)\b.*\b(to-?dos?|tasks?)\b", c) or c in ("tasks", "my tasks", "todo", "to-do", "todo list"):
            todos = productivity.get_todos()
            if todos:
                speech.speak("Your tasks: " + ", ".join(todos) + ".")
            else:
                speech.speak("Your to-do list is empty.")
            return True

        m = re.match(r"^(?:complete|finish|remove|delete|done with|clear)\s+(?:task|to-?do)?\s*(.+)", c)
        if m:
            if productivity.complete_todo(m.group(1)):
                speech.speak(f"Marked task as completed.")
            else:
                speech.speak(f"I couldn't find that task in your list.")
            return True

        # --- 9. Open Websites & Apps ---
        if c.startswith("open "):
            target = c[5:].strip()
            if web_tools.open_site(target):
                speech.speak(f"Opening {target}.")
            elif web_tools.open_app(target):
                speech.speak(f"Opening {target}.")
            else:
                speech.speak(f"I don't have a shortcut for {target}. You can add it in config.json.")
            return True

        # --- 10. Search & Play ---
        m = re.match(r"^(?:search|google)(?:\s+for)?\s+(.+)", c)
        if m:
            query = m.group(1)
            speech.speak(f"Searching Google for {query}.")
            web_tools.search_google(query)
            return True

        m = re.match(r"^play\s+(.+?)(?:\s+on youtube)?$", c)
        if m:
            query = m.group(1)
            speech.speak(f"Playing {query} on YouTube.")
            web_tools.play_youtube(query)
            return True

        # --- 11. Fun & Persona ---
        if "joke" in c:
            speech.speak(random.choice(JOKES))
            return True

        if re.match(r"^(hello|hi|hey|how are you|who are you)", c):
            speech.speak(f"Hello {user_name}! I am JARVIS, your personal desktop assistant. How can I assist you today?")
            return True

        if "clear chat" in c or "clear history" in c:
            ai.clear_history()
            speech.speak("Conversation history cleared.")
            return True

        if "help" in c or "what can you do" in c:
            speech.speak(
                "I can monitor system health, take screenshots, adjust volume, "
                "open applications and websites, set timers and reminders, manage notes and to-dos, "
                "report weather and news, search Google, play YouTube, and answer questions using AI."
            )
            return True

        # --- 12. Knowledge & AI Fallback ---
        reply = ai.ask(c)
        if reply:
            speech.speak(reply)
            return True

        m = re.match(r"^(?:who is|who was|what is|what are|tell me about|define)\s+(.+)", c)
        if m:
            summary = web_tools.wikipedia_summary(m.group(1))
            if summary:
                speech.speak(summary)
                return True

        # Final Fallback: search web
        speech.speak("Let me search that for you.")
        web_tools.search_google(c)
        return True


brain = Brain()
