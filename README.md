# Sezzle AI Customer Support Agent

A Retrieval-Augmented Generation (RAG) powered AI support agent for Sezzle, built with intent classification, agentic order actions, confidence-based escalation, and a real-time analytics dashboard.

**Live Backend:** https://harerpratham-sezzle-ai-customer-support-agent.hf.space

---

## Overview

Sezzle AI Customer Support Agent is an end-to-end, production-style conversational AI system built to handle real-world customer support for Sezzle, a Buy Now Pay Later (BNPL) fintech platform.

Unlike a simple FAQ chatbot, this project combines three layers of intelligence:

1. **Retrieval-Augmented Generation (RAG)** — answers are grounded strictly in Sezzle's official Shopper & Merchant Help Center content, preventing hallucinated policies, fees, or refund timelines.
2. **Intent Classification + Agentic Actions** — the agent detects user intent (refund, cancel order, order status, etc.) and can act on it directly (e.g., cancel an order, initiate a refund) rather than just describing how to do it.
3. **Confidence Scoring & Escalation** — every response is scored for retrieval confidence. Low-confidence queries are automatically escalated to human support instead of risking an incorrect answer.

The system is wrapped in a FastAPI backend, a React + Framer Motion chat widget frontend, and a Streamlit analytics dashboard for monitoring conversation trends, intent distribution, and escalation rates in real time.

This project was built as a portfolio piece to demonstrate production-grade GenAI engineering: RAG pipeline design, vector search, agentic tool execution, prompt engineering for grounded responses, and full-stack deployment, aimed at AI/ML and Applied AI engineering roles in fintech.

---

## Features

- **RAG-powered Q&A** — retrieves relevant context from Pinecone over Sezzle's Shopper & Merchant Help Center articles before generating an answer.
- **Strict grounded responses** — a custom system prompt enforces zero hallucination; the LLM only answers from retrieved context and explicitly refuses to invent fees, timelines, or policies.
- **Intent classification** — every query is classified into one of: refund_request, chargeback, cancel_order, order_status, payment_failure, merchant_account, checkout_issue, general_faq.
- **Agentic order actions** — detects order IDs (e.g., SZ1234) and directly executes actions: cancel an order, initiate a refund, or check order status.
- **Confidence scoring and auto-escalation** — computes similarity confidence for every retrieval; queries below a threshold are automatically flagged for human escalation instead of being guessed at.
- **Conversation logging** — all conversations (query, intent, confidence, escalation flag, timestamp) are persisted to SQLite for analytics.
- **Live analytics dashboard** — a Streamlit dashboard visualizes total conversations, intent distribution, escalation rate, average confidence, and daily trends.
- **Modern chat widget UI** — a floating, animated chat widget (React + Framer Motion) with quick-action buttons, typing indicators, and a voice-mode UI concept.
- **Containerized deployment** — a Dockerfile is included for one-command deployment, currently live on Hugging Face Spaces.

---

## Architecture

```
                          React Chat Widget
                       (Framer Motion + Vite)
                                  |
                              POST /get
                                  v
+----------------------------------------------------------------+
|                     FastAPI Backend (app.py)                    |
|                                                                  |
|   Intent Classifier (Groq LLM)                                  |
|            |                                                     |
|            |--- actionable intent + order ID found ------+      |
|            |                                              v      |
|            |                              Agentic Action Layer   |
|            |                              (cancel / refund /     |
|            |                               order status)         |
|            |                                      |               |
|            |                                Mock Order Database   |
|            |                                  (in-memory)         |
|            |                                                     |
|            +--- otherwise --------------------+                  |
|                                                v                  |
|                                  RAG QA Chain (LangChain)         |
|                                                                    |
|                Retriever -> Pinecone Vector Store                 |
|                (BAAI/bge-base-en-v1.5 embeddings, top-k = 5)      |
|                                                                    |
|                Context + Query -> Grounded System Prompt          |
|                       -> ChatGroq (Llama-3.3-70B) -> Answer       |
|                                                                    |
|   Confidence Scoring -> escalate if score < 0.60                  |
|                                                                    |
|   SQLite Logging (database.py)                                    |
|        -> /analytics, /recent-conversations, /daily-trends        |
+----------------------------------------------------------------+
                                  |
                                  v
                      Streamlit Analytics Dashboard
                           (streamlit_app.py)
```

### Data pipeline (offline, one-time)

```
shopper_help_center.json   --+
merchant_help_center.json  --+--> load_sezzle_json() --> clean_text() --> chunk_documents()
                                          (src/helper.py)

  --> HuggingFace Embeddings (BAAI/bge-base-en-v1.5)
  --> Pinecone Index "sezzle-bot" (768-dim, cosine similarity)
```

Run via `store_index.py` — a one-time (or re-runnable) script that builds and populates the Pinecone index.

---

## Tech Stack

**Backend / AI:** Python 3.11, FastAPI, LangChain (langchain, langchain-core, langchain-community, langchain-text-splitters), LangChain-Groq, LangChain-Pinecone, Pinecone (serverless, AWS us-east-1), HuggingFace Embeddings (BAAI/bge-base-en-v1.5, 768-dim), SQLite, Wasabi.

**LLM:** Groq — llama-3.3-70b-versatile.

**Frontend:** React 19, Vite 8, Framer Motion, React Icons, Spline (embedded 3D voice-mode visual).

**Analytics:** Streamlit, Pandas.

**DevOps:** Docker (containerized backend, deployed to Hugging Face Spaces); Vercel (frontend hosting).

---

## Project Structure

