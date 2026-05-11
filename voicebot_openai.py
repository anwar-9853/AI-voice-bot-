
"""
voicebot_openai.py

Adds OpenAI API integration so recognized speech text is sent to OpenAI (chat/completions).
The assistant's text response is displayed and also spoken via the thread-safe TTS queue.

Usage:
    export OPENAI_API_KEY="sk-..."   # (Windows: setx OPENAI_API_KEY "sk-...")
    python voicebot_openai.py

Notes:
 - This script supports two client styles: the newer `from openai import OpenAI; client = OpenAI()`
   and the legacy `import openai; openai.api_key = ...` usage. It will try the modern client first.
 - Replace MODEL_NAME with a model you have access to (e.g. "gpt-3.5-turbo").
"""

import os
import time
import traceback
import sys

# reuse core voice bot components by copying the minimal necessary code from previous file
import threading
import queue

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

# ---------------------------
# OpenAI client helper (supports modern and legacy clients)
# ---------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
MODEL_NAME = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")


client_modern = None
client_legacy = None

def init_openai_client():
    global client_modern, client_legacy
    if OPENAI_API_KEY is None:
        print("Warning: OPENAI_API_KEY is not set. OpenAI calls will fail.", file=sys.stderr)
    try:
        # Try modern client: from openai import OpenAI; client = OpenAI()
        from openai import OpenAI
        client_modern = OpenAI(api_key=OPENAI_API_KEY, base_url="https://openrouter.ai/api/v1") if OPENAI_API_KEY else OpenAI()
        print("Using modern OpenAI client (OpenAI()).")
        return
    except Exception:
        client_modern = None

    try:
        import openai
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
        client_legacy = openai
        openai.base_url = "https://openrouter.ai/api/v1"

        print("Using legacy openai module (openai.ChatCompletion).")
    except Exception:
        client_legacy = None

def ask_openai_chat(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    #  Send prompt to OpenAI and return assistant text.
   # Tries modern client first, falls back to legacy ChatCompletion call.
    if client_modern is None and client_legacy is None:
        init_openai_client()
    try:
        if client_modern is not None:
            # Modern client: client.chat.completions.create(...)
            response = client_modern.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
            )
            # response.choices[0].message.content or response.choices[0].message['content'] depending on client
            try:
                return response.choices[0].message.content
            except Exception:
                # alternative attribute access
                return response.choices[0].message['content']
        elif client_legacy is not None:
            # legacy: openai.ChatCompletion.create(...)
            response = client_legacy.ChatCompletion.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
            )
            return response.choices[0].message['content']
        else:
            return "OpenAI client not available."
    except Exception as e:
        print("OpenAI API call failed:", e, file=sys.stderr)
        traceback.print_exc()
        return f"OpenAI API error: {e}"


def ask_openai_chat(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    try:
        response = client_modern.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
        )

        return response.choices[0].message.content

    except Exception as e:
        print("OpenAI API call failed:", e, file=sys.stderr)
        return f"OpenAI API error: {e}"
# ---------------------------
# Thread-safe TTS (same as before)
# ---------------------------
TTS_RATE = 150 
_tts_queue = queue.Queue()
_tts_thread = None
_tts_stop_event = threading.Event()

def _tts_worker():
    if pyttsx3 is None:
        print("pyttsx3 not installed. TTS disabled.", file=sys.stderr)
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', TTS_RATE)
    except Exception as e:
        print("Failed to initialize pyttsx3 in TTS thread:", e, file=sys.stderr)
        traceback.print_exc()
        return
    while not _tts_stop_event.is_set():
        try:
            item = _tts_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        if item is None:
            break
        try:
            text = item
            if not text:
                continue
            engine.say(text)
            engine.runAndWait()
        except Exception:
            print("Error during TTS:", traceback.format_exc(), file=sys.stderr)
    try:
        engine.stop()
    except Exception:
        pass

def start_tts_thread():
    global _tts_thread
    if _tts_thread is None or not _tts_thread.is_alive():
        _tts_stop_event.clear()
        _tts_thread = threading.Thread(target=_tts_worker, name="TTS-Thread", daemon=True)
        _tts_thread.start()

def stop_tts_thread():
    _tts_stop_event.set()
    try:
        _tts_queue.put_nowait(None)
    except Exception:
        pass
    if _tts_thread is not None:
        _tts_thread.join(timeout=2)

def speak(text: str):
    if pyttsx3 is None:
        print("[TTS disabled] " + text)
        return
    start_tts_thread()
    _tts_queue.put(text)

# ---------------------------
# Speech recognition (same pattern)
# ---------------------------
_recognizer = sr.Recognizer() if sr is not None else None
_microphone = None

def init_audio_resources():
    global _microphone
    if sr is None:
        print("SpeechRecognition library not available. STT disabled.", file=sys.stderr)
        return
    if _microphone is not None:
        return
    try:
        _microphone = sr.Microphone()
    except Exception as e:
        print("Microphone initialization failed:", e, file=sys.stderr)
        traceback.print_exc()
        _microphone = None

def listen_once(timeout: float = 5, phrase_time_limit: float = 8) -> str:
    init_audio_resources()
    if _microphone is None or _recognizer is None:
        return ""
    with _microphone as source:
        try:
            _recognizer.adjust_for_ambient_noise(source, duration=0.6)
            print("Listening... (speak now)")
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return ""
        except Exception as e:
            print("Error while listening:", e)
            traceback.print_exc()
            return ""
    try:
        text = _recognizer.recognize_google(audio)
        print("Recognized:", text)
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print("API request failed (online recognizer may be unavailable):", e)
        try:
            text = _recognizer.recognize_sphinx(audio)
            print("Sphinx recognized:", text)
            return text
        except Exception as e2:
            print("Pocketsphinx fallback failed:", e2)
            return ""
    except Exception as e:
        print("Unexpected error recognizing speech:", e)
        traceback.print_exc()
        return ""

# ---------------------------
# Main loop: send user text to OpenAI, display and speak response
# ---------------------------

def main_loop():
    print("Starting voice bot with OpenAI integration. Say 'quit' to stop.")
    init_openai_client()
    start_tts_thread()
    try:
        while True:
            user_text = listen_once()
            if not user_text:
                continue
            if user_text.strip().lower() in ("quit", "exit", "stop"):
                speak("Goodbye. Shutting down.")
                break
            print("Sending to OpenAI:", user_text)
            reply = ask_openai_chat(user_text)
            print("Assistant:", reply)
            speak(reply)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        stop_tts_thread()
        print("Exited cleanly.")

if __name__ == "__main__":
    main_loop()
