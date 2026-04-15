"""Tests for RAG pipeline: VectorStore + rag_handler functions."""

import os
import sys
import tempfile

import chromadb
import pytest

# src/ is the import root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.vector_store import VectorStore, _chunk_text
from core.schemas import Task, TaskResult
from core.enums import ActionTypeEnum
from core.session import SessionState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class _FakeEmbedding(chromadb.EmbeddingFunction):
    """Deterministic embedding: hash-based, no API calls."""

    def __call__(self, input: list[str]) -> list[list[float]]:
        results = []
        for text in input:
            h = hash(text) % 10_000
            results.append([h / 10_000] * 64)
        return results


@pytest.fixture()
def tmp_store(tmp_path):
    """VectorStore with fake embeddings pointing at a temp directory."""
    store = VectorStore.__new__(VectorStore)
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    store._collection = client.get_or_create_collection(
        name="test_knowledge",
        embedding_function=_FakeEmbedding(),
    )
    return store


@pytest.fixture()
def sample_file(tmp_path):
    """A small .txt file for indexing."""
    p = tmp_path / "note.txt"
    p.write_text("Python is a programming language.\n\nIt is widely used for AI.")
    return str(p)


@pytest.fixture()
def sample_dir(tmp_path):
    """Directory with mixed files (supported + unsupported)."""
    (tmp_path / "a.txt").write_text("Alpha content here.")
    (tmp_path / "b.md").write_text("Beta markdown content.")
    (tmp_path / "c.jpg").write_bytes(b"\xff\xd8")  # unsupported
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "d.py").write_text("# Python file\nprint('hello')")
    return str(tmp_path)


def _make_task(action: str, name: str = "", **params) -> Task:
    return Task(action=ActionTypeEnum(action), name=name, params=params)


# ---------------------------------------------------------------------------
# _chunk_text unit tests
# ---------------------------------------------------------------------------

class TestChunkText:
    def test_single_paragraph(self):
        chunks = _chunk_text("Hello world")
        assert chunks == ["Hello world"]

    def test_multiple_paragraphs_fit_one_chunk(self):
        text = "First.\n\nSecond."
        chunks = _chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert "First." in chunks[0]
        assert "Second." in chunks[0]

    def test_split_when_exceeds_chunk_size(self):
        text = "A" * 300 + "\n\n" + "B" * 300
        chunks = _chunk_text(text, chunk_size=400)
        assert len(chunks) == 2

    def test_empty_text(self):
        assert _chunk_text("") == []

    def test_only_whitespace(self):
        assert _chunk_text("   \n\n   ") == []

    def test_oversized_paragraph_gets_split(self):
        text = "X" * 2000
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1
        assert all(len(c) <= 500 for c in chunks)


# ---------------------------------------------------------------------------
# VectorStore tests
# ---------------------------------------------------------------------------

class TestVectorStoreIndexFile:
    def test_index_and_search(self, tmp_store, sample_file):
        count = tmp_store.index_file(sample_file)
        assert count >= 1
        results = tmp_store.search("programming language")
        assert len(results) >= 1

    def test_file_not_found(self, tmp_store):
        with pytest.raises(FileNotFoundError):
            tmp_store.index_file("/nonexistent/file.txt")

    def test_unsupported_extension(self, tmp_store, tmp_path):
        p = tmp_path / "image.png"
        p.write_bytes(b"\x89PNG")
        with pytest.raises(ValueError, match="Unsupported file type"):
            tmp_store.index_file(str(p))

    def test_file_too_large(self, tmp_store, tmp_path):
        p = tmp_path / "big.txt"
        p.write_text("x" * (513 * 1024))  # > 512KB
        with pytest.raises(ValueError, match="File too large"):
            tmp_store.index_file(str(p))

    def test_empty_file_returns_zero(self, tmp_store, tmp_path):
        p = tmp_path / "empty.txt"
        p.write_text("")
        count = tmp_store.index_file(str(p))
        assert count == 0

    def test_upsert_duplicate(self, tmp_store, sample_file):
        """Indexing same file twice should upsert, not duplicate."""
        count1 = tmp_store.index_file(sample_file)
        count2 = tmp_store.index_file(sample_file)
        assert count1 == count2
        total = tmp_store._collection.count()
        assert total == count1  # no duplicates


