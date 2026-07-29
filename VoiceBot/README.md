# VoiceBot

VoiceBot is a real-time AI voice assistant built using the Pipecat framework.  
It supports live voice conversations, document-based knowledge retrieval, and natural AI responses using speech-to-text, large language models, and text-to-speech.

The bot connects through a browser and allows users to speak with the AI assistant in real time.

---

## Features

- Real-time voice conversation
- Speech-to-Text transcription
- AI response generation using LLM
- Text-to-Speech voice responses
- PDF knowledge base embedding
- Retrieval-Augmented Generation (RAG) using ChromaDB
- Runs inside WSL (Windows Subsystem for Linux)
- Built with Python 3.11.14
- Uses Pipecat voice pipeline

---

## Tech Stack

### Speech-to-Text (STT)
- Deepgram STT

### Text-to-Speech (TTS)
- Cartesia TTS

### LLM Models
- OpenAI GPT-4o-mini

### Vector Database
- ChromaDB

### Embeddings Model
- all-MiniLM-L6-v2 (Sentence Transformers)

### Framework
- Pipecat Voice AI Pipeline

### Python Version
- Python 3.11.14

### Environment
- WSL (Windows Subsystem for Linux)

---

## Project Structure

```
VoiceBot/
│
├── bot.py
├── prompt.py
├── calendar_service.py
├── .env
├── requirements.txt
└── README.md
```

---

## How It Works

1. PDF document is loaded.
2. PDF is split into chunks.
3. Chunks are embedded using sentence transformer embeddings.
4. Embeddings are stored in ChromaDB.
5. During conversation, user questions are converted into vector search queries.
6. Relevant document chunks are retrieved.
7. LLM generates answers based only on retrieved content.
8. Response is converted to speech and played back to the user.

---

## Setup Instructions (WSL)

### 1. Create Virtual Environment

```bash
python3.11.14 -m venv voicevenv
```

### 2. Activate Virtual Environment

```bash
source voicevenv/bin/activate
```

### 3. Start ChromaDB Server

```bash
chroma run --host 0.0.0.0 --port 8000
```

### 4. Run the Bot

```bash
python bot.py
```

---

## Environment Variables (.env)

Create a `.env` file and add:

```
OPENAI_API_KEY=
DEEPGRAM_API_KEY=
CARTESIA_API_KEY=

CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=voicebot_docs

file_path=/path/to/your/pdf
```

---

## Pipeline Flow

```
Microphone Input
      ↓
Speech-to-Text (Deepgram)
      ↓
LLM (OpenAI GPT-4o-mini)
      ↓
Knowledge Retrieval (ChromaDB)
      ↓
Text-to-Speech (Cartesia)
      ↓
Speaker Output
```

---

## Run Command Summary

```
python3.11.14 -m venv voicevenv
source voicevenv/bin/activate
chroma run --host 0.0.0.0 --port 8000
python bot.py
```

---

## Notes

- First run may take time to load models.
- Make sure ChromaDB is running before starting the bot.
- Ensure PDF file path is correctly set in `.env`.
- Runs best inside WSL environment.
- Uses real-time audio streaming via Pipecat transport.

---

## Project Name

VoiceBot – Real-Time AI Voice Assistant with RAG