```
sezzle-ai-customer-support-agent/
├── app.py                      # FastAPI app — RAG chain, intent classifier, agentic actions, routes
├── database.py                 # SQLite connection, schema, and conversation logging
├── store_index.py              # One-time script to build the Pinecone vector index
├── streamlit_app.py            # Streamlit analytics dashboard
├── requirements.txt            # Backend Python dependencies
├── dashboard_requirements.txt  # Streamlit dashboard dependencies
├── runtime.txt                 # Python runtime version
├── Dockerfile                  # Container build for deployment
├── setup.py                    # Package metadata
│
├── data/
│   ├── shopper_help_center.json
│   ├── merchant_help_center.json
│   └── partner_help_center.json
│
├── src/
│   ├── helper.py                # JSON loading, text cleaning, chunking, embeddings
│   └── prompt.py                # Grounded system prompt template
│
├── templates/
│   └── chat.html                # Standalone HTML chat UI served at "/"
│
├── frontend/                    # React + Vite chat widget
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── public/
│   └── package.json
│
└── research/
    └── trials.ipynb             # Exploratory notebook / experimentation
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend)
- API keys for Pinecone, Groq, and HuggingFace

### 1. Clone the repository

```bash
git clone https://github.com/Pratham1603/sezzle-ai-customer-support-agent.git
cd sezzle-ai-customer-support-agent
```

### 2. Backend setup

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
PINECONE_API_KEY=your_pinecone_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
GROQ_API_KEY=your_groq_api_key
```

### 3. Build the vector index (one-time)

```bash
python store_index.py
```

Set `FORCE_RELOAD = True` inside `store_index.py` if you want to wipe and re-populate the index.

### 4. Run the backend

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`, with a built-in chat UI served at `http://localhost:8000/`.

### 5. Run the analytics dashboard

```bash
pip install -r dashboard_requirements.txt
streamlit run streamlit_app.py
```

Update the `API_URL` constant at the top of `streamlit_app.py` if your backend is not running on the default Hugging Face URL.

### 6. Run the React frontend (optional chat widget)

```bash
cd frontend
npm install
npm run dev
```

Update the fetch URL inside `frontend/src/App.jsx` to point to your local backend (`http://localhost:8000/get`) if testing locally.

---

## Docker

```bash
docker build -t sezzle-ai-agent .
docker run -p 7860:7860 --env-file .env sezzle-ai-agent
```

The app is available at `http://localhost:7860`.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves the built-in HTML chat interface |
| GET | `/health` | Health check |
| POST | `/get` | Main chat endpoint — accepts `msg` (form data); returns the agent's response, intent, confidence, and escalation status |
| GET | `/analytics` | Aggregated KPIs — total conversations, intent breakdown, escalation count, average confidence |
| GET | `/recent-conversations` | Returns the 10 most recent logged conversations |
| GET | `/daily-trends` | Returns conversation counts grouped by day |

### Example: POST /get

Request:
```bash
curl -X POST http://localhost:8000/get -d "msg=What is the status of order SZ1234?"
```

Response (agentic action):
```json
{
  "agent_action": true,
  "intent": "order_status",
  "answer": "Order SZ1234 is currently Processing."
}
```

Response (RAG, general FAQ):
```json
{
  "answer": "To request a refund, you need to...",
  "intent": "refund_request",
  "confidence": 0.84,
  "confidence_level": "high",
  "escalate": false
}
```

Response (low confidence, escalated):
```json
{
  "answer": "I'm not confident enough to answer this question. Please contact Sezzle support.",
  "intent": "general_faq",
  "confidence": 0.41,
  "confidence_level": "low",
  "escalate": true
}
```

---

## How It Works

1. A user sends a message via the chat widget or the `/get` endpoint.
2. **Intent classification** — a lightweight LLM call (Groq, llama-3.3-70b-versatile) classifies the message into a fixed set of support intents.
3. **Agentic routing** — if the intent maps to an actionable task (cancel_order, refund_request, order_status) and an order ID (e.g., SZ1234) is detected in the message, the corresponding action is executed against the mock order database and a direct response is returned, bypassing the RAG pipeline entirely.
4. **RAG fallback** — for all other queries, the system retrieves the top-5 most relevant chunks from the Pinecone vector index (Shopper + Merchant Help Center content) and passes them, along with the query, into a strict grounded prompt.
5. **Confidence scoring** — the maximum similarity score from retrieval determines a confidence level (high ≥ 0.80, medium ≥ 0.60, low < 0.60). Queries scoring below 0.60 are escalated instead of being answered.
6. **Logging** — every interaction (query, intent, confidence, escalation flag, timestamp) is written to a local SQLite database for analytics.
7. **Analytics dashboard** — the Streamlit app polls `/analytics`, `/recent-conversations`, and `/daily-trends` to visualize support trends in real time.

---

## Roadmap

- Replace the mock in-memory order database with a real database (PostgreSQL / Supabase)
- Add authentication for order-related actions
- Multi-turn conversation memory / context retention
- Streaming responses in the chat widget
- Add an evaluation suite (RAGAS) for retrieval and answer quality
- Expand the intent taxonomy and add a fine-tuned intent classifier
- Voice input/output integration (currently a UI placeholder)
- CI/CD pipeline for automated testing and deployment

---

## Contributing

Contributions, issues, and feature requests are welcome.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Author

**Pratham Harer**

- GitHub: [@Pratham1603](https://github.com/Pratham1603)
- Medium: [@prathamharer1603](https://medium.com/@prathamharer1603)
- X (Twitter): [@PROSEED_AI](https://x.com/PROSEED_AI)
- Kaggle: [prathamharer](https://www.kaggle.com/prathamharer)
- Portfolio: [pratham-harer.vercel.app](https://pratham-harer.vercel.app)
