# 🤖 Hana - Personal AI Assistant Bot

<div align="center">

![Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

*A personal AI assistant with voice capabilities, powered by LangGraph and Google Gemini*

</div>

---

## 📖 About Hana

**Hana** is a personal AI assistant bot currently in development with a focus on creating a unique persona and personality. The goal is to build an AI assistant capable of:

- 🗣️ **Voice Interaction** - Natural voice-based communication
- 🧠 **Contextual Memory** - Remember and understand conversation context
- 🎭 **Unique Persona** - Develop distinctive personality and style
- 🔧 **Tool Integration** - Integrate various tools and extensible capabilities

## ✨ Features

### 🎤 Voice Capabilities
- **Speech-to-Text (STT)**: English speech recognition
- **Text-to-Speech (TTS)**: Natural voice synthesis with Kitten TTS
- **Real-time Processing**: Real-time processing and response

### 🛠️ Technical Stack
- **Backend**: FastAPI + Python 3.11
- **AI Framework**: LangChain + LangGraph
- **LLM**: Google Gemini 2.5 Flash
- **Memory**: Redis (conversation history)
- **Database**: PostgreSQL (vector store)
- **Voice**: RealtimeSTT + Kitten TTS
- **WebSocket**: Real-time bidirectional communication

## 🚀 Getting Started

### Prerequisites

- Python 3.11
- Conda
- Redis Server
- PostgreSQL
- CUDA-capable GPU (recommended for TTS/STT)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/nguyendao16/hana-bot-langgraph.git
cd hana-bot-langgraph
```

2. **Setup environment**
```bash
# Automatic setup (recommended)
.\setup_environment.ps1

# Or manual setup
conda env create -f hana_conda_environment.yml
conda activate hana
pip install torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

3. **Configure environment variables**
```bash
# Copy .env.example to .env and fill in your credentials
cp .env.example .env
```

Required variables:
```env
GOOGLE_API_KEY=your_google_api_key
REDIS_URL=redis://:@localhost:6379/0
PG_HOST=localhost
PG_DBNAME=vectorDB
PG_USER=your_username
PG_PASSWORD=your_password
STT_SERVER_URL=ws://localhost:8765
TTS_SERVER_URL=ws://localhost:8766
```

### Running Hana

Start the services in separate terminals:

**Terminal 1 - TTS Server:**
```bash
conda activate hana
python voice/hana_tts.py
```

**Terminal 2 - Main Bot:**
```bash
conda activate hana
python main.py
```

**Terminal 3 - STT Server (Optional for voice input):**
```bash
conda activate hana
python voice/stt.py
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Hana Bot                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │   STT    │─────▶│ Chatbot  │─────▶│   TTS    │        │
│  │  Server  │      │  (Main)  │      │  Server  │        │
│  └──────────┘      └──────────┘      └──────────┘        │
│       │                  │                  │              │
│   WebSocket          FastAPI          WebSocket           │
│       │                  │                  │              │
│       ▼                  ▼                  ▼              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │ Realtime │      │LangGraph │      │  Kitten  │        │
│  │   STT    │      │  Agent   │      │   TTS    │        │
│  └──────────┘      └──────────┘      └──────────┘        │
│                         │                                  │
│                    ┌────┴────┐                            │
│                    │         │                            │
│              ┌─────▼───┐ ┌──▼──────┐                     │
│              │  Redis  │ │Postgres │                     │
│              │ Memory  │ │ Vector  │                     │
│              └─────────┘ └─────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🎭 Persona Development (In Progress)

Hana đang trong giai đoạn phát triển persona. Các đặc điểm đang được xây dựng:

### 🧩 Personality Quirks (To be developed)
- Personal preferences
- Unique expressions
- Response patterns
- Emotional intelligence
- Cultural awareness

> **Note**: Persona development is an ongoing process. Contributions and suggestions are welcome!

## 📁 Project Structure

```
hana-bot-langgraph/
├── agent/
│   ├── agent.py              # LangGraph agent configuration
│   ├── prompt_template.txt   # System prompt & persona
│   └── utils/
│       ├── memory.py         # Redis memory management
│       ├── nodes.py          # LangGraph nodes
│       ├── tools.py          # RAG and custom tools
│       └── state.py          # Agent state definition
├── voice/
│   ├── hana_tts.py          # TTS WebSocket server
│   ├── stt.py               # STT WebSocket server
│   └── README_TTS.md        # TTS documentation
├── Embedding/
│   └── xlsx_Embedding.py    # Document embedding utilities
├── main.py                   # Main FastAPI application
├── setup_environment.ps1     # Auto setup script
└── hana_conda_environment.yml
```

## 🔧 API Endpoints

### Chat Endpoint
```bash
POST http://localhost:8200/chat
Content-Type: application/json

{
  "message": "Hello Hana!",
  "thread_id": "user-123"
}
```

### WebSocket (STT/TTS)
- **STT Server**: `ws://localhost:8765` - Send audio, receive English transcription
- **TTS Server**: `ws://localhost:8766` - Send text, receive audio

## 🛣️ Roadmap

### Phase 1: Core Functionality ✅
- [x] Basic LangGraph agent
- [x] Memory management
- [x] TTS/STT integration
- [x] WebSocket communication
- [x] FastAPI backend

### Phase 2: Persona Development 🚧 (Current)
- [ ] Define core personality traits
- [ ] Create consistent response patterns
- [ ] Develop emotional intelligence
- [ ] Add persona-specific knowledge base
- [ ] Implement personality-driven decision making

### Phase 3: Advanced Features 📋
- [ ] Multi-language support
- [ ] Context-aware responses
- [ ] Proactive suggestions
- [ ] Custom tools integration

### Phase 4: Optimization 📋
- [ ] Response time optimization
- [ ] Memory efficiency
- [ ] Scalability improvements
- [ ] Advanced memory
- [ ] Fine-tuning persona

## 🤝 Contributing

Contributions are welcome! Especially for:
- Persona development suggestions
- Voice model improvements

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangChain & LangGraph** - AI framework
- **Google Gemini** - Language model
- **Kitten TTS** - Text-to-speech engine
- **RealtimeSTT** - Speech recognition
- **FastAPI** - Web framework

## 📧 Contact

For questions or suggestions about Hana's development:
- GitHub: [@nguyendao16](https://github.com/nguyendao16)
- Repository: [hana-bot-langgraph](https://github.com/nguyendao16/hana-bot-langgraph)

---

<div align="center">

**✨ Hana is evolving... Stay tuned for updates! ✨**

Made with ❤️ by Nguyen Dao

</div>
