# 🎙️ VoiceBot OpenAI (Speech-to-AI Conversational System)

A Python-based real-time voice assistant that captures speech, converts it into text, sends it to an OpenAI-compatible LLM, and responds using both text and speech output.

It integrates **Speech Recognition (STT)**, **OpenAI Chat API**, and **Text-to-Speech (TTS)** with a thread-safe architecture for continuous interaction.

---

# 🧠 System Design Overview

## 🎯 Objective

To design a real-time conversational voice assistant that:

- Captures user voice input 🎤  
- Converts speech → text using SpeechRecognition  
- Sends text to OpenAI API 🤖  
- Receives AI-generated response  
- Converts response → speech 🔊  
- Runs continuously until user exits

# 🏗️ 2. Architectural Design


User Voice 🎤
      ↓
Microphone Input (SpeechRecognition)
      ↓
Speech-to-Text (Google API / Sphinx fallback)
      ↓
Transcribed Text
      ↓
OpenAI Chat Completion API 🤖
      ↓
AI Response Text
      ↓
Thread-Safe TTS Queue
      ↓
pyttsx3 Voice Engine 🔊
      ↓
Speaker Output 🔊

---

## ⚙️ Functional Requirements

- Real-time microphone input
- Speech-to-text conversion
- AI response generation via OpenAI API
- Text-to-speech audio output
- Continuous conversational loop
- Voice-based exit commands (`quit`, `exit`, `stop`)

---

## ⚙️ Non-Functional Requirements

- Low-latency response pipeline
- Thread-safe audio processing
- Fault-tolerant API handling
- Offline fallback for STT (Sphinx)
- Modular and extensible architecture

---

---

## 🧱 Component Breakdown

### 1. 🎤 Speech Recognition Module
- Captures audio from microphone
- Converts speech → text
- Example libraries:
  - `SpeechRecognition`
  - `Whisper (OpenAI)`

---

### 2. 🤖 OpenAI Processing Module
- Sends user text to OpenAI API
- Handles conversation context
- Returns intelligent response

---

### 3. 🔊 Text-to-Speech (TTS) Module
- Converts AI response text → spoken audio
- Uses:
  - `pyttsx3` (offline)
  - or `gTTS` (online)

---

### 4. 🧵 Threading & Queue System
- Ensures non-blocking audio playback
- Handles async TTS execution safely

🚀 5. Tech Stack

 **AI Model:** OpenAI GPT API
- **Speech-to-Text:** SpeechRecognition / Whisper
- **Text-to-Speech:** pyttsx3 / gTTS
- **Concurrency:** threading + queue

# 📦 6. Installation

```bash
git clone https://github.com/your-repo/voicebot-openai.git
cd voicebot-openai

pip install -r requirements.txt


7. Run the Application

export OPENAI_API_KEY="your-api-key"
streamlit run app.py

8. Key Features
🎤 Voice-based interaction
🤖 AI-powered responses
