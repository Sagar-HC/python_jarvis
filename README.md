# ⚡ JARVIS - Desktop Voice & AI Assistant

A fast, responsive, and extensible desktop voice & AI assistant for **Windows, macOS, and Linux**.

Built in Python with native support for **Voice Mode**, **Interactive CLI**, and a modern **Dark Desktop GUI**.

---

## 🚀 Quick Start

### 1. Requirements & Installation
Ensure you have Python 3.10+ installed. Install the core requirements:

```bash
pip install -r requirements.txt
```

*(Note: On Windows, `sounddevice`, `pyttsx3`, `SpeechRecognition`, `psutil`, and `pyautogui` provide native mic and speech synthesis without requiring external C compilation).*

---

### 2. Launching JARVIS

You can launch JARVIS in 3 different modes:

#### 🎙️ Voice Mode (Default)
Say **"Jarvis"** followed by your command (e.g., *"Jarvis, what's the weather in New York?"*):
```bash
python jarvis.py
```

#### ⌨️ Interactive Text Mode
Type commands in your terminal without needing a microphone:
```bash
python jarvis.py --text
```

#### 🖥️ Desktop GUI Mode
Launch a modern dark-mode desktop assistant window with quick action buttons, live chat log, and voice toggle:
```bash
python jarvis.py --gui
```

---

## 🧠 Supported Commands & Capabilities

JARVIS can execute natural language voice or text commands across a wide range of tasks:

### 📊 System Telemetry & Controls
| Command | Description |
| :--- | :--- |
| `system status` / `battery` / `specs` | Checks CPU usage, RAM, disk space, and battery level |
| `take a screenshot` / `screenshot` | Captures screen and saves it into your Pictures directory |
| `volume up` / `volume down` / `mute` | Controls system master audio volume |
| `close <app>` / `kill <app>` | Terminates a running application (e.g. `close notepad`) |
| `lock screen` / `lock computer` | Instantly locks your workstation |
| `shut down computer` / `restart computer` | Safely schedules shutdown/restart (with confirmation) |
| `cancel shutdown` | Cancels any pending scheduled shutdown (Windows) |

### 📝 Notes, Reminders & To-Dos
| Command | Description |
| :--- | :--- |
| `take a note <text>` / `remember that <text>` | Saves a timestamped note to `jarvis_notes.txt` |
| `read notes` / `show notes` | Reads out your 5 most recent notes |
| `clear notes` | Deletes all saved notes (asks for confirmation) |
| `set a timer for <duration>` | Sets a background timer (e.g., `set a timer for 5 minutes`) |
| `remind me in <duration> to <task>` | Background reminder alert (e.g., `remind me in 30 seconds to stretch`) |
| `add to do <task>` / `todo <task>` | Adds an item to your to-do list (`jarvis_todo.json`) |
| `show my tasks` / `list to do` | Reads out pending to-do items |
| `complete task <task>` | Marks a task as completed |

### 🌐 Web, News & Weather
| Command | Description |
| :--- | :--- |
| `weather` / `weather in <city>` | Live weather and temperature report via `wttr.in` |
| `news` / `latest headlines` | Fetches top breaking news headlines from RSS feed |
| `search <query>` / `google <query>` | Performs a Google search in your default web browser |
| `play <song/video> on youtube` | Searches and plays content on YouTube |
| `open <app>` | Launches desktop apps (`chrome`, `notepad`, `vs code`, `calculator`, `spotify`, etc.) |
| `open <website>` | Opens bookmarked websites or any `.com`/`.org` domain directly |

### 🧮 Calculations & Knowledge
| Command | Description |
| :--- | :--- |
| `calculate <expression>` | Safe arithmetic calculator (e.g. `calculate 45 * 12 + 100`) |
| `what time is it` / `today's date` | Reports current time and formatted date |
| `who is <person>` / `what is <concept>` | Instant Wikipedia 2-sentence summary |
| `joke` / `tell me a joke` | Tells a programmer / tech joke |

---

## 🤖 AI Integration (Optional)

JARVIS features **multi-provider LLM intelligence**. When you ask a general question that isn't a direct system command, JARVIS queries your configured AI:

1. **Google Gemini**: Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`)
2. **Anthropic Claude**: Set `ANTHROPIC_API_KEY`
3. **OpenAI ChatGPT**: Set `OPENAI_API_KEY`
4. **Local Ollama** (100% Free & Offline): Install [Ollama](https://ollama.ai) and run `ollama run llama3`. JARVIS automatically detects local Ollama!

You can configure keys either by setting environment variables or by creating a `.env` file from `.env.example`:
```env
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

*If no AI key is configured, JARVIS gracefully falls back to Wikipedia summaries and web search!*

---

## ⚙️ Customization (`config.json`)

All assistant parameters can be customized in `config.json`:

```json
{
    "wake_word": "jarvis",
    "user_name": "Boss",
    "voice_rate": 180,
    "voice_volume": 1.0,
    "default_city": "London",
    "ai_provider": "auto"
}
```

- **`wake_word`**: Change your assistant's trigger name (e.g., `"friday"`, `"computer"`).
- **`user_name`**: The name JARVIS addresses you by.
- **`apps`**: Add your own custom desktop application shortcuts and executable paths.
- **`sites`**: Add your favorite bookmarks.
