import datetime
import queue
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from core.brain import brain
from core.config import config
from core.speech import speech

COLOR_BG = "#0f172a"        # Dark slate
COLOR_CARD = "#1e293b"      # Card background
COLOR_ACCENT = "#38bdf8"    # Bright cyan/sky
COLOR_USER = "#a855f7"      # Violet
COLOR_BOT = "#38bdf8"       # Cyan
COLOR_TEXT = "#f8fafc"      # White / light grey
COLOR_MUTED = "#94a3b8"     # Muted grey
COLOR_SUCCESS = "#22c55e"   # Green
COLOR_WARNING = "#f59e0b"   # Amber
COLOR_SPEAKING = "#ec4899"  # Pink

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS - Desktop Assistant")
        self.root.geometry("820x660")
        self.root.minsize(680, 520)
        self.root.configure(bg=COLOR_BG)

        self.msg_queue = queue.Queue()
        self.is_listening = False
        self.current_status = "idle"

        # Wire up speech callbacks
        speech.set_callbacks(
            status_cb=self._on_speech_status,
            transcript_cb=self._on_transcript
        )

        self._build_ui()
        self._poll_queue()

        # Initial Welcome
        user_name = config.get("user_name", "Boss")
        self.root.after(300, lambda: self._add_message(
            "JARVIS",
            f"Online and ready, {user_name}. How can I assist you today? You can type commands below or click the microphone to speak."
        ))

    def _build_ui(self):
        # 1. Header Frame
        header = tk.Frame(self.root, bg=COLOR_CARD, padx=20, pady=14)
        header.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            header,
            text="⚡ JARVIS AI ASSISTANT",
            font=("Segoe UI", 15, "bold"),
            fg=COLOR_ACCENT,
            bg=COLOR_CARD
        )
        title_label.pack(side=tk.LEFT)

        # Status Badge
        self.status_badge = tk.Label(
            header,
            text="● SYSTEM READY",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_SUCCESS,
            bg=COLOR_CARD,
            padx=10,
            pady=4
        )
        self.status_badge.pack(side=tk.RIGHT)

        # 2. Quick Action Bar
        quick_frame = tk.Frame(self.root, bg=COLOR_BG, padx=16, pady=8)
        quick_frame.pack(fill=tk.X)

        quick_actions = [
            ("📊 System Status", "system status"),
            ("⛅ Weather", "weather"),
            ("📰 Latest News", "news"),
            ("📸 Screenshot", "screenshot"),
            ("📝 View Notes", "read notes"),
            ("❓ Help", "help")
        ]

        for label, cmd in quick_actions:
            btn = tk.Button(
                quick_frame,
                text=label,
                font=("Segoe UI", 9),
                fg=COLOR_TEXT,
                bg=COLOR_CARD,
                activebackground=COLOR_ACCENT,
                activeforeground=COLOR_BG,
                relief=tk.FLAT,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda c=cmd: self._send_command_async(c)
            )
            btn.pack(side=tk.LEFT, padx=4)

        # 3. Chat / Transcript Display
        chat_frame = tk.Frame(self.root, bg=COLOR_BG, padx=16, pady=6)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            padx=14,
            pady=14,
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Tag configurations
        self.chat_display.tag_configure("time", foreground=COLOR_MUTED, font=("Segoe UI", 8))
        self.chat_display.tag_configure("user_hdr", foreground=COLOR_USER, font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("user_body", foreground=COLOR_TEXT, font=("Segoe UI", 10))
        self.chat_display.tag_configure("bot_hdr", foreground=COLOR_BOT, font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("bot_body", foreground=COLOR_TEXT, font=("Segoe UI", 10))

        # 4. Input Area
        input_frame = tk.Frame(self.root, bg=COLOR_CARD, padx=16, pady=12)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Voice Button
        self.mic_btn = tk.Button(
            input_frame,
            text="🎙️ Voice",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_BG,
            bg=COLOR_ACCENT,
            activebackground="#0284c7",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._toggle_voice_input
        )
        self.mic_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Text Entry
        self.entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            bg="#0f172a",
            fg=COLOR_TEXT,
            insertbackground=COLOR_ACCENT,
            relief=tk.FLAT,
            bd=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self._on_send_click())
        self.entry.focus_set()

        # Send Button
        send_btn = tk.Button(
            input_frame,
            text="Send ➤",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg="#334155",
            activebackground=COLOR_ACCENT,
            activeforeground=COLOR_BG,
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._on_send_click
        )
        send_btn.pack(side=tk.RIGHT)

    def _on_speech_status(self, status):
        self.msg_queue.put(("status", status))

    def _on_transcript(self, role, text):
        self.msg_queue.put(("transcript", (role, text)))

    def _poll_queue(self):
        try:
            while not self.msg_queue.empty():
                kind, data = self.msg_queue.get_nowait()
                if kind == "status":
                    self._update_status_ui(data)
                elif kind == "transcript":
                    role, text = data
                    display_role = "JARVIS" if role.lower() == "jarvis" else config.get("user_name", "You")
                    self._add_message(display_role, text)
        except Exception:
            pass
        self.root.after(100, self._poll_queue)

    def _update_status_ui(self, status):
        self.current_status = status
        if status == "listening":
            self.status_badge.config(text="● LISTENING...", fg=COLOR_ACCENT)
            self.mic_btn.config(text="🔴 Stop", bg="#ef4444")
        elif status == "processing":
            self.status_badge.config(text="● THINKING...", fg=COLOR_WARNING)
            self.mic_btn.config(text="🎙️ Voice", bg=COLOR_ACCENT)
        elif status == "speaking":
            self.status_badge.config(text="● SPEAKING...", fg=COLOR_SPEAKING)
        else:
            self.status_badge.config(text="● SYSTEM READY", fg=COLOR_SUCCESS)
            self.mic_btn.config(text="🎙️ Voice", bg=COLOR_ACCENT)

    def _add_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        t_now = datetime.datetime.now().strftime("%H:%M:%S")

        is_bot = (sender == "JARVIS")
        hdr_tag = "bot_hdr" if is_bot else "user_hdr"
        body_tag = "bot_body" if is_bot else "user_body"
        prefix = "⚡ " if is_bot else "👤 "

        self.chat_display.insert(tk.END, f"[{t_now}] ", "time")
        self.chat_display.insert(tk.END, f"{prefix}{sender}\n", hdr_tag)
        self.chat_display.insert(tk.END, f"{message}\n\n", body_tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def _on_send_click(self):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, tk.END)
        self._send_command_async(cmd)

    def _send_command_async(self, cmd_text):
        def _worker():
            brain.process(cmd_text)

        threading.Thread(target=_worker, daemon=True).start()

    def _toggle_voice_input(self):
        if self.current_status == "listening":
            return

        def _voice_worker():
            heard = speech.listen_once(timeout=6, phrase_limit=8)
            if heard:
                brain.process(heard)

        threading.Thread(target=_voice_worker, daemon=True).start()


def launch_gui():
    root = tk.Tk()
    app = JarvisGUI(root)
    root.mainloop()
