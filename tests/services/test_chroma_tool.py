"""Tests for the Chroma search tool."""

from app.services.crewai.tools.chroma_search import ChromaSearchTool


class DummyCollection:
    """Minimal in-memory collection for similarity queries."""

    def __init__(self) -> None:
        self.documents = []
        self.embeddings = []

    def add(self, *, documents, embeddings, ids):  # pragma: no cover - simple
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)

    def query(self, query_texts, n_results=4):
        def embed(text: str):
            words = ["hello", "python", "world"]
            return [1.0 if w in text.lower() else 0.0 for w in words]

        q_emb = embed(query_texts[0])
        scored = []
        for doc, emb in zip(self.documents, self.embeddings):
            score = sum(a * b for a, b in zip(emb, q_emb))
            scored.append((score, doc))
        scored.sort(reverse=True)
        docs = [doc for _, doc in scored[:n_results]]
        return {"documents": [docs]}


class DummyClient:
    def __init__(self) -> None:
        self.collection = DummyCollection()

    def get_or_create_collection(self, name):  # pragma: no cover - simple
        return self.collection


def test_chroma_search_tool_returns_seeded_document(monkeypatch):
    """Tool retrieves the document seeded in the dummy collection."""

    client = DummyClient()
    monkeypatch.setattr(
        "app.services.crewai.tools.chroma_search.get_chroma_client",
        lambda: client,
    )

    client.collection.add(
        documents=["Hello Python world"],
        ids=["1"],
        embeddings=[[1.0, 1.0, 1.0]],
    )

    tool = ChromaSearchTool(collection_name="test", n_results=1)

    result = tool.run("hello")

    assert "Hello Python world" in result

