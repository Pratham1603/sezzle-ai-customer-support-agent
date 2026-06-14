"""
app.py
-------
Sezzle AI Customer Support Bot (FastAPI)
"""

# ==========================================
# Mock Sezzle Database
# ==========================================

orders = {
    "SZ1234": {
        "status": "Processing",
        "amount": 1499,
        "customer": "Pratham"
    },

    "SZ5678": {
        "status": "Delivered",
        "amount": 2499,
        "customer": "Rahul"
    }
}

from database import (
    init_db,
    save_conversation
)

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from wasabi import msg

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

# ==========================================
# Intent Classification
# ==========================================

from langchain_core.prompts import ChatPromptTemplate

INTENT_PROMPT = ChatPromptTemplate.from_template("""
You are an intent classifier.

Classify the user query into ONLY one of these intents:

refund_request
chargeback
cancel_order
order_status
payment_failure
merchant_account
checkout_issue
general_faq

Return ONLY the intent name.

User Query:
{query}
""")

intent_chain = (
    INTENT_PROMPT
    | llm
    | StrOutputParser()
)

def classify_intent(query):
    try:
        return intent_chain.invoke(
            {"query": query}
        ).strip().lower()

    except Exception:
        return "general_faq"

# ==================================================
# Confidence & Escalation
# ==================================================

def get_confidence(query):

    try:

        docs_with_scores = docsearch.similarity_search_with_score(
            query,
            k=5
        )

        if not docs_with_scores:
            return 0.0

        scores = [
            score
            for _, score in docs_with_scores
        ]

        return float(max(scores))

    except Exception:
        return 0.0


def confidence_level(score):

    if score >= 0.80:
        return "high"

    elif score >= 0.60:
        return "medium"

    return "low"


def should_escalate(score):

    return score < 0.60

# ==========================================
# Agent Tools
# ==========================================

def cancel_order(order_id):

    if order_id not in orders:

        return {
            "success": False,
            "message": f"Order {order_id} not found."
        }

    orders[order_id]["status"] = "Cancelled"

    return {
        "success": True,
        "action": "cancel_order",
        "order_id": order_id,
        "status": "Cancelled"
    }


def refund_order(order_id):

    if order_id not in orders:

        return {
            "success": False,
            "message": f"Order {order_id} not found."
        }

    return {
        "success": True,
        "action": "refund_order",
        "order_id": order_id,
        "refund_amount": orders[order_id]["amount"],
        "status": "Processing"
    }


def get_order_status(order_id):

    if order_id not in orders:

        return {
            "success": False,
            "message": f"Order {order_id} not found."
        }

    return {
        "success": True,
        "action": "order_status",
        "order_id": order_id,
        "status": orders[order_id]["status"]
    }

# ==================================================
# Extract Order ID
# ==================================================

import re

def extract_order_id(text):

    match = re.search(r"SZ\d+", text.upper())

    if match:
        return match.group()

    return None

# ==================================================
# Agentic Routes
# ==================================================

def execute_agent_action(intent, query):

    order_id = extract_order_id(query)

    if intent == "cancel_order":

        if not order_id:
            return {
                "message": "Please provide an order ID (Example: SZ1234)"
            }

        return cancel_order(order_id)

    elif intent == "refund_request":

        if not order_id:
            return {
                "message": "Please provide an order ID (Example: SZ1234)"
            }

        return refund_order(order_id)

    elif intent == "order_status":

        if not order_id:
            return {
                "message": "Please provide an order ID (Example: SZ1234)"
            }

        return get_order_status(order_id)

    return None

from database import get_connection

def get_analytics():
    conn = get_connection()
    cursor = conn.cursor()

    # total conversations
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_conversations = cursor.fetchone()[0]

    # intents breakdown
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE intent='refund_request'")
    refund_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM conversations WHERE intent='cancel_order'")
    cancel_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM conversations WHERE intent='order_status'")
    order_status_requests = cursor.fetchone()[0]

    # escalations
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE escalate=1")
    escalations = cursor.fetchone()[0]

    conn.close()

    return {
        "total_conversations": total_conversations,
        "refund_requests": refund_requests,
        "cancel_orders": cancel_orders,
        "order_status_requests": order_status_requests,
        "escalations": escalations
    }

# ==================================================
# Routes
# ==================================================

from fastapi.responses import FileResponse

# Create tables when app starts
init_db()

@app.get("/")
async def home():
    return FileResponse("templates/chat.html")


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }

@app.get("/analytics")
async def analytics():
    return get_analytics()

@app.post("/get")
async def chat(msg: str = Form(...)):

    print(f"\n👤 User: {msg}")

    intent = classify_intent(msg)

    # ==========================================
    # Agent Layer Inside Chat Endpoint 
    # ==========================================

    agent_result = execute_agent_action(
        intent,
        msg
    )

    if agent_result:

        print("Agent Executed")
        print(agent_result)

        answer = ""

        if intent == "cancel_order":

            answer = (
                f"Order {agent_result['order_id']} has been cancelled successfully."
            )

        elif intent == "refund_request":

            answer = (
                f"Refund request created successfully for order "
                f"{agent_result['order_id']}. "
                f"Refund amount: ₹{agent_result['refund_amount']}. "
                f"Status: {agent_result['status']}."
            )

        elif intent == "order_status":

            answer = (
                f"Order {agent_result['order_id']} "
                f"is currently {agent_result['status']}."
            )

        # Save for ALL agent actions
        print("Saving agent conversation...")

        save_conversation(
            query=msg,
            intent=intent,
            confidence=1.0,
            escalate=False
        )

        print("Agent conversation saved.")

        return {
            "agent_action": True,
            "intent": intent,
            "answer": answer
        }    

    confidence = get_confidence(msg)

    level = confidence_level(confidence)

    escalate = should_escalate(confidence)

    print("\n========== DEBUG ==========")
    print("User:", msg)
    print("Intent:", intent)
    print("Confidence:", confidence)
    print("Escalate:", escalate)
    print("==========================")

    if escalate:

        save_conversation(
            query=msg,
            intent=intent,
            confidence=confidence,
            escalate=True
        )

        return {
            "answer":
            "I'm not confident enough to answer this question. Please contact Sezzle support.",
            "intent": intent,
            "confidence": round(confidence, 2),
            "confidence_level": level,
            "escalate": True
        }

    answer = qa_chain.invoke(msg)

    print(f"Intent: {intent}")
    print(f"Confidence: {confidence}")
    print(f"Bot: {answer}")

    save_conversation(
        query=msg,
        intent=intent,
        confidence=confidence,
        escalate=False
    )

    return {
        "answer": answer,
        "intent": intent,
        "confidence": round(confidence, 2),
        "confidence_level": level,
        "escalate": False
    }