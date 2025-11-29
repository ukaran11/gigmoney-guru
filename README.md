# 💰 GigMoney Guru

> **AI-Powered Financial Coach for Gig Workers in India**

GigMoney Guru is an intelligent financial management platform designed specifically for gig workers with irregular incomes. It uses a multi-agent AI system to provide personalized financial guidance, smart budget allocation, micro-advances, and goal tracking.

## 🌟 Features

### Core Features
- **Smart Bucket Allocation**: Auto-allocate earnings into Essentials, Flex, Goals, and Emergency buckets
- **Income Pattern Analysis**: AI-powered detection of income trends and patterns
- **Cashflow Forecasting**: 7-day rolling forecast with visual charts
- **Micro-Advances**: Low-interest (1%) emergency advances based on earning patterns
- **Goal Tracking**: Set and track savings goals with progress visualization
- **AI Chat Coach**: Bilingual (English/Hinglish) conversational financial guidance
- **Risk Assessment**: Real-time obligation risk scoring and alerts

### Multi-Agent AI System
The platform uses **8 specialized AI agents** orchestrated via LangGraph:

1. **Income Pattern Agent** - Analyzes income stability and trends
2. **Obligation Risk Agent** - Assesses upcoming payment risks
3. **Cashflow Planner Agent** - Forecasts 7-day cash positions
4. **Bucket Allocation Agent** - Optimizes daily income allocation
5. **Micro-Advance Agent** - Determines advance eligibility
6. **Goal Scenario Agent** - Simulates goal achievement paths
7. **Conversation Agent** - Generates bilingual coaching messages
8. **Explainability Agent** - Provides human-readable decision explanations

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **MongoDB Atlas** - Cloud database with Beanie ODM
- **LangGraph** - Multi-agent orchestration
- **OpenAI API** - LLM for intelligent analysis
- **Matplotlib** - Forecast chart generation

### Frontend
- **React 18** + **TypeScript** - Modern UI framework
- **Vite** - Fast build tool
- **Tailwind CSS** - Utility-first styling
- **Zustand** - State management
- **Recharts** - Data visualization

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB Atlas account
- OpenAI API key

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env
# Edit .env with your credentials

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access the Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
GigMoneyGuru/
├── backend/
│   ├── app/
│   │   ├── agents/          # 8 AI agents
│   │   ├── api/             # FastAPI routes
│   │   ├── llm/             # OpenAI client & prompts
│   │   ├── models/          # MongoDB Beanie models
│   │   ├── orchestrator/    # LangGraph agent graph
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # DB connection
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── components/      # Reusable UI components
    │   ├── pages/           # Page components
    │   ├── store/           # Zustand stores
    │   ├── lib/             # API client & utilities
    │   └── App.tsx          # Root component
    ├── package.json
    └── vite.config.ts
```

## 🎮 Demo: Ravi's Week

The platform includes a demo scenario following "Ravi", a multi-platform gig worker in Bangalore:

1. Register/Login to the app
2. Click **"Load Ravi's Data"** to seed demo data
3. Click **"Run AI"** to trigger the agent graph
4. Explore:
   - Dashboard with buckets and income
   - Chat with the AI coach
   - Track savings goals
   - Request micro-advances
5. Simulate different scenarios:
   - Normal day
   - Rainy day (lower rideshare, higher delivery)
   - Festival day (surge pricing)
   - Payday (weekly payouts)

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token

### Dashboard
- `GET /api/state/today` - Get today's financial state
- `GET /api/state/forecast` - Get 7-day forecast

### Agents
- `POST /api/agent/run-daily` - Run full agent graph
- `POST /api/agent/run/{agent_name}` - Run single agent

### Goals
- `GET /api/goals` - List goals
- `POST /api/goals` - Create goal
- `POST /api/goals/{id}/contribute` - Add to goal

### Advances
- `GET /api/advances/available` - Check available advance
- `POST /api/advances/request` - Request advance
- `POST /api/advances/{id}/repay` - Mark as repaid

### Chat
- `POST /api/chat/message` - Send message to AI coach
- `GET /api/chat/history` - Get chat history


## 📝 Environment Variables

```env
# MongoDB Atlas
MONGODB_URI=mongodb+srv://...

# OpenAI
OPENAI_API_KEY=sk-...

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# App
DEBUG=true
```

## 🤝 Team

Built for the hackathon with ❤️

## 📄 License

MIT License

---

**GigMoney Guru** - *Helping gig workers thrive, one earning at a time* 💰
