"""
src/helper.py
-------------
Helper functions for Sezzle AI Support Bot.
"""

import re
import json
import warnings

warnings.filterwarnings("ignore")

# NEW UPDATED CODE
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings

EMBED_MODEL = "BAAI/bge-base-en-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_sezzle_json(file_path: str, source_type: str) -> list[Document]:
    """Parse one Sezzle help center JSON file."""
    documents = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON: {file_path}")
        return []

    for category in data:
        category_title = category.get("title", "").strip()

        for article in category.get("articles", []):
            article_title = article.get("title", "").strip()
            article_url = article.get("url", "").strip()
            breadcrumbs = article.get("breadcrumbs", [])
            content_blocks = article.get("content", [])

            text_parts = []
            for block in content_blocks:
                btype = block.get("type", "")
                btext = block.get("text", "").strip()

                if not btext:
                    continue

                if btype == "bullet":
                    text_parts.append(f"• {btext}")
                elif btype == "number":
                    text_parts.append(f"{block.get('number', '')}. {btext}")
                elif btype == "heading":
                    text_parts.append(f"\n{btext}:")
                else:
                    text_parts.append(btext)

            body_text = "\n\n".join(text_parts).strip()
            if not body_text:
                continue

            page_content = f"""
Category: {category_title}
Article Title: {article_title}
Source URL: {article_url}
Navigation: {" > ".join(breadcrumbs) if breadcrumbs else "N/A"}

Content:
{body_text}
""".strip()

            metadata = {
                "title": article_title,
                "url": article_url,
                "source": source_type,
                "breadcrumbs": " > ".join(breadcrumbs) if breadcrumbs else "",
                "category": category_title[:80],
            }

            documents.append(
                Document(page_content=page_content, metadata=metadata)
            )

    return documents


def clean_text(text: str) -> str:
    """Clean extracted text."""
    text = re.sub(r'(\w+)-\s*[\r\n]+\s*(\w+)', r'\1\2', text)
    text = text.replace('\n\n', '[[PARA]]')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    text = text.replace('\t', ' ')
    text = text.replace('[[PARA]]', '\n\n')
    text = re.sub(r' +', ' ', text)
    return text.strip()


def clean_documents(documents: list[Document]) -> list[Document]:
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
    return documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    short_docs = [d for d in documents if len(d.page_content) <= 1200]
    long_docs = [d for d in documents if len(d.page_content) > 1200]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "•", ". ", " "],
    )

    split_chunks = splitter.split_documents(long_docs)
    return short_docs + split_chunks


def download_embeddings():
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return embeddings