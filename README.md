# OmniLens AI ⚡

> **Universal Enterprise LLM Gateway & Real-Time Context Window Optimizer**

OmniLens AI is a FAANG-grade, multi-model AI gateway engineered for ultra-low latency, granular cost/token telemetry, and interactive context window optimization (Map-Reduce, semantic deduplication, and sliding-window pruning).

---

## 🌟 Key Features

* **Real-Time Context Optimizer Studio**
  * **Map-Reduce Pruning:** Parallel chunk summarization for massive document inputs.
  * **Semantic Deduplication:** Cosine similarity clustering to strip redundant prompt data.
  * **Sliding Window & Recency Decay:** Pin system context while dropping low-impact conversational turns.
  * **Live Savings Dial:** Real-time token reduction, cost-savings projection, and latency estimates before sending queries.

* **Enterprise Telemetry Engine**
  * **Live Latency & Speed:** Time-To-First-Token (TTFT), tokens/second (TPS), and total round-trip time.
  * **Token Accounting:** Exact prompt (in) and completion (out) counts.
  * **Unit Economics:** Micro-cent accuracy cost calculation ($/query) across providers.

* **Universal Multi-Model Routing**
  * Unified proxy interface supporting **Google Gemini**, **OpenAI**, **Anthropic Claude**, and **Groq**.
  * Dynamic fallback, load balancing, and side-by-side model arena comparison.

---

## 🏗️ System Architecture

```text
  [ Client Browser / SPA ]
             │
             │ (SSE / WebSockets)
             ▼
  [ FastAPI Gateway & Telemetry Engine ]
             │
      ┌──────┴───────────────────────────────────────┐
      ▼                                              ▼
[ Context Optimizer Pipeline ]             [ Redis Layer ]
  ├─ Map-Reduce Summarizer                   ├─ Semantic Cache
  ├─ Embedding Deduplication                 ├─ Rate Limiting
  └─ Tiktoken Token Estimator                └─ Session Windows
      │
      ▼
[ Universal Model Router (LiteLLM) ]
      ├─ Google Gemini API
      ├─ OpenAI GPT-4o
      ├─ Anthropic Claude 3.5
      └─ Groq LPU (Ultra-low latency)
```

---

## 🛠️ Tech Stack

* **Frontend:** Next.js / React (TypeScript), Tailwind CSS / Vanilla CSS, Lucide Icons, Recharts
* **Backend:** Python 3.11+, FastAPI, Uvicorn, AsyncIO
* **Inference & Routing:** LiteLLM, Tiktoken, HuggingFace Tokenizers
* **Caching & State:** Redis / Upstash
* **Streaming Protocol:** Server-Sent Events (SSE)

---

## 📁 Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # Chat & telemetry endpoints
│   │   ├── core/config.py         # App configurations & pricing tables
│   │   ├── services/
│   │   │   ├── optimizer.py       # Map-Reduce & context pruning algorithms
│   │   │   ├── telemetry.py       # TTFT, TPS & cost calculation
│   │   │   └── llm_router.py      # Unified model provider gateway
│   │   └── main.py                # FastAPI entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/                      # Next.js / React interactive dashboard
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone & Setup Repository

```bash
git init
git add .
git commit -m "Initial commit: project structure and specifications"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

---

## 🔑 Environment Configuration

Create a `.env` in `/backend`:

```env
# API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GROQ_API_KEY=your_groq_api_key

# Cache & Redis
REDIS_URL=redis://localhost:6379/0

# Server
PORT=8000
ENVIRONMENT=development
```

---

## 📜 License
MIT License.
