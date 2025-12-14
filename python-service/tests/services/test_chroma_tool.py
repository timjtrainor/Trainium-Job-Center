"""Tests for the ChromaDB search tools."""

from python_service.app.services.crewai.tools.chroma_search import (
    chroma_search,
    chroma_list_collections,
    chroma_search_across_collections,
    ChromaSearchTool,
)


class DummyCollection:
    """Minimal in-memory collection for similarity queries."""

    def __init__(self, name: str = "test") -> None:
        self.name = name
        self.documents = []
        self.embeddings = []
        self.metadatas = []

    def add(self, *, documents, embeddings, ids, metadatas=None):  # pragma: no cover - simple
        self.documents.extend(documents)
        self.embeddings.extend(embeddings)
        if metadatas:
            self.metadatas.extend(metadatas)

    def query(self, query_texts, n_results=4, include=None):
        def embed(text: str):
            words = ["hello", "python", "world"]
            return [1.0 if w in text.lower() else 0.0 for w in words]

        q_emb = embed(query_texts[0])
        scored = []
        for i, (doc, emb) in enumerate(zip(self.documents, self.embeddings)):
            score = sum(a * b for a, b in zip(emb, q_emb))
            distance = 1.0 - score / max(1.0, sum(q_emb))  # Normalized distance
            metadata = self.metadatas[i] if i < len(self.metadatas) else {}
            scored.append((distance, doc, metadata))
        
        scored.sort()  # Sort by distance (smaller = more relevant)
        
        results = {"documents": [], "metadatas": [], "distances": []}
        for distance, doc, metadata in scored[:n_results]:
            results["documents"].append(doc)
            results["metadatas"].append(metadata)
            results["distances"].append(distance)
        
        # Return in the nested format ChromaDB uses
        return {
            "documents": [results["documents"]],
            "metadatas": [results["metadatas"]],
            "distances": [results["distances"]]
        }

    def count(self):
        return len(self.documents)


class DummyCollectionInfo:
    """Represents collection info returned by list_collections."""
    def __init__(self, name: str, metadata: dict = None):
        self.name = name
        self.metadata = metadata or {}


class DummyClient:
    def __init__(self) -> None:
        self.collections = {
            "test": DummyCollection("test"),
            "job_postings": DummyCollection("job_postings"),
            "company_profiles": DummyCollection("company_profiles"),
        }

    def get_or_create_collection(self, name):  # pragma: no cover - simple
        if name not in self.collections:
            self.collections[name] = DummyCollection(name)
        return self.collections[name]

    def get_collection(self, name):
        if name not in self.collections:
            raise ValueError(f"Collection {name} not found")
        return self.collections[name]

    def list_collections(self):
        return [DummyCollectionInfo(name) for name in self.collections.keys()]


def test_chroma_search_tool_returns_seeded_document(monkeypatch):
    """New tool retrieves the document seeded in the dummy collection."""

    client = DummyClient()
    monkeypatch.setattr(
        "app.services.crewai.tools.chroma_search.get_chroma_client",
        lambda: client,
    )

    client.collections["test"].add(
        documents=["Hello Python world"],
        ids=["1"],
        embeddings=[[1.0, 1.0, 1.0]],
        metadatas=[{"title": "Test Document"}],
    )

    result = chroma_search("hello", "test", 1)

    assert "Hello Python world" in result
    assert "Test Document" in result


def test_chroma_list_collections(monkeypatch):
    """Test that collections can be listed."""
    
    client = DummyClient()
    monkeypatch.setattr(
        "app.services.crewai.tools.chroma_search.get_chroma_client",
        lambda: client,
    )

    # Add some documents to collections
    client.collections["job_postings"].add(
        documents=["Python developer position"],
        ids=["1"],
        embeddings=[[1.0, 1.0, 0.0]],
    )
    client.collections["company_profiles"].add(
        documents=["Tech company profile"],
        ids=["1"],
        embeddings=[[0.0, 1.0, 1.0]],
    )

    result = chroma_list_collections()

    assert "job_postings" in result
    assert "company_profiles" in result
    assert "Documents: 1" in result  # Should show document count


def test_chroma_search_across_collections(monkeypatch):
    """Test cross-collection search functionality."""
    
    client = DummyClient()
    monkeypatch.setattr(
        "app.services.crewai.tools.chroma_search.get_chroma_client",
        lambda: client,
    )

    # Add documents to multiple collections
    client.collections["job_postings"].add(
        documents=["Python developer position with machine learning"],
        ids=["1"],
        embeddings=[[1.0, 1.0, 0.0]],
        metadatas=[{"title": "ML Engineer Job"}],
    )
    client.collections["company_profiles"].add(
        documents=["Python-focused tech company"],
        ids=["1"],
        embeddings=[[1.0, 0.0, 0.0]],
        metadatas=[{"title": "Tech Company"}],
    )

    result = chroma_search_across_collections(
        "python", 
        ["job_postings", "company_profiles"], 
        1
    )

    assert "job_postings" in result
    assert "company_profiles" in result
    assert "Python developer position" in result
    assert "Python-focused tech company" in result


def test_legacy_chroma_search_tool_compatibility(monkeypatch):
    """Test that legacy ChromaSearchTool still works for backward compatibility."""
    
    client = DummyClient()
    monkeypatch.setattr(
        "app.services.crewai.tools.chroma_search.get_chroma_client",
        lambda: client,
    )

    client.collections["test"].add(
        documents=["Legacy compatibility test"],
        ids=["1"],
        embeddings=[[1.0, 1.0, 1.0]],
    )

    tool = ChromaSearchTool("test", 1)
    result = tool.run("legacy")

    assert "Legacy compatibility test" in result


def test_chroma_search_error_handling(monkeypatch):
    """Test error handling in ChromaDB tools."""
    
    def failing_client():
        raise Exception("Connection failed")
    
    monkeypatch.setattr(
        "app.services.crewai.tools.chroma_search.get_chroma_client",
        failing_client,
    )

    result = chroma_search("test query", "test_collection")
    
    assert "Error searching ChromaDB collection" in result
    assert "Connection failed" in result


def test_chroma_search_no_results(monkeypatch):
    """Test handling when no documents are found."""
    
    client = DummyClient()
    monkeypatch.setattr(
        "app.services.crewai.tools.chroma_search.get_chroma_client",
        lambda: client,
    )

    # Empty collection
    result = chroma_search("nonexistent query", "test", 5)
    
    assert "No relevant documents found" in result
    assert "test" in result

