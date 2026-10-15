"""
JARVIS - Desktop Voice & AI Assistant for Windows / macOS / Linux

Run:
    python jarvis.py            # Voice mode (say "Jarvis, <command>")
    python jarvis.py --text     # Interactive text terminal (no mic required)
    python jarvis.py --gui      # Sleek modern desktop GUI

Optional AI keys (set in environment or .env):
    GEMINI_API_KEY / GOOGLE_API_KEY
    ANTHROPIC_API_KEY
    OPENAI_API_KEY
    (or run Ollama locally for free offline AI: ollama run llama3)
"""

import argparse
import datetime
import os
import sys

# Configure UTF-8 encoding safely for Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.brain import brain
from core.config import config
from core.speech import speech

BANNER = r"""
  ================================================
     _   _   ____ __     __ ___  ____  
    | | / \ |  _ \\ \   / /|_ _|/ ___| 
 _  | |/ _ \| |_) |\ \ / /  | | \___ \ 
| |_| / ___ \  _ <  \ V /   | |  ___) |
 \___/_/   \_\_| \_\ \_/   |___||____/ 
       Desktop Voice & AI Assistant
  ================================================
"""

def parse_arguments():
    parser = argparse.ArgumentParser(description="JARVIS Desktop Assistant")
    parser.add_argument("--text", action="store_true", help="Run in text CLI mode (no microphone needed)")
    parser.add_argument("--gui", action="store_true", help="Launch modern desktop window GUI")
    parser.add_argument("--provider", type=str, help="AI provider (gemini, claude, openai, ollama, offline)")
    parser.add_argument("--user", type=str, help="Custom user name")
    return parser.parse_args()


def main():
    args = parse_arguments()

    if args.provider:
        config.set("ai_provider", args.provider)
    if args.user:
        config.set("user_name", args.user)

    # Launch GUI if requested
    if args.gui:
        from gui.app import launch_gui
        launch_gui()
        return

    print(BANNER)
    user_name = config.get("user_name", "Boss")
    wake_word = config.get("wake_word", "jarvis").lower()

    # Determine mode
    if args.text:
        speech.text_mode = True
    else:
        mic_source = speech.get_microphone_source()
        if speech.recognizer is None or mic_source is None:
            print("[Warning] No microphone library or device available. Defaulting to text mode.")
            speech.text_mode = True
        else:
            speech.calibrate(duration=0.8)

    # Greeting
    hour = datetime.datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"

    if speech.text_mode:
        speech.speak(f"{greeting}, {user_name}. Text mode is active. Type a command, or 'exit' to quit.")
    else:
        speech.speak(f"{greeting}, {user_name}. Voice mode is active. Say '{wake_word}' followed by your command.")

    # Main Command Loop
    while True:
        try:
            heard = speech.listen_once(prompt_message="Listening for voice...")
            if not heard:
                continue

            if speech.text_mode:
                command = heard
            else:
                # OG Behavior: Only trigger when 'jarvis' (or phonetic close 'javis') is spoken
                matched_alias = None
                for alias in [wake_word, "javis"]:
                    if alias in heard:
                        matched_alias = alias
                        break

                if not matched_alias:
                    # Did not say Jarvis -> stay OG, remain silent and continue listening
                    continue

                # User said Jarvis! Extract the command
                command = heard.split(matched_alias, 1)[1].strip()
                if not command:
                    speech.speak(f"Yes, {user_name}?")
                    command = speech.listen_once(timeout=7, phrase_limit=20, prompt_message="Listening for command...")
                    if not command:
                        continue

            should_continue = brain.process(command)
            if not should_continue:
                break

        except KeyboardInterrupt:
            speech.speak(f"\nGoodbye, {user_name}.")
            break
        except Exception as e:
            print(f"[Error] {e}")
            speech.speak("Sorry, something unexpected occurred while handling that request.")


if __name__ == "__main__":
    main()
