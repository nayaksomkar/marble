# Marble — Multi‑Agent Research Assistant

[![GitHub](https://img.shields.io/badge/GitHub-nayaksomkar/marble-blue)](https://github.com/nayaksomkar/marble)

A production‑grade research platform powered by **LangGraph**. Four specialized agents collaborate in a feedback loop: **Researcher → Summarizer → Critic → Refiner**, delivering high‑quality, self‑critiqued outputs.

---

## Why Marble is Better?

| Feature | Traditional API | Marble |
|---------|-----------------|--------|
| **Response Quality** | Single pass, no feedback | Iterative refinement until quality threshold met |
| **Debugging** | Hard to trace agent decisions | Full step-by-step history in database |
| **LLM Reliability** | Single provider, one failure = total failure | **Dual-provider fallback** (Groq + Mistral) |
| **Database** | Complex PostgreSQL setup | **Zero-config SQLite** (just works!) |
| **Deployment** | Docker required | **Pure Python** - runs anywhere with `pip install` |

### Unique Features:
- **Self-Critiquing**: Output is scored (1-10) and refined until quality threshold (default: 8)
- **Agent Tracing**: Every agent step saved with input/output for debugging
- **Resilient**: If Groq fails, Mistral automatically takes over
- **Simple**: No Docker, no PostgreSQL, no setup headaches

---

## Quick Start

### Local (SQLite — no setup)

```bash
git clone https://github.com/nayaksomkar/marble.git
cd marble

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000/docs

### Docker (PostgreSQL — production)

```bash
git clone https://github.com/nayaksomkar/marble.git
cd marble

# Copy env and add your API keys
cp .env.example .env
# Edit .env with your GROQ_API_KEY and MISTRAL_API_KEY

docker compose up -d
```

Visit: http://localhost:8000/docs

---

## Test Results

### 1. Health Check API
```bash
curl http://localhost:8000/health
```
```json
{
    "status": "healthy",
    "environment": "development",
    "database_connected": true,
    "version": "1.0.0"
}
```

### 2. Create Research Session

**Request:**
```bash
curl -X POST http://localhost:8000/research/ \
  -H "Content-Type: application/json" \
  -d '{"user_query": "What is AI?"}'
```

**Response:**
```json
{
    "session_id": 2,
    "user_query": "What is AI?",
    "final_output": "**Summary: Artificial Intelligence (AI)**\n\nArtificial Intelligence (AI) is a broad field of computer science focused on developing intelligent machines that can perform tasks that typically require human intelligence. The key characteristics of AI include:\n\n1. **Machine Learning (ML)**: AI systems can learn from data...\n2. **Reasoning and Problem-Solving**: AI systems can analyze complex data...\n3. **Natural Language Processing (NLP)**: AI systems can understand human language...\n4. **Computer Vision**: AI systems can interpret visual data...",
    "is_complete": true,
    "iteration_count": 0,
    "steps": [
        {"agent_name": "researcher", "input_data": {"user_query": "What is AI?"}, "output_data": {...}},
        {"agent_name": "summarizer", "input_data": {...}, "output_data": {"summary": "..."}},
        {"agent_name": "critic", "input_data": {...}, "output_data": {"critique": "...", "critique_score": 9}}
    ]
}
```

### 3. Multiple Query Tests

| Query | Summary | Critique Score | Iterations |
|-------|---------|----------------|-------------|
| What is Python programming? | Comprehensive overview with key features | 9/10 | 0 |
| Benefits of solar energy | Environmental & economic benefits | 10/10 | 0 |
| How does blockchain work? | Decentralized ledger explanation | 9/10 | 0 |
| What is machine learning? | ML algorithms & types explained | 10/10 | 0 |

### 4. Detailed Workflow Output

**Query: "What is machine learning?"**

```
Summary:
**Machine Learning Summary:**

Machine learning is a subset of artificial intelligence (AI) that 
involves the development of algorithms and statistical models that 
enable computers to learn from data, make decisions, and improve 
their performance over time without being explicitly programmed.

Key Characteristics:
1. **Data-driven**: Machine learning relies on large datasets
2. **Pattern Recognition**: Algorithms identify patterns
3. **Continuous Improvement**: Models improve with more data

Critique:
**Evaluation Scores:**
1. **Relevance to the query:** 10/10
2. **Completeness:** 9.5/10
3. **Accuracy:** 9/10
4. **Readability:** 9.5/10

Overall Score: 10/10
Iterations: 0 (threshold met, no refinement needed)
```

### 5. Agent Step History

Every agent interaction is saved in SQLite:

```
Agent Steps for Session #2:
1. Researcher  → Web search completed
2. Summarizer  → LLM generated summary (1.7KB)
3. Critic      → Quality score: 9/10 ✓
4. Refiner     → Skipped (score ≥ 8 threshold)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check with DB status |
| `POST` | `/research/` | Start new research session |
| `GET` | `/research/{id}` | Get session by ID |
| `GET` | `/research/` | List all sessions |

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│   Researcher    │ ◄── Web Search (DuckDuckGo)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Summarizer    │ ◄── LLM Summary (Groq)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Critic      │ ◄── Quality Score (1-10)
└────────┬────────┘
         │
    ┌────┴────┐
    │ Score≥8 │──► END (Output Ready)
    └────┬────┘
         │ Score<8
         ▼
┌─────────────────┐
│    Refiner      │ ◄── Improve based on critique
└────────┬────────┘
         │
         └──────────► (loop back to Critic)
```

---

## Configuration

Add your API keys in `.env`:

```bash
GROQ_API_KEY=your_groq_key
MISTRAL_API_KEY=your_mistral_key
LLM_MODEL=llama-3.1-8b-instant
MAX_ITERATIONS=3
CRITIQUE_THRESHOLD=8
```

---

## Tech Stack

- **FastAPI** - Modern Python web framework
- **LangGraph** - Multi-agent orchestration
- **SQLite** - Zero-config local database
- **LangChain** - LLM integration (Groq)
- **DuckDuckGo** - Free web search