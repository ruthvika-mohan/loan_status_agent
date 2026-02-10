# 🎤 AI Voice Agent for Loan Status Inquiries

An intelligent conversational AI agent for automated loan status inquiries, 
built with state machine architecture and LLM-powered intent recognition.

**[ Watch Demo Video](https://youtu.be/lT0n99LexpY)** | 
**[Full Documentation](https://industrious-ursinia-a33.notion.site/Loan-Status-Voice-Agent-2fbd805a3c2e80718153f72cb24b4622?pvs=143)**

---

##  Features

- 🎯 Caller ID detection with confirmation
- 💬 Natural language understanding via OpenAI GPT-4
- 📞 Multi-channel support (voice/text/DTMF)
- 🔄 Graceful error handling and agent handoff
- ⚡ Sub-2-second response times

---

## 🏗️ Architecture
```
User Input (Voice/Text)
    ↓
State Machine (JSON flows)
    ↓
LLM Intent Router (GPT-4)
    ↓
Action Handler (Phone lookup, etc.)
    ↓
Response (TTS/Text)
```

---

## 🚀 Quick Start

### **Setup**

```
git clone https://github.com/ruthvika-mohan/loan_status_agent/
cd loan-voice-agent
pip install -r requirements.txt
```

Create a .env file using the template:

```
cp .env.example .env
```

Add your API keys to .env:

```
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_CHAT_DEPLOYMENT=...
```

Start the backend:

```
uvicorn app.main:app --reload
```

Open voice_chat.html in your browser to start a voice conversation.


---

## 🎯 Use Cases

- Banking: Loan/account status inquiries
- Healthcare: Appointment confirmations
- Retail: Order status tracking
- Insurance: Claim status updates

---

## 📊 Technical Stack

### Current Implementation

**Backend**
- FastAPI (Python)
- Deterministic state-machine conversation engine

**AI / LLM**
- Azure OpenAI (GPT-4–class model)
- Bounded intent routing (no free-form generation)

**Voice Interface**
- Browser-native Web Speech API (STT/TTS)

**Frontend**
- HTML / CSS / JavaScript
- Streamlit for testing and development

### Planned / Extensible

- Twilio Voice (phone-based calls)
- Azure Speech Services (multi-language STT/TTS)
- Redis (distributed session management)

