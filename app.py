"""
app.py
-------
Sezzle AI Customer Support Bot (FastAPI)
"""

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sezzle AI Support Bot",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.helper import download_embeddings
from src.prompt import PROMPT

import os

load_dotenv()

# ==================================================
# Environment Variables
# ==================================================

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not PINECONE_API_KEY or not HUGGINGFACE_API_KEY or not GROQ_API_KEY:
    raise ValueError("❌ Missing API Keys in .env file.")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["HUGGINGFACE_API_KEY"] = HUGGINGFACE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

INDEX_NAME = "sezzle-bot"

# ==================================================
# Embeddings & Pinecone
# ==================================================

print("🔢 Loading embeddings...")
embeddings = download_embeddings()

print("📌 Connecting to Pinecone...")
docsearch = PineconeVectorStore.from_existing_index(
    index_name=INDEX_NAME,
    embedding=embeddings
)

retriever = docsearch.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)

# ==================================================
# LLM
# ==================================================

print("🤖 Loading LLM...")
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0.2
)

# ==================================================
# Helper
# ==================================================

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# ==================================================
# RAG Chain
# ==================================================

qa_chain = (
    {
        "context": retriever | format_docs,
        "input": RunnablePassthrough()
    }
    | PROMPT
    | llm
    | StrOutputParser()
)

print("✅ Sezzle AI Support Bot Ready!")

# ==================================================
# Routes
# ==================================================

from fastapi.responses import FileResponse

@app.get("/")
async def home():
    return FileResponse("templates/chat.html")


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.post("/get")
async def chat(msg: str = Form(...)):
    print(f"\n👤 User: {msg}")

    answer = qa_chain.invoke(msg)

    print(f"🤖 Bot: {answer}")

    return {
        "answer": answer
    }

