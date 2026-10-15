import datetime
import os
import platform
import subprocess
import sys

from core.config import OS

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None


class SystemTools:
    @staticmethod
    def get_status():
        """Return formatted string of CPU, RAM, Disk, and Battery."""
        if psutil is None:
            return "psutil library is not available to read system status."

        parts = []
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            parts.append(f"CPU is at {cpu:.0f}%")
        except Exception:
            pass

        try:
            mem = psutil.virtual_memory()
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            parts.append(f"RAM is at {mem.percent:.0f}% ({used_gb:.1f} of {total_gb:.1f} GB)")
        except Exception:
            pass

        try:
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            free_gb = disk.free / (1024 ** 3)
            parts.append(f"Disk has {free_gb:.1f} GB free")
        except Exception:
            pass

        try:
            bat = psutil.sensors_battery()
            if bat:
                status = "charging" if bat.power_plugged else "on battery"
                parts.append(f"Battery is at {bat.percent:.0f}%, {status}")
        except Exception:
            pass

        return ", ".join(parts) + "." if parts else "System metrics currently unavailable."

    @staticmethod
    def take_screenshot():
        """Save a screenshot and return the absolute path."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures")
        if not os.path.exists(pictures_dir):
            pictures_dir = os.path.expanduser("~")

        filename = f"screenshot_{timestamp}.png"
        target_path = os.path.join(pictures_dir, filename)

        if pyautogui is not None:
            try:
                pyautogui.screenshot().save(target_path)
                return target_path
            except Exception:
                pass

        if ImageGrab is not None:
            try:
                img = ImageGrab.grab()
                img.save(target_path)
                return target_path
            except Exception:
                pass

        return None

    @staticmethod
    def change_volume(action):
        """action can be 'up', 'down', 'mute'."""
        if pyautogui is not None:
            if action == "mute":
                pyautogui.press("volumemute")
            elif action == "up":
                for _ in range(5):
                    pyautogui.press("volumeup")
            elif action == "down":
                for _ in range(5):
                    pyautogui.press("volumedown")
            return True
        elif OS == "Windows":
            # Windows PowerShell volume shortcut or nircmd fallback
            return False
        return False

    @staticmethod
    def power_action(action):
        """Execute shutdown, restart, lock, or sleep."""
        commands = {
            "shutdown": {
                "Windows": ["shutdown", "/s", "/t", "15"],
                "Darwin": ["osascript", "-e", 'tell app "System Events" to shut down'],
                "Linux": ["systemctl", "poweroff"]
            },
            "restart": {
                "Windows": ["shutdown", "/r", "/t", "15"],
                "Darwin": ["osascript", "-e", 'tell app "System Events" to restart'],
                "Linux": ["systemctl", "reboot"]
            },
            "lock": {
                "Windows": ["rundll32.exe", "user32.dll,LockWorkStation"],
                "Darwin": ["pmset", "displaysleepnow"],
                "Linux": ["loginctl", "lock-session"]
            },
            "sleep": {
                "Windows": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                "Darwin": ["pmset", "sleepnow"],
                "Linux": ["systemctl", "suspend"]
            }
        }
        entry = commands.get(action, {}).get(OS)
        if entry:
            subprocess.Popen(entry)
            return True
        return False

    @staticmethod
    def cancel_shutdown():
        if OS == "Windows":
            subprocess.Popen(["shutdown", "/a"])
            return True
        return False

    @staticmethod
    def close_app(process_name):
        """Terminate a running process by name."""
        if psutil is None:
            return False

        proc_query = process_name.lower().replace(".exe", "")
        terminated = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower()
                if proc_query in name:
                    proc.terminate()
                    terminated += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return terminated > 0


system_tools = SystemTools()