class TestVectorStoreIndexDirectory:
    def test_index_directory(self, tmp_store, sample_dir):
        report = tmp_store.index_directory(sample_dir)
        # a.txt, b.md, sub/d.py — 3 supported files; c.jpg skipped
        assert len(report) == 3
        assert all(v >= 1 for v in report.values())

    def test_empty_directory(self, tmp_store, tmp_path):
        empty = tmp_path / "empty_dir"
        empty.mkdir()
        report = tmp_store.index_directory(str(empty))
        assert report == {}


class TestVectorStoreSearch:
    def test_search_empty_store(self, tmp_store):
        results = tmp_store.search("anything")
        assert results == []

    def test_search_returns_list_of_strings(self, tmp_store, sample_file):
        tmp_store.index_file(sample_file)
        results = tmp_store.search("Python")
        assert isinstance(results, list)
        assert all(isinstance(r, str) for r in results)

    def test_n_results_cap(self, tmp_store, sample_file):
        tmp_store.index_file(sample_file)
        results = tmp_store.search("Python", n_results=1)
        assert len(results) <= 1


# ---------------------------------------------------------------------------
# rag_handler tests (search_knowledge / index_knowledge)
# ---------------------------------------------------------------------------

class TestSearchKnowledge:
    def test_empty_query(self):
        from tools.rag_handler import search_knowledge

        task = _make_task("search_knowledge", name="", query="")
        result = search_knowledge(task, SessionState())
        assert result.returncode == 1
        assert "No query" in result.stderr

    def test_no_results(self, tmp_store, monkeypatch):
        from tools import rag_handler

        monkeypatch.setattr(rag_handler, "_vector_store", tmp_store)
        task = _make_task("search_knowledge", name="test", query="anything")
        result = rag_handler.search_knowledge(task, SessionState())
        assert result.returncode == 0
        assert "No relevant documents" in result.stdout

    def test_returns_results(self, tmp_store, sample_file, monkeypatch):
        from tools import rag_handler

        tmp_store.index_file(sample_file)
        monkeypatch.setattr(rag_handler, "_vector_store", tmp_store)
        task = _make_task("search_knowledge", name="test", query="programming")
        result = rag_handler.search_knowledge(task, SessionState())
        assert result.returncode == 0
        assert "Knowledge base results" in result.stdout


class TestIndexKnowledge:
    def test_no_path(self):
        from tools.rag_handler import index_knowledge

        task = _make_task("index_knowledge", name="", path="")
        result = index_knowledge(task, SessionState())
        assert result.returncode == 1

    def test_index_file(self, tmp_store, sample_file, monkeypatch):
        from tools import rag_handler

        monkeypatch.setattr(rag_handler, "_vector_store", tmp_store)
        task = _make_task("index_knowledge", name="note.txt", path=sample_file)
        result = rag_handler.index_knowledge(task, SessionState())
        assert result.returncode == 0
        assert "Indexed" in result.stdout
        assert "chunk" in result.stdout

    def test_index_nonexistent_path(self, tmp_store, monkeypatch):
        from tools import rag_handler

        monkeypatch.setattr(rag_handler, "_vector_store", tmp_store)
        task = _make_task("index_knowledge", name="x", path="/no/such/path")
        result = rag_handler.index_knowledge(task, SessionState())
        assert result.returncode == 1

    def test_index_directory(self, tmp_store, sample_dir, monkeypatch):
        from tools import rag_handler

        monkeypatch.setattr(rag_handler, "_vector_store", tmp_store)
        task = _make_task("index_knowledge", name="docs", path=sample_dir)
        result = rag_handler.index_knowledge(task, SessionState())
        assert result.returncode == 0
        assert "file(s)" in result.stdout
