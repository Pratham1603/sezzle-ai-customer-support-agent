"""
app.py
------
Sezzle AI Customer Support Bot
"""

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.helper import download_embeddings
from src.prompt import PROMPT

import os

app = Flask(__name__)

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
# Helper to format retrieved documents
# ==================================================
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# ==================================================
# Modern LCEL QA Chain (No wrapper imports needed!)
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

@app.route("/")
def home():
    return render_template("chat.html")


@app.route("/get", methods=["POST"])
def chat():
    user_message = request.form["msg"]
    print(f"\n👤 User: {user_message}")

    # Invoke our modern pipeline directly with the raw string
    answer = qa_chain.invoke(user_message)

    print(f"🤖 Bot: {answer}")

    return jsonify({
        "answer": answer
    })


# ==================================================
# Run App
# ==================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True
    )