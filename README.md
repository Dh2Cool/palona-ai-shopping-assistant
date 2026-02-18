# Palona – AI Agent for a Commerce Website

A single AI-powered shopping assistant inspired by [Amazon Rufus](https://www.aboutamazon.com/news/retail/amazon-rufus). One agent handles general conversation, text-based product recommendations, and image-based product search—all limited to a predefined product catalog.

---

## Features

| Use Case | Example |
|----------|---------|
| **General conversation** | "What's your name?", "What can you do?" |
| **Text-based product recommendation** | "Recommend me a t-shirt for sports" |
| **Image-based product search** | Upload an image to find similar products in the catalog |

All product recommendations and search are limited to items in the predefined catalog (~115 products from Amazon-style CSVs).

---

## Deliverables

### 1. User-friendly frontend interface

- React + Vite chat UI with message history
- Product cards with ratings, prices, and "View on Amazon" links
- Image upload for visual product search
- Markdown rendering (including comparison tables)
- Sticky header and input; product detail modals
- Responsive layout

### 2. Documented agent API

- **OpenAPI (Swagger)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/chat` | POST | Main agent endpoint (text + optional image) |
| `GET /api/health` | GET | Health check, catalog size |
| `GET /api/products` | GET | List all catalog products |

**Chat request:**
```json
{
  "message": "Recommend me a t-shirt for sports",
  "image_base64": null,
  "session_id": null,
  "history": [],
  "previous_products": []
}
```

**Chat response:**
```json
{
  "response": "I'd recommend the Nike Men's Park T-Shirt...",
  "products": [{ "id": "...", "name": "...", "price": "$29.76", "rating": 4.5, ... }],
  "intent": "SEARCH",
  "session_id": "uuid"
}
```

### 3. Code repository

- GitHub: [palona-ai-shopping-assistant](https://github.com/Dh2Cool/palona-ai-shopping-assistant)
- Includes this README with setup, architecture, and deployment instructions

---

## Technology Stack & Decisions

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | React + Vite + TypeScript | Fast builds, small bundle, strong typing |
| **Backend** | Python FastAPI | Async, OpenAPI docs, good AI/ML ecosystem |
| **LLM (local)** | Ollama (llama3.2, llava) | Free, runs locally, supports vision |
| **LLM (deployed)** | Groq (llama-3.1-8b, Llama 4 Scout vision) | Low latency, free tier |
| **Retrieval** | ChromaDB + sentence-transformers | Vector search; in-memory fallback on Python 3.14 |
| **Embeddings** | all-MiniLM-L6-v2 | Semantic product search |
| **Image search** | LLaVA / Groq Llama 4 Scout | Image → description → semantic match |
| **Catalog** | CSV (amazon_100 + amazon_clothing) | Easy to extend, no DB setup |

**Architecture highlights:**
- Single agent with intent routing (SEARCH, CHAT, IMAGE_SEARCH)
- Server-side session store for history and active products
- RAG: retrieve → augment prompt → generate

---

## Project Structure

```
PalonaAIProject/
├── frontend/                 # React + Vite
│   ├── src/
│   │   ├── components/       # Chat, Message, ImageUpload
│   │   └── hooks/            # useAgent
│   └── public/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI, /api/chat, /api/health, /api/products
│   │   ├── agent.py          # Intent routing, RAG orchestration
│   │   ├── catalog.py        # Load products from CSV
│   │   ├── retrieval.py      # ChromaDB / in-memory search
│   │   ├── state.py          # Session store
│   │   ├── llm.py            # Ollama + Groq adapter
│   │   └── embeddings.py     # sentence-transformers
│   ├── data/
│   │   ├── amazon_100_products.csv
│   │   └── amazon_clothing_products.csv
│   └── requirements.txt
└── README.md
```

---

## Quick Start (Local)

### Prerequisites

- Python 3.11 or 3.12 (ChromaDB; 3.14 uses in-memory fallback)
- Node.js 18+
- [Ollama](https://ollama.ai) (optional; use Groq for cloud-only)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
# Optional: copy .env.example to .env and set GROQ_API_KEY for cloud LLM
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. API defaults to `http://localhost:8000`.

### 3. Local LLM (Ollama)

```bash
ollama pull llama3.2
ollama pull llava
```

If `GROQ_API_KEY` is not set, the backend uses Ollama.

---

## Deployed Mode (Groq)

For hosting without Ollama:

1. Get an API key from [Groq Console](https://console.groq.com)
2. Set `GROQ_API_KEY` in your environment
3. Backend uses Groq for chat and vision (Llama 4 Scout)

---

## Deployment

See **[DEPLOY.md](DEPLOY.md)** for step-by-step instructions.

- **Railway**: Host both backend + frontend (recommended)
- **Render + Vercel**: Backend on Render, frontend on Vercel

Set `VITE_API_URL` to your backend URL when building the frontend.

---

## License

MIT
