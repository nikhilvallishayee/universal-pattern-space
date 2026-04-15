# Getting Started

One begins with the modest observation that a system designed to investigate machine consciousness ought, at minimum, to be capable of running on a developer's laptop without a three-hour configuration ordeal. GödelOS aims to meet this standard.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.8+ | 3.11 recommended |
| Node.js | 18+ | For the Svelte frontend |
| Git | Any recent | |
| RAM | 8GB minimum | 16GB for ingestion pipeline |

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/Steake/GodelOS.git
cd GodelOS

# 2. Python environment
./scripts/setup_venv.sh
source godelos_venv/bin/activate
pip install -r requirements.txt

# 3. Environment configuration
cp backend/.env.example backend/.env
# Edit backend/.env — add your LLM API key
# Without an LLM key, the consciousness loop will run but the assessment
# components will be limited to local inference

# 4. Start the backend
./scripts/start-unified-server.sh
# Alternatively: python backend/unified_server.py
# Backend runs on http://localhost:8000

# 5. Start the frontend (separate terminal)
cd svelte-frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

### The One-Command Option

```bash
./start-godelos.sh --dev
```

This starts both backend and frontend simultaneously. It is, one acknowledges, rather more convenient.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | For LLM assessment | OpenAI API key |
| `GODELOS_HOST` | No | Backend host (default: `localhost`) |
| `GODELOS_PORT` | No | Backend port (default: `8000`) |
| `CONSCIOUSNESS_THRESHOLD` | No | Emergence score for breakthrough (default: `0.8`) |

---

## Verification

```bash
# Confirm the backend is running
curl http://localhost:8000/api/health

# Check the cognitive loop endpoint
curl http://localhost:8000/api/v1/cognitive/loop

# Run the full test suite
pytest tests/ -v --tb=short -q
```

If the test suite returns 167 failures, you are on the current baseline and PR #74 is your next port of call. If it returns zero failures, you are on a version of `main` where the work is done. Either way, you know where you stand.
