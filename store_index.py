"""
store_index.py
--------------
Builds Pinecone vector store from Sezzle help center JSON files.

Run once:
    python store_index.py
"""

from dotenv import load_dotenv
import os
import re
import time

from src.helper import (
    load_sezzle_json,
    clean_documents,
    chunk_documents,
    download_embeddings,
)
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore


# ── 1. Setup & Config ─────────────────────────────────────────────────────────

load_dotenv()

PINECONE_API_KEY    = os.getenv("PINECONE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

os.environ["PINECONE_API_KEY"]    = PINECONE_API_KEY
os.environ["HUGGINGFACE_API_KEY"] = HUGGINGFACE_API_KEY

# Set True to wipe existing index and re-upload everything
FORCE_RELOAD = False

INDEX_NAME = "sezzle-bot"

# Shopper + Merchant only — Partner excluded (not customer-facing)
DATA_FILES = {
    "shopper":  "data/shopper_help_center.json",
    "merchant": "data/merchant_help_center.json",
}


# ── 2. Initialize Pinecone & Embeddings ───────────────────────────────────────

pc         = Pinecone(api_key=PINECONE_API_KEY)
embeddings = download_embeddings()


# ── 3. Handle Index Creation / Deletion ──────────────────────────────────────

if FORCE_RELOAD and pc.has_index(INDEX_NAME):
    print(f"⚠️  Force reload active. Deleting index: {INDEX_NAME}...")
    pc.delete_index(INDEX_NAME)
    time.sleep(2)

if not pc.has_index(INDEX_NAME):
    print(f"🆕 Creating new index: {INDEX_NAME}...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=768,      # BAAI/bge-base-en-v1.5 output size
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    # Wait for index to be ready
    while not pc.describe_index(INDEX_NAME).status["ready"]:
        time.sleep(1)
    print(f"✅ Index '{INDEX_NAME}' created and ready")


# ── 4. Check if Data Already Exists ──────────────────────────────────────────

index        = pc.Index(INDEX_NAME)
index_stats  = index.describe_index_stats()
vector_count = index_stats["total_vector_count"]

if vector_count > 0 and not FORCE_RELOAD:
    print(f"ℹ️  Index '{INDEX_NAME}' already has {vector_count} vectors. Skipping upload.")
    print("   Set FORCE_RELOAD = True to re-upload.")

else:
    print("📦 Loading and processing documents...\n")

    # Load all JSON files
    all_docs = []
    for source_type, file_path in DATA_FILES.items():
        docs = load_sezzle_json(file_path, source_type)
        all_docs.extend(docs)
        print(f"📁 {source_type:<10}: {len(docs)} articles loaded")

    print(f"\n📊 Total articles : {len(all_docs)}")

    # Clean
    all_docs = clean_documents(all_docs)
    print("🧹 Text cleaned")

    # Chunk
    all_chunks = chunk_documents(all_docs)
    short = sum(1 for d in all_docs if len(d.page_content) <= 1200)
    long  = sum(1 for d in all_docs if len(d.page_content) >  1200)
    print(f"✂️  Chunks : {len(all_chunks)} total")
    print(f"   Kept whole : {short}  |  Split : {long}")

    # Generate Unique IDs
    # Format: {source}_{INITIALS}_{index}
    # e.g. shopper_HDRF_1 = How Do Refunds work, article 1, shopper source
    doc_ids = []
    for i, doc in enumerate(all_chunks, start=1):
        source      = doc.metadata.get("source", "doc")
        title       = doc.metadata.get("title", "unknown")
        clean_title = title.replace("-", " ")
        initials    = "".join(
            [word[0].upper() for word in clean_title.split() if word]
        )[:8]
        doc_ids.append(f"{source}_{initials}_{i}")

    # Batch Upsert to Pinecone
    batch_size = 100
    print(f"\n🚀 Upserting {len(all_chunks)} chunks in batches of {batch_size}...")

    for i in range(0, len(all_chunks), batch_size):
        batch_docs = all_chunks[i: i + batch_size]
        batch_ids  = doc_ids[i: i + batch_size]

        PineconeVectorStore.from_documents(
            documents=batch_docs,
            embedding=embeddings,
            index_name=INDEX_NAME,
            ids=batch_ids
        )
        print(f"   Uploaded {i + 1} → {i + len(batch_docs)}")

    print("\n✅ Upload complete")


# ── 5. Initialize Search Object ───────────────────────────────────────────────

docsearch = PineconeVectorStore(
    index_name=INDEX_NAME,
    embedding=embeddings
)

print(f"\n🔍 docsearch ready — index: {INDEX_NAME}")