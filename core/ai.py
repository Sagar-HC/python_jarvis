import json
import os
import urllib.parse
import urllib.request
from core.config import config

class AIClient:
    def __init__(self):
        self.chat_history = []
        self.system_prompt = (
            "You are JARVIS, an intelligent, accurate, and truthful desktop voice assistant. "
            "Always provide direct, strictly factual, and truthful answers. "
            "Never invent facts, hallucinate, or extrapolate fictional information. "
            "Treat each user question as an independent inquiry unless the user explicitly refers to prior conversation. "
            "Reply concisely in one or two clear, plain sentences suitable for being spoken aloud without markdown symbols."
        )

    def detect_provider(self):
        pref = config.get("ai_provider", "auto").lower()
        if pref != "auto":
            return pref

        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            return "gemini"
        if os.environ.get("ANTHROPIC_API_KEY"):
            return "claude"
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"

        # Check local Ollama
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    return "ollama"
        except Exception:
            pass

        return "none"

    def ask(self, question):
        provider = self.detect_provider()
        if provider == "none" or provider == "offline":
            return None

        reply = None
        if provider == "gemini":
            reply = self._ask_gemini(question)
        elif provider == "claude":
            reply = self._ask_claude(question)
        elif provider == "openai":
            reply = self._ask_openai(question)
        elif provider == "ollama":
            reply = self._ask_ollama(question)

        return reply

    def _get_recent_context_pair(self):
        """Returns at most the last (user, assistant) exchange to avoid topic bleeding."""
        if len(self.chat_history) >= 2:
            prev_user = self.chat_history[-2]
            prev_bot = self.chat_history[-1]
            if prev_user.get("role") == "user" and prev_bot.get("role") == "assistant":
                return [prev_user, prev_bot]
        return []

    def _ask_gemini(self, question):
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None

        user_model = config.get("ai_model")
        candidate_models = []
        if user_model:
            candidate_models.append(user_model)
        candidate_models.extend([
            "gemini-flash-lite-latest",
            "gemini-2.5-flash-lite",
            "gemini-flash-latest",
            "gemini-pro-latest"
        ])

        contents = []
        for turn in self._get_recent_context_pair():
            role = "user" if turn["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": turn["content"]}]})
        contents.append({"role": "user", "parts": [{"text": question}]})

        payload = {
            "system_instruction": {"parts": [{"text": self.system_prompt}]},
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 200, "temperature": 0.2}
        }
        body = json.dumps(payload).encode("utf-8")

        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    url,
                    data=body,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    self._record_history(question, text)
                    return text
            except Exception:
                continue

        return None

    def _ask_claude(self, question):
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            return None

        model = config.get("ai_model") or "claude-3-5-sonnet-20241022"
        messages = list(self._get_recent_context_pair())
        messages.append({"role": "user", "content": question})

        body = json.dumps({
            "model": model,
            "max_tokens": 200,
            "system": self.system_prompt,
            "messages": messages,
            "temperature": 0.2
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                reply = json.loads(resp.read().decode("utf-8"))["content"][0]["text"].strip()
            self._record_history(question, reply)
            return reply
        except Exception:
            return None

    def _ask_openai(self, question):
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return None

        model = config.get("ai_model") or "gpt-4o-mini"
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._get_recent_context_pair())
        messages.append({"role": "user", "content": question})

        body = json.dumps({
            "model": model,
            "max_tokens": 200,
            "messages": messages,
            "temperature": 0.2
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                reply = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
            self._record_history(question, reply)
            return reply
        except Exception:
            return None

    def _ask_ollama(self, question):
        base_url = config.get("ollama_url", "http://localhost:11434")
        model = config.get("ollama_model", "llama3")

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self._get_recent_context_pair())
        messages.append({"role": "user", "content": question})

        body = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2}
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data.get("message", {}).get("content", "").strip()
                if reply:
                    self._record_history(question, reply)
                    return reply
        except Exception:
            pass
        return None

    def _record_history(self, user_text, bot_text):
        self.chat_history.append({"role": "user", "content": user_text})
        self.chat_history.append({"role": "assistant", "content": bot_text})
        if len(self.chat_history) > 6:
            self.chat_history = self.chat_history[-6:]

    def clear_history(self):
        self.chat_history.clear()


ai = AIClient()
