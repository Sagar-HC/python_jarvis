"""
Microphone Diagnostic Tool for JARVIS
Tests connected input audio devices, ambient noise levels, and speech recognition.
"""

import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from core.speech import speech, SoundDeviceMicrophone
import sounddevice as sd
import speech_recognition as sr
import numpy as np

def run_diagnostics():
    print("=" * 55)
    print("      JARVIS MICROPHONE DIAGNOSTIC UTILITY")
    print("=" * 55)

    print("\n1. Detected Input Audio Devices:")
    devices = sd.query_devices()
    default_input = sd.default.device[0] if sd.default.device else None
    
    for idx, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0:
            is_default = " [DEFAULT]" if idx == default_input else ""
            print(f"   [{idx}] {d['name']} (Channels: {d['max_input_channels']}, Rate: {d['default_samplerate']}){is_default}")

    print("\n2. Testing Audio Stream & Ambient Noise...")
    try:
        source = speech.get_microphone_source()
        if source is None:
            print("   [!] Error: No working microphone source could be created!")
            return

        with source as s:
            print("   Listening to room noise for 1 second...")
            speech.recognizer.adjust_for_ambient_noise(s, duration=1.0)
            threshold = int(speech.recognizer.energy_threshold)
            print(f"   [OK] Ambient calibration successful!")
            print(f"   [OK] Dynamic Energy Threshold set to: {threshold}")

    except Exception as e:
        print(f"   [!] Stream test failed: {e}")
        return

    print("\n3. Testing Speech Capture (Say 'Testing one two three' or 'Jarvis')...")
    print("   [Speak into your microphone now - 5 seconds window]")
    
    try:
        with source as s:
            audio = speech.recognizer.listen(s, timeout=5, phrase_time_limit=5)
            raw_len = len(audio.get_raw_data())
            print(f"   [OK] Audio captured successfully ({raw_len} bytes)")

        print("   Sending audio to speech recognition service...")
        recognized = speech.recognizer.recognize_google(audio)
        print(f"\n   [*] Recognized Speech: \"{recognized}\"")
        print("\n=> Result: Your microphone and speech recognition are working properly!")

    except sr.WaitTimeoutError:
        print("   [!] No speech detected within 5 seconds (timed out).")
        print("   Tip: Check that your microphone is not muted in Windows Settings > Sound.")
    except sr.UnknownValueError:
        print("   [!] Sound was detected, but words could not be recognized.")
        print("   Tip: Speak closer to your microphone or adjust microphone volume.")
    except sr.RequestError as e:
        print(f"   [!] Speech service unreachable: {e}. Check your internet connection.")
    except Exception as e:
        print(f"   [!] Error during capture: {e}")

    print("\n" + "=" * 55)

if __name__ == "__main__":
    run_diagnostics()
