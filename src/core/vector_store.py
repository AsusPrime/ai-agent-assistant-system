import os
from typing import TYPE_CHECKING

import chromadb
import google.genai as genai

from config import settings

if TYPE_CHECKING:
    from chromadb import Collection

_SUPPORTED_EXTENSIONS = {".txt", ".md", ".py", ".rst", ".json", ".csv"}
_MAX_FILE_BYTES = 512 * 1024  # 512 KB
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50


class _GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.API_KEY)

    def __call__(self, input: list[str]) -> list[list[float]]:
        result: list[list[float]] = []
        for text in input:
            resp = self._client.models.embed_content(
                model="models/text-embedding-004",
                contents=text,
            )
            result.append(resp.embeddings[0].values)
        return result


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    # fallback: split oversized paragraphs
    final: list[str] = []
    for chunk in chunks:
        if len(chunk) <= chunk_size * 2:
            final.append(chunk)
        else:
            for i in range(0, len(chunk), chunk_size - overlap):
                final.append(chunk[i: i + chunk_size])
    return final


class VectorStore:
    def __init__(self, data_dir: str) -> None:
        data_dir = os.path.expanduser(data_dir)
        os.makedirs(data_dir, exist_ok=True)
        chroma_path = os.path.join(data_dir, "chroma")
        client = chromadb.PersistentClient(path=chroma_path)
        self._collection: Collection = client.get_or_create_collection(
            name="knowledge",
            embedding_function=_GeminiEmbeddingFunction(),
        )

    def index_file(self, path: str, chunk_size: int = _CHUNK_SIZE) -> int:
        path = os.path.expanduser(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        ext = os.path.splitext(path)[1].lower()
        if ext not in _SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        if os.path.getsize(path) > _MAX_FILE_BYTES:
            raise ValueError(f"File too large (>{_MAX_FILE_BYTES // 1024}KB): {path}")
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
        chunks = _chunk_text(text, chunk_size=chunk_size)
        if not chunks:
            return 0
        ids = [f"{path}::{i}" for i in range(len(chunks))]
        self._collection.upsert(ids=ids, documents=chunks, metadatas=[{"source": path}] * len(chunks))
        return len(chunks)

    def index_directory(self, dir_path: str) -> dict[str, int]:
        dir_path = os.path.expanduser(dir_path)
        report: dict[str, int] = {}
        for root, _, files in os.walk(dir_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()
                if ext not in _SUPPORTED_EXTENSIONS:
                    continue
                if os.path.getsize(fpath) > _MAX_FILE_BYTES:
                    continue
                try:
                    report[fpath] = self.index_file(fpath)
                except Exception:
                    report[fpath] = 0
        return report

    def search(self, query: str, n_results: int = 3) -> list[str]:
        total = self._collection.count()
        if total == 0:
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=min(n_results, total),
        )
        docs = results.get("documents", [[]])[0]
        return [d for d in docs if d]
