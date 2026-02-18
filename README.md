# Palona - AI Commerce Agent

A single AI-powered shopping assistant for a commerce website, inspired by [Amazon Rufus](https://www.aboutamazon.com/news/retail/amazon-rufus). Handles general conversation, text-based product recommendations, and image-based product search.

## Features

- **General conversation**: "What's your name?", "What can you do?"
- **Text-based product recommendation**: "Recommend me a t-shirt for sports"
- **Image-based product search**: Upload an image to find similar products in the catalog

All product recommendations and search are limited to a predefined catalog of ~50 products.

## Technology Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Frontend** | React + Vite + TypeScript | Fast builds, small bundle, easy GitHub Pages deploy |
| **Backend** | Python FastAPI | Strong AI/ML ecosystem, async support, auto OpenAPI docs |
| **LLM (local)** | Ollama | Free, runs locally, supports LLaVA for vision |
| **LLM (deployed)** | Groq | Free tier, low latency |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Semantic product search |
| **Image search** | LLaVA via Ollama / Groq vision | Image → description → product match |
| **Catalog** | JSON + in-memory embeddings | Simple, no database setup |

## Project Structure

```
PalonaAIProject/
├── frontend/           # React + Vite
├── backend/            # FastAPI
│   ├── app/
│   │   ├── main.py     # API routes
│   │   ├── agent.py    # Single agent orchestration
│   │   ├── catalog.py  # Product catalog
│   │   ├── embeddings.py
│   │   └── llm.py      # Ollama + Groq adapter
│   └── data/
│       └── catalog.json
└── README.md
```

## Quick Start (Local)

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- [Ollama](https://ollama.ai) installed and running

### 1. Install Ollama models

```bash
ollama pull llama3.2
ollama pull llava
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The frontend uses `http://localhost:8000` as the API URL by default.

## Deployed Mode (Groq)

For deployment without local Ollama (e.g., Railway, Render):

1. Get a free API key from [Groq](https://console.groq.com)
2. Set environment variable: `GROQ_API_KEY=your_key`
3. Run the backend. It will use Groq instead of Ollama.

For image search in deployed mode, Groq's vision model (`llama-3.2-90b-vision-preview`) is used if available.

## API Documentation

When the backend is running, OpenAPI docs are at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/chat` | POST | Main agent endpoint. Body: `{ "message": "...", "image_base64": null }` |
| `GET /api/health` | GET | Health check |
| `GET /api/products` | GET | List all catalog products |

### Chat Request

```json
{
  "message": "Recommend me a t-shirt for sports",
  "image_base64": null
}
```

### Chat Response

```json
{
  "response": "I'd recommend the Sport Performance T-Shirt...",
  "products": [{ "id": "p1", "name": "...", "price": 29.99, ... }],
  "intent": "product_recommendation"
}
```

## Deployment

### Frontend (GitHub Pages)

1. Set `base` in `frontend/vite.config.ts` to your repo path (e.g. `/PalonaAIProject/` for `username.github.io/PalonaAIProject/`)
2. Build: `cd frontend && npm run build`
3. Deploy the `dist/` folder to GitHub Pages, or use the provided workflow

### Backend (Railway / Render)

1. Create a new service from the `backend/` directory
2. Set `GROQ_API_KEY` for cloud LLM
3. Add CORS origins for your GitHub Pages URL
4. Set `VITE_API_URL` in frontend build to your backend URL

### Frontend API URL

For production, build with:

```bash
VITE_API_URL=https://your-backend.railway.app npm run build
```

## License

MIT
