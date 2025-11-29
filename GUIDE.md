# 📚 GigMoney Guru - Comprehensive User & Developer Guide

> **Version:** 1.0  
> **Last Updated:** November 2025  
> **Your AI-Powered Financial Coach for Gig Workers**

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Getting Started](#-getting-started)
3. [Dashboard Overview](#-dashboard-overview)
4. [Money Buckets System](#-money-buckets-system)
5. [Recording Transactions](#-recording-transactions)
6. [Managing Obligations](#-managing-obligations)
7. [Savings Goals](#-savings-goals)
8. [Micro-Advances](#-micro-advances)
9. [AI Financial Coach](#-ai-financial-coach)
10. [Agent Modes Explained](#-agent-modes-explained)
11. [Charts & Analytics](#-charts--analytics)
12. [Technical Architecture](#-technical-architecture)
13. [API Reference](#-api-reference)
14. [Troubleshooting](#-troubleshooting)

---

## 🎯 Introduction

### What is GigMoney Guru?

GigMoney Guru is an **AI-powered financial management application** specifically designed for gig workers in India who face the challenge of irregular income. Think of it as having a **personal CFO in your pocket** that:

- 📊 **Tracks** your earnings across multiple platforms (Uber, Ola, Swiggy, Zomato, etc.)
- 💰 **Allocates** your money automatically to different buckets (rent, EMI, fuel, savings)
- 🔮 **Predicts** potential cash shortfalls before they happen
- 💡 **Advises** you in friendly Hinglish (Hindi + English) without judgment
- 🚀 **Offers** micro-advances when you're short on cash

### Who is it for?

Our primary persona is **Ravi** - a gig worker in Mumbai who:
- Works across multiple platforms (ride-hailing, food delivery, quick commerce)
- Has volatile income (weekend spikes, mid-week dips, seasonal changes)
- Has recurring obligations (rent, EMIs, fuel, school fees)
- Lives with constant anxiety: "Will I have enough at month-end?"

### The Problem We Solve

| Pain Point | GigMoney Guru Solution |
|------------|----------------------|
| "I don't know how much I can safely spend" | Real-time "Safe to Spend" calculation |
| "I get surprised by EMI dates" | Proactive alerts 3-7 days before due dates |
| "I fall into payday loan traps" | Transparent micro-advances with 1% fee |
| "Budgeting apps don't understand gig income" | AI trained on irregular income patterns |
| "Financial advice feels judgmental" | Friendly Hinglish coaching without shame |

---

## 🚀 Getting Started

### Prerequisites

**For Users:**
- A modern web browser (Chrome, Firefox, Edge, Safari)
- Mobile or desktop device

**For Developers:**
- Node.js 18+ and npm/pnpm
- Python 3.10+
- MongoDB 6.0+
- OpenAI API key

### Installation

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your MONGODB_URI and OPENAI_API_KEY

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### First Login

1. Open `http://localhost:5173` in your browser
2. Click **Register** to create a new account
3. Enter your name, phone number, and password
4. You'll be taken to the Dashboard

### Loading Demo Data

To experience all features with sample data:

1. Click the **"Seed Demo Data"** button on the Dashboard
2. This loads "Ravi's Week" - a pre-configured scenario with:
   - 14 days of income history
   - Multiple expense patterns
   - Active obligations (rent, EMI)
   - Savings goals

---

## 📊 Dashboard Overview

The Dashboard is your financial command center:

```
┌─────────────────────────────────────────────────────────┐
│  🏠 GigMoney Guru                         [Logout]      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  Today's    │ │   Safe to   │ │  Upcoming   │       │
│  │  Earnings   │ │   Spend     │ │  Bills      │       │
│  │  ₹2,450     │ │   ₹1,200    │ │  3 due soon │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                         │
│  Money Buckets                    [+ Add Income/Expense]│
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │🏠 Rent │ │🏍️ EMI  │ │⛽ Fuel │ │💰 Save │          │
│  │₹5,200  │ │₹2,100  │ │₹800   │ │₹1,500 │          │
│  │▓▓▓▓░░░ │ │▓▓▓▓▓░░ │ │▓▓▓░░░░│ │▓▓░░░░░│          │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
│                                                         │
│  🤖 AI Insights          [🚀Enhanced] [🧠ReAct] [⚡Fast]│
│  ┌─────────────────────────────────────────────────┐   │
│  │ "Bhai, aaj ka earning achha hai! ₹500 rent mein │   │
│  │  daal diya, ₹200 fuel mein. ₹1,200 safely spend │   │
│  │  kar sakte ho!"                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  📈 Charts Dashboard                        [Expand]    │
│  [Cashflow] [Buckets] [Income] [Expenses] [Risk]       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Dashboard Elements

| Element | Description |
|---------|-------------|
| **Today's Earnings** | Sum of all income recorded today |
| **Safe to Spend** | Money you can spend without affecting obligations |
| **Upcoming Bills** | Obligations due in the next 7 days |
| **Money Buckets** | Visual cards showing each bucket's balance and progress |
| **AI Insights** | Latest recommendations from the AI coach |
| **Agent Mode Buttons** | Switch between different AI modes |
| **Charts** | Visual analytics of your financial health |

---

## 💰 Money Buckets System

### What are Buckets?

Buckets are virtual "envelopes" where your money is allocated for specific purposes. When you earn money, it automatically flows into buckets based on priority and rules.

### Default Buckets

| Bucket | Icon | Purpose | Default Allocation |
|--------|------|---------|-------------------|
| **Kiraya (Rent)** | 🏠 | Monthly rent payment | 25% |
| **Bike EMI** | 🏍️ | Vehicle loan payment | 15% |
| **Tax Savings** | 📋 | Quarterly tax reserve | 5% |
| **Fuel/Petrol** | ⛽ | Daily fuel expenses | 10% |
| **Emergency Fund** | 🛡️ | Unexpected expenses | 10% |
| **Bachat (Savings)** | 💰 | General savings | 10% |
| **Safe to Spend** | 🎯 | Discretionary spending | Remainder |

### How Allocation Works

```
Income: ₹1,000
    │
    ├──► ₹250 → Rent (25%)
    ├──► ₹150 → EMI (15%)
    ├──► ₹50  → Tax (5%)
    ├──► ₹100 → Fuel (10%)
    ├──► ₹100 → Emergency (10%)
    ├──► ₹100 → Savings (10%)
    └──► ₹250 → Safe to Spend (remaining)
```

### Smart Allocation Features

1. **Priority-based**: High-priority buckets (rent, EMI) get funded first
2. **Risk-aware**: If an obligation is due soon, its bucket gets 30% extra allocation
3. **Target-aware**: Buckets that reach their target get reduced allocation (30%)
4. **AI-adjusted**: The Enhanced agent can override allocations based on context

---

## 📝 Recording Transactions

### Adding Income

1. Click **"+ Add Income"** button on Dashboard
2. Fill in:
   - **Amount**: How much you earned
   - **Source**: Platform name (Uber, Ola, Swiggy, etc.)
   - **Date/Time**: When you earned it
3. Click **Save**
4. The AI automatically allocates money to buckets

**What happens behind the scenes:**
```
Income Added: ₹2,000 from Uber
    │
    ├── Proactive Agent triggers
    ├── Buckets updated based on allocation rules
    ├── Risk assessment runs
    └── AI generates insight message
```

### Adding Expenses

1. Click **"+ Add Expense"** button
2. Fill in:
   - **Amount**: How much you spent
   - **Category**: Type of expense (food, fuel, entertainment, etc.)
   - **Primary Bucket**: Which bucket to deduct from
3. Click **Save**

### Cascade Deduction System

If your expense exceeds the primary bucket's balance, the system **cascades** to other buckets:

```
Expense: ₹500 from "discretionary"
Discretionary Balance: ₹200

Cascade Priority:
1. Discretionary (₹200) ✓ Used ₹200
2. Flex           (₹0)  - Empty
3. Fuel           (₹150) ✓ Used ₹150
4. Savings        (₹100) ✓ Used ₹100
5. Emergency      (₹50)  ✓ Used ₹50
                  ─────────────────
                  Total:    ₹500 ✓
```

**Warning System:**
- ⚠️ **Yellow Warning**: Using emergency or savings buckets
- 🔴 **Red Warning**: Using rent/EMI/tax buckets (reserved for obligations)

---

## 📋 Managing Obligations

### What are Obligations?

Obligations are recurring bills that **must** be paid - rent, EMIs, subscriptions, school fees, etc.

### Adding an Obligation

1. Click **"+ Add Obligation"** on Dashboard
2. Fill in:
   - **Name**: e.g., "Bike EMI"
   - **Amount**: Monthly amount
   - **Due Day**: Day of month (1-31)
   - **Frequency**: Monthly, Weekly, One-time
   - **Linked Bucket**: Which bucket pays for this

### Obligation Risk Assessment

The AI calculates risk for each obligation:

| Risk Level | Meaning | Visual |
|------------|---------|--------|
| 🟢 **Low** | Bucket has enough money | Green badge |
| 🟡 **Medium** | Might be short, need attention | Yellow badge |
| 🔴 **High** | Likely shortfall, action needed | Red badge |

### Proactive Alerts

The system automatically alerts you:
- **7 days before**: "Rent due in 7 days, ₹8,000 needed"
- **3 days before**: "EMI due in 3 days, you're ₹1,000 short!"
- **Day before**: "URGENT: Bill due tomorrow!"

---

## 🎯 Savings Goals

### Creating a Goal

1. Navigate to **Goals** page
2. Click **"+ New Goal"**
3. Enter:
   - **Name**: e.g., "New Phone"
   - **Emoji**: Pick an icon
   - **Target Amount**: e.g., ₹15,000
   - **Target Date**: When you want to achieve it
   - **Priority**: Low, Medium, High

### Goal Tracking

Each goal shows:
- **Progress Bar**: Visual progress percentage
- **Current Amount**: How much saved so far
- **Daily Target**: How much to save per day
- **Days Remaining**: Time until target date
- **On Track?**: Whether you'll meet the goal

### What-If Scenarios

Explore different scenarios:

| Scenario | Description |
|----------|-------------|
| **Extra Hours** | "What if I work 2 extra hours on weekends?" |
| **Reduce Expenses** | "What if I cut eating out by ₹500/week?" |
| **Skip Days** | "What if I take 2 days off next week?" |

---

## 💸 Micro-Advances

### What are Micro-Advances?

When you're short on cash for an upcoming obligation, GigMoney Guru can offer a small advance against your future earnings. It's like borrowing from your future self!

### How It Works

```
Situation: Rent (₹8,000) due in 3 days
           Rent bucket has: ₹7,000
           Shortfall: ₹1,000

AI Proposes:
┌─────────────────────────────────────────┐
│ 💡 Micro-Advance Offer                  │
│                                         │
│ Principal:      ₹1,000                  │
│ Fee (1%):       ₹10                     │
│ Total Repay:    ₹1,010                  │
│                                         │
│ Repay When: Sunday (4 days)             │
│ From: Weekend earnings                  │
│                                         │
│ [Accept] [Decline] [Learn More]         │
└─────────────────────────────────────────┘
```

### Guardrails (Responsible Lending)

| Rule | Limit |
|------|-------|
| Maximum Advance | 40% of average weekly income |
| Active Advances | Only 1 at a time |
| Minimum Amount | ₹500 |
| Maximum Amount | ₹5,000 |
| Fee | 1% (transparent, no hidden charges) |

### Advance Statuses

| Status | Meaning |
|--------|---------|
| **Pending** | Offered but not yet accepted |
| **Active** | Accepted, waiting for repayment |
| **Repaid** | Successfully paid back |
| **Overdue** | Past repayment date |

---

## 🤖 AI Financial Coach

### Chat Interface

The Chat page provides a conversational interface with your AI financial coach:

```
┌─────────────────────────────────────────┐
│  💬 Chat with Guru                      │
├─────────────────────────────────────────┤
│                                         │
│  🤖 Guru: "Namaste bhai! Aaj main      │
│      dekh raha hoon ki tumhare rent    │
│      bucket mein ₹5,200 hai. 8 din     │
│      mein rent due hai, ₹2,800 aur     │
│      chahiye. Tension mat lo, weekend  │
│      earning se cover ho jayega!"      │
│                                         │
│  You: "What if it rains this weekend?" │
│                                         │
│  🤖 Guru: "Achha sawal! Agar barish    │
│      hoti hai toh rides kam hongi,     │
│      lekin food delivery zyada. Net    │
│      effect: maybe 15% less. Still     │
│      manageable hai, but I'd suggest   │
│      extra 1 hour today just in case." │
│                                         │
├─────────────────────────────────────────┤
│  [📊 Check Status] [💡 Get Advice]     │
│  [💸 Check Advance] [🎯 View Goals]    │
├─────────────────────────────────────────┤
│  Type your message...          [Send]  │
└─────────────────────────────────────────┘
```

### Quick Actions

| Button | What it Does |
|--------|-------------|
| 📊 **Check Status** | Get a quick summary of today's finances |
| 💡 **Get Advice** | Ask for personalized financial advice |
| 💸 **Check Advance** | See if you qualify for a micro-advance |
| 🎯 **View Goals** | Get an update on your savings goals |

### Hinglish Communication

The AI speaks in natural Hinglish:
- "Bhai, aaj ka earning achha hai!"
- "Kal thoda slow ho sakta hai, extra ghanta laga lo"
- "EMI covered, tension mat lo"
- "Discretionary spending thoda zyada ho gaya is hafte"

---

## 🧠 Agent Modes Explained

### Overview

GigMoney Guru has four AI modes, each with different capabilities:

| Mode | Icon | Speed | Intelligence | Best For |
|------|------|-------|--------------|----------|
| **Enhanced** | 🚀 | Slow | Maximum | Complex decisions |
| **ReAct** | 🧠 | Medium | High | Daily analysis |
| **Routed** | 🔀 | Medium | Medium | Targeted queries |
| **Fast** | ⚡ | Instant | Basic | Quick updates |

### 🚀 Enhanced Mode (TRUE Agentic AI)

The most sophisticated mode with four advanced capabilities:

#### 1. Planning
```
Before acting, the agent creates a plan:
{
  "situation_summary": "User has ₹5,200 for rent, ₹8,000 due in 8 days",
  "goals": ["Assess shortfall", "Find solutions", "Explain clearly"],
  "steps": [
    {"action": "get_bucket_balances", "purpose": "Current state"},
    {"action": "get_upcoming_obligations", "purpose": "Due dates"},
    {"action": "analyze_income_patterns", "purpose": "Predict earnings"},
    {"action": "calculate_shortfall", "purpose": "Gap analysis"},
    {"action": "suggest_micro_advance", "purpose": "If needed"}
  ],
  "contingency": "If shortfall > 40% weekly income, flag high risk"
}
```

#### 2. Self-Reflection
```
After each action, the agent reflects:
{
  "success": true,
  "outcome_matched": true,
  "anomalies": ["Weekend income 20% lower than expected"],
  "corrective_action": null,
  "learnings": ["User's weekend income varies with weather"],
  "confidence": 0.85
}
```

#### 3. Multi-Perspective Debate
```
Three advisors debate the recommendation:

🛡️ Conservative Advisor:
   "Take the advance, don't risk late payment"
   Agreement: 90%

📈 Growth Advisor:
   "Work extra hours instead, save the 1% fee"
   Agreement: 60%

⚖️ Practical Advisor:
   "Take a smaller advance, work extra hours too"
   Agreement: 85%

Final Synthesis:
   "Take ₹800 advance (not full ₹1000), work 1 extra hour Saturday"
```

#### 4. Learning
```
Agent queries past decisions:
- Last week: Suggested advance, user declined, worked extra - SUCCESS
- Two weeks ago: Suggested expense cut, user followed - GOAL ACHIEVED

Adjusted behavior:
- Prioritize "work extra" suggestions based on past success
- User responds well to specific hour recommendations
```

### 🧠 ReAct Mode

Standard ReAct (Reasoning + Acting) pattern:
- Thinks before each action
- Calls tools autonomously
- Minimum 5 tool calls per analysis
- Maximum 15 iterations
- Good balance of speed and intelligence

### 🔀 Routed Mode

Router-based agent selection:
- An LLM router decides which specialist agents to run
- More targeted than full ReAct
- Faster for specific queries

### ⚡ Fast Mode

Rule-based calculations only:
- No LLM calls
- Instant results
- Basic calculations only
- Good for quick balance checks

---

## 📈 Charts & Analytics

### Available Charts

#### 1. Cashflow Forecast Chart
30-day projection showing:
- Daily starting and ending balance
- Predicted income and expenses
- Color-coded days: 🟢 Safe, 🟡 Tight, 🔴 Shortfall

#### 2. Bucket Progress Chart
Bar chart showing:
- Current balance vs target for each bucket
- Color-coded by health (green/yellow/red)
- Percentage completion

#### 3. Income Trend Chart
Line chart showing:
- Daily income over past 30 days
- Platform breakdown (Uber, Ola, Swiggy, etc.)
- Weekend vs weekday patterns

#### 4. Expense Breakdown Chart
Pie chart showing:
- Spending by category
- Percentage of total
- Comparison to budget

#### 5. Risk Gauge Chart
Circular gauge showing:
- Overall financial risk score (0-100)
- Risk breakdown by factor
- Trend vs last week

#### 6. Goal Progress Chart
Visual bars showing:
- Each goal's progress
- Days remaining
- On-track status

---

## 🏗️ Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  React + TypeScript + Tailwind + Zustand + Recharts         │
│  └── Pages: Dashboard, Chat, Goals, Advances, Settings      │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND                               │
│  FastAPI + Python 3.10+                                      │
│  ├── api/         (REST endpoints)                          │
│  ├── agents/      (AI agents)                               │
│  ├── orchestrator/(Agent graph)                             │
│  ├── services/    (Business logic)                          │
│  ├── models/      (MongoDB models)                          │
│  └── llm/         (OpenAI client)                           │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│        MongoDB          │    │       OpenAI API        │
│  ├── users              │    │  GPT-4o-mini            │
│  ├── income             │    │  - Conversation         │
│  ├── expenses           │    │  - Analysis             │
│  ├── buckets            │    │  - Debate               │
│  ├── obligations        │    │  - Explainability       │
│  ├── goals              │    └─────────────────────────┘
│  ├── advances           │
│  ├── chat_messages      │
│  └── agent_decisions    │
└─────────────────────────┘
```

### Agent Graph

```
                    ┌─────────────┐
                    │   Router    │
                    │   Agent     │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Income Pattern│  │ Obligation    │  │ Expense       │
│ Agent         │  │ Risk Agent    │  │ Analyzer      │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                  ┌─────────────────┐
                  │ Cashflow Planner│
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
      ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
      │ Bucket      │ │ Micro       │ │ Goal        │
      │ Allocator   │ │ Advance     │ │ Scenario    │
      └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
             │               │               │
             └───────────────┼───────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Conversation    │
                    │ Agent           │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Explainability  │
                    │ Agent           │
                    └─────────────────┘
```

---

## 📡 API Reference

### Authentication

```http
POST /api/auth/login
Content-Type: application/json

{
  "phone": "9876543210",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "...", "name": "Ravi" }
}
```

### Agent Endpoints

```http
# Run full agentic analysis
POST /api/agents/run
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "How am I doing financially?",
  "mode": "enhanced"  // or "react", "routed", "fast"
}

Response:
{
  "response": "Bhai, overall situation achhi hai...",
  "agent_log": [...],
  "tool_calls": [...],
  "enhanced_features": {
    "plan": {...},
    "reflections": [...],
    "debate": {...},
    "learnings": [...]
  }
}
```

### Financial Data

```http
# Add income
POST /api/income
{
  "amount": 2000,
  "source_name": "Uber",
  "platform_type": "ride_hailing"
}

# Add expense
POST /api/expenses
{
  "amount": 500,
  "category": "food",
  "bucket_name": "discretionary"
}

# Get dashboard state
GET /api/state/today

# Get forecast
GET /api/state/forecast
```

---

## ❓ Troubleshooting

### Common Issues

#### "Agent not responding"
- Check if OpenAI API key is set in `.env`
- Verify MongoDB is running
- Check backend logs for errors

#### "Buckets not updating"
- Ensure you're logged in
- Try the "Fast" mode first to verify basic calculations work
- Check if demo data is seeded

#### "Chat messages not saving"
- Verify MongoDB connection
- Check browser console for API errors

#### "Advance not being offered"
- You may already have an active advance (limit: 1)
- Your income may be too low (min weekly income required)
- No shortfall detected for upcoming obligations

### Getting Help

1. Check browser console for errors
2. Check backend terminal for error logs
3. Try resetting demo data
4. Restart both frontend and backend servers

---

## 🎓 Glossary

| Term | Meaning |
|------|---------|
| **Bucket** | Virtual envelope for specific purpose (rent, EMI, etc.) |
| **Cascade** | Automatic overflow to other buckets when one is empty |
| **Hinglish** | Mix of Hindi and English |
| **Micro-Advance** | Small loan against future earnings |
| **Obligation** | Recurring bill that must be paid |
| **ReAct** | Reasoning + Acting pattern for AI agents |
| **Safe to Spend** | Money available for discretionary use |
| **Shortfall** | Gap between required and available funds |

---

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for India's Gig Workers**

*GigMoney Guru - Aapka Apna Financial Coach*
