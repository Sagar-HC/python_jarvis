import os
import platform
import sys
import time

from core.config import config, OS

# Speech & Audio dependencies
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
    import subprocess
    from speech_recognition.audio import get_flac_converter, AudioData

    def _safe_get_flac_data(self, convert_rate=None, convert_width=None):
        wav_data = self.get_wav_data(convert_rate, convert_width)
        flac_converter = get_flac_converter()
        if os.name == "nt":
            startup_info = subprocess.STARTUPINFO()
            startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup_info.wShowWindow = subprocess.SW_HIDE
        else:
            startup_info = None

        process = subprocess.Popen(
            [
                flac_converter,
                "--stdout",
                "--totally-silent",
                "--best",
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # Fixes Windows WinError 50 handle duplication error
            startupinfo=startup_info,
        )
        flac_data, _ = process.communicate(wav_data)
        return flac_data

    AudioData.get_flac_data = _safe_get_flac_data
except ImportError:
    sr = None

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    sd = None
    np = None

import re

if OS == "Windows":
    try:
        import winsound
    except ImportError:
        winsound = None
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        pythoncom = None
        win32com = None
else:
    winsound = None
    pythoncom = None
    win32com = None

def clean_for_speech(text):
    if not text:
        return ""
    # Strip markdown formatting so text sounds natural when spoken
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    t = re.sub(r"\*([^*]+)\*", r"\1", text)
    t = re.sub(r"`([^`]+)`", r"\1", text)
    t = re.sub(r"#+\s*", "", t)
    t = re.sub(r"^\s*[-*•]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


class SoundDeviceMicrophone(sr.AudioSource if sr is not None else object):
    """
    Seamless AudioSource wrapper for sounddevice, providing full compatibility
    with SpeechRecognition (recognizer.listen, adjust_for_ambient_noise, VAD).
    Works on all Python versions including Python 3.14 without PyAudio!
    """
    class SDStream:
        def __init__(self, device=None, sample_rate=16000, chunk_size=1024):
            self.device = device
            self.sample_rate = sample_rate
            self.chunk_size = chunk_size
            self.stream = sd.InputStream(
                device=device,
                channels=1,
                samplerate=sample_rate,
                dtype="int16",
                blocksize=chunk_size
            )
            self.stream.start()

        def read(self, size):
            data, _ = self.stream.read(size)
            return data.tobytes()

        def close(self):
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass

    def __init__(self, device=None, sample_rate=16000, chunk_size=1024):
        self.device = device
        self.SAMPLE_RATE = sample_rate
        self.SAMPLE_WIDTH = 2  # 16-bit PCM
        self.CHUNK = chunk_size
        self.stream = None

    def __enter__(self):
        self.stream = self.SDStream(
            device=self.device,
            sample_rate=self.SAMPLE_RATE,
            chunk_size=self.CHUNK
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stream is not None:
            self.stream.close()
            self.stream = None


class SpeechSystem:
    def __init__(self):
        self.text_mode = False
        self.engine = None
        self.recognizer = None
        self.status_callback = None
        self.transcript_callback = None
        self._calibrated = False

        self._init_tts()
        self._init_stt()

    def set_callbacks(self, status_cb=None, transcript_cb=None):
        self.status_callback = status_cb
        self.transcript_callback = transcript_cb

    def update_status(self, status):
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception:
                pass

    def _init_tts(self):
        self.sapi_voice = None
        if OS == "Windows" and win32com is not None:
            try:
                if pythoncom:
                    pythoncom.CoInitialize()
                self.sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
                self.sapi_voice.Rate = 1
                vol = int(config.get("voice_volume", 1.0) * 100)
                self.sapi_voice.Volume = max(10, min(100, vol))
            except Exception:
                self.sapi_voice = None

        if pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
                rate = config.get("voice_rate", 180)
                vol = config.get("voice_volume", 1.0)
                self.engine.setProperty("rate", rate)
                self.engine.setProperty("volume", vol)
            except Exception:
                self.engine = None

    def _init_stt(self):
        if sr is not None:
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = 1.6  # Generous pause threshold (1.6s) so sentences don't cut off early
            self.recognizer.non_speaking_duration = 0.8
            self.recognizer.phrase_threshold = 0.25
            self.recognizer.dynamic_energy_threshold = False  # Fixed threshold prevents speech cut-offs

    def get_microphone_source(self):
        """Returns a working SpeechRecognition AudioSource (PyAudio or SoundDevice)."""
        device_idx = config.get("microphone_device", None)
        # Try PyAudio standard microphone if available
        if sr is not None:
            try:
                # Test PyAudio init
                mic = sr.Microphone(device_index=device_idx)
                # Quick test if PyAudio is really functional
                with mic as _:
                    pass
                return mic
            except Exception:
                pass

        # Fall back to SoundDeviceMicrophone
        if sd is not None and sr is not None:
            return SoundDeviceMicrophone(device=device_idx, sample_rate=16000)

        return None

    def calibrate(self, duration=1.0):
        """Calibrates microphone for ambient room noise."""
        if self.text_mode or self.recognizer is None:
            return

        source = self.get_microphone_source()
        if source is None:
            return

        try:
            print("[Calibrating microphone for background noise...]")
            self.update_status("calibrating")
            with source as s:
                self.recognizer.adjust_for_ambient_noise(s, duration=duration)
            self._calibrated = True
            print(f"[Microphone calibrated. Energy threshold: {int(self.recognizer.energy_threshold)}]")
            self.update_status("idle")
        except Exception as e:
            print(f"[Microphone calibration warning: {e}]")
            self.update_status("idle")

    def play_chime(self, freq=800, dur_ms=80):
        if config.get("sound_feedback", True) and winsound is not None:
            try:
                winsound.Beep(freq, dur_ms)
            except Exception:
                pass

    def speak(self, text):
        clean_text = clean_for_speech(text)
        if not clean_text:
            return

        user_facing = f"JARVIS: {clean_text}"
        print(user_facing)
        if self.transcript_callback:
            try:
                self.transcript_callback("jarvis", clean_text)
            except Exception:
                pass

        self.update_status("speaking")
        spoken = False

        # 1. Windows Native SAPI.SpVoice (Direct, crisp, and thread-safe)
        if OS == "Windows" and win32com is not None:
            try:
                if pythoncom:
                    pythoncom.CoInitialize()
                voice = self.sapi_voice or win32com.client.Dispatch("SAPI.SpVoice")
                voice.Speak(clean_text)
                spoken = True
            except Exception:
                pass

        # 2. pyttsx3 fallback
        if not spoken and self.engine is not None:
            try:
                self.engine.say(clean_text)
                self.engine.runAndWait()
                spoken = True
            except Exception:
                pass

        # 3. PowerShell SpeechSynthesizer fallback
        if not spoken and OS == "Windows":
            try:
                safe = clean_text.replace('"', "'").replace("\n", " ")
                cmd = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe}")'
                import subprocess
                subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, timeout=12)
                spoken = True
            except Exception:
                pass

        self.update_status("idle")

    def listen_once(self, timeout=7, phrase_limit=20, prompt_message="Listening..."):
        """Return what the user said in lowercase, or '' if nothing was recognized."""
        if self.text_mode:
            try:
                self.update_status("waiting_input")
                text = input("You: ").strip()
                if self.transcript_callback and text:
                    self.transcript_callback("user", text)
                self.update_status("idle")
                return text.lower()
            except (EOFError, KeyboardInterrupt):
                return "exit"

        source = self.get_microphone_source()
        if source is None:
            print("[Error: No microphone device available. Falling back to text mode.]")
            self.text_mode = True
            return self.listen_once()

        # Auto-calibrate once if not yet calibrated
        if not self._calibrated:
            self.calibrate(duration=0.8)

        self.update_status("listening")
        self.play_chime(700, 70)
        print(f"[{prompt_message}]")

        try:
            with source as s:
                audio = self.recognizer.listen(s, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            self.update_status("idle")
            return ""
        except Exception as e:
            # print(f"[Listen error: {e}]")
            self.update_status("idle")
            return ""

        self.update_status("processing")
        try:
            recognized = self.recognizer.recognize_google(audio).strip()
            print(f"You (Voice): {recognized}")
            if self.transcript_callback and recognized:
                self.transcript_callback("user", recognized)
            self.update_status("idle")
            return recognized.lower()
        except sr.UnknownValueError:
            # Speech was detected but words could not be discerned
            self.update_status("idle")
            return ""
        except sr.RequestError:
            print("(Speech recognition network error - check your internet connection)")
            self.update_status("idle")
            return ""
        except Exception:
            self.update_status("idle")
            return ""

    def confirm(self, question):
        self.speak(question + " Say yes or no, or type yes/no.")
        heard = self.listen_once(timeout=6)
        return heard.startswith(("yes", "yeah", "yep", "sure", "confirm", "y", "ok", "okay"))


speech = SpeechSystem()
