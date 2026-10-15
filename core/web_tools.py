import json
import re
import subprocess
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET

from core.config import config, OS

class WebTools:
    @staticmethod
    def http_get(url, timeout=8):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 JARVIS Desktop Assistant"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @classmethod
    def get_weather(cls, city=""):
        city_query = (city or config.get("default_city", "")).strip()
        encoded = urllib.parse.quote(city_query) if city_query else ""
        url = f"https://wttr.in/{encoded}?format=%C,+%t,+feels+like+%f"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                report = resp.read().decode("utf-8", errors="replace").strip()
            loc_str = f" in {city_query}" if city_query else ""
            return f"Weather{loc_str}: {report}"
        except Exception:
            return None

    @classmethod
    def get_news(cls, limit=4):
        """Fetch latest top headlines from Google News RSS feed."""
        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        try:
            raw_xml = cls.http_get(url, timeout=10)
            root = ET.fromstring(raw_xml)
            items = root.findall(".//item")
            headlines = []
            for item in items[:limit]:
                title = item.find("title")
                if title is not None and title.text:
                    # Clean source attribution e.g. "Headline - Source Name"
                    clean_title = re.sub(r"\s+-\s+[^-]+$", "", title.text).strip()
                    headlines.append(clean_title)
            return headlines
        except Exception:
            return []

    @classmethod
    def wikipedia_summary(cls, topic):
        title = urllib.parse.quote(topic.strip().replace(" ", "_"))
        try:
            data = json.loads(cls.http_get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"))
            if data.get("type") == "disambiguation" or not data.get("extract"):
                return None
            sentences = re.split(r"(?<=[.!?])\s+", data["extract"])
            return " ".join(sentences[:2])
        except Exception:
            return None

    @classmethod
    def open_site(cls, target):
        sites = config.get("sites", {})
        target_lower = target.lower().strip()

        if target_lower in sites:
            webbrowser.open(sites[target_lower])
            return True

        if "." in target_lower or target_lower.startswith("http"):
            url = target_lower if target_lower.startswith("http") else f"https://{target_lower}"
            webbrowser.open(url)
            return True

        return False

    @classmethod
    def open_app(cls, app_name):
        apps = config.get("apps", {})
        target_lower = app_name.lower().strip()

        entry = apps.get(target_lower)
        if not entry:
            return False

        target = entry.get(OS)
        if not target:
            return False

        try:
            if OS == "Windows":
                safe_target = f'"{target}"' if not (target.startswith('"') and target.endswith('"')) else target
                subprocess.Popen(f'start "" {safe_target}', shell=True)
            elif OS == "Darwin":
                subprocess.Popen(["open", "-a", target])
            else:
                subprocess.Popen(target.split())
            return True
        except Exception:
            return False

    @staticmethod
    def search_google(query):
        url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
        webbrowser.open(url)

    @staticmethod
    def play_youtube(query):
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
        webbrowser.open(url)


web_tools = WebTools()
