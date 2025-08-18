# MERE AI Agent Phase 2

## 🤖 About
Personal Voice Assistant with Advanced AI Features - **완전 오픈소스, 비용 0원**

## 🏗️ Project Structure

```
mere/
├── src/mere/               # Main source code (NEW)
│   ├── api/               # FastAPI application
│   ├── services/          # AI services (STT, NLU, TTS)
│   ├── core/              # Business logic & database
│   └── models/            # Data models
├── tests/                 # All tests (organized)
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests 
│   └── e2e/              # End-to-end tests
├── backend/              # Docker & deployment
├── ios/                  # iOS SwiftUI app
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

## 🚀 Quick Start

### Backend (Docker)
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
```

### iOS App
```bash
# Open Xcode project
cd ios/MEREApp
open MEREApp.xcodeproj

# Run on iPhone simulator
```

### Testing
```bash
# Run E2E tests
python -m pytest tests/e2e/ -v

# Run specific test
PYTHONPATH=src python tests/e2e/test_pipeline_e2e.py
```

## ✅ Week 1 Achievements
- **iOS App**: Successfully running on iPhone 15 simulator
- **Voice Pipeline**: STT → NLU → Business Logic → TTS (85.7% success)
- **Response Time**: 1.90s average (goal: <3s ✅)
- **Architecture**: Production-ready Docker setup

## 🎯 Week 2 Goals (Current)
- **LangGraph**: State management for complex conversations
- **Google Calendar**: Real calendar integration
- **Offline Mode**: CoreData sync & local processing  
- **Advanced NLU**: Context awareness & confirmations

## 📊 Performance Metrics
- STT Accuracy: 95%+ (Whisper)
- NLU Accuracy: 95%+ (GPT-4)
- E2E Success Rate: 85.7% (12/14 scenarios)
- Average Response Time: 1.90 seconds

## 🛠️ Tech Stack
- **Backend**: Python 3.11+, FastAPI, PostgreSQL, Redis
- **AI/ML**: Whisper (STT), GPT-4 (NLU), Piper (TTS), LangGraph
- **iOS**: SwiftUI, Combine, AVFoundation
- **Infrastructure**: Docker, nginx, Langfuse, DeepEval