"""FastAPI application for AI Commerce Agent."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env before any app code reads env vars
load_dotenv(Path(__file__).parent.parent / ".env")

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.responses import JSONResponse

from .agent import process_message
from .catalog import load_catalog
from .retrieval import init_in_background, is_ready
from .state import get_or_create_session, update_session

# Global catalog (ChromaDB/embeddings warm up in background)
catalog: list[dict[str, Any]] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load catalog and start retrieval warm-up in background. App binds to port immediately."""
    global catalog
    catalog = load_catalog()
    init_in_background(catalog)
    yield


app = FastAPI(
    title="AI Commerce Agent API",
    description="Single agent for general conversation, text-based product recommendations, and image-based product search.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow GitHub Pages and localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request body."""

    message: str
    image_base64: str | None = None
    session_id: str | None = None  # Server-side state; new id = new chat
    history: list[ChatMessage] = []  # Fallback when no session_id
    previous_products: list[dict[str, Any]] = []  # Fallback when no session_id


class ChatResponse(BaseModel):
    """Chat response body."""

    response: str
    products: list[dict[str, Any]] = []
    intent: str
    session_id: str | None = None  # Returned when new session created


@app.get("/api/health")
async def health():
    """Health check endpoint. ready=true when retrieval is warmed up."""
    ready = is_ready()
    return {
        "status": "ok" if ready else "warming_up",
        "ready": ready,
        "catalog_size": len(catalog),
    }


@app.get("/api/products")
async def list_products():
    """List all products in the catalog."""
    return {"products": catalog}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main agent endpoint: text + optional image."""
    if not is_ready():
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Service warming up. First load takes 1–2 minutes. Please retry in 60 seconds.",
                "ready": False,
            },
            headers={"Retry-After": "60"},
        )
    try:
        # Use server-side state when session_id provided
        session_id, state = get_or_create_session(request.session_id)
        history = [{"role": h["role"], "content": h["content"]} for h in state["messages"]]
        previous_products = state["products"]
        if not history and request.history:
            history = [{"role": h.role, "content": h.content} for h in request.history]
        if not previous_products and request.previous_products:
            previous_products = request.previous_products

        result = await process_message(
            message=request.message,
            image_base64=request.image_base64,
            catalog=catalog,
            history=history,
            previous_products=previous_products,
        )

        # Update server-side session
        update_session(
            session_id,
            user_message=request.message,
            assistant_message=result["response"],
            products=result.get("products", []),
        )

        return ChatResponse(
            response=result["response"],
            products=result.get("products", []),
            intent=result.get("intent", "CHAT"),
            session_id=session_id,  # Client uses this for subsequent requests
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
