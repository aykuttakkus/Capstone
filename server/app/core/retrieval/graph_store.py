from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from server.app.core.retrieval.corpus import KnowledgeBase
from server.app.utils.text import tokenize


GRAPH_QUERY_KEYWORDS = {
    "cause",
    "causes",
    "effect",
    "effects",
    "relationship",
    "relationships",
    "connected",
    "connect",
    "link",
    "linked",
    "pattern",
    "patterns",
    "trigger",
    "triggers",
    "influence",
    "influences",
    "impact",
    "impacts",
    "between",
    "compare",
    "family",
    "support",
    "social",
    "interact",
    "interactions",
}


@dataclass
class GraphNode:
    id: str
    type: str
    metadata: dict = field(default_factory=dict)


def should_enable_graph_rag(knowledge_base: KnowledgeBase, min_chunks: int = 400) -> bool:
    if len(knowledge_base.chunks) < max(1, min_chunks):
        return False

    unique_topics = {chunk.topic for chunk in knowledge_base.chunks if chunk.topic}
    if len(unique_topics) < 4:
        return False

    keyword_count = len({kw.lower() for chunk in knowledge_base.chunks for kw in chunk.keywords})
    return keyword_count >= max(1, min_chunks // 2)


def is_graph_friendly_query(query: str, topic: str | None = None, *, min_terms: int = 5) -> bool:
    tokens = tokenize(query)
    if len(tokens) < max(1, min_terms):
        return False

    token_set = set(tokens)
    if len(token_set & GRAPH_QUERY_KEYWORDS) >= 2:
        return True

    if topic in {"social_pressure", "help_seeking"} and len(token_set) >= min_terms:
        return True

    return False


class GraphStore:
    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, list[str]] = {}

    def build(self, kb: KnowledgeBase) -> None:
        for chunk in kb.chunks:
            chunk_node_id = f"chunk_{chunk.id}"
            self._add_node(chunk_node_id, "chunk", {"title": chunk.title})

            topic_node_id = f"topic_{chunk.topic}"
            self._add_node(topic_node_id, "topic")
            self._add_edge(topic_node_id, chunk_node_id)

            for kw in chunk.keywords:
                kw_node_id = f"kw_{kw.lower()}"
                self._add_node(kw_node_id, "keyword")
                self._add_edge(kw_node_id, chunk_node_id)
                self._add_edge(topic_node_id, kw_node_id)

    def _add_node(self, node_id: str, node_type: str, metadata: dict | None = None) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = GraphNode(node_id, node_type, metadata or {})

    def _add_edge(self, u: str, v: str) -> None:
        if u not in self.edges:
            self.edges[u] = []
        if v not in self.edges:
            self.edges[v] = []
        if v not in self.edges[u]:
            self.edges[u].append(v)
        if u not in self.edges[v]:
            self.edges[v].append(u)

    def get_related_chunks(self, seed_topic: str | None = None, seed_keywords: list[str] | None = None) -> list[str]:
        related_chunk_ids = set()
        to_visit = []

        if seed_topic:
            to_visit.append(f"topic_{seed_topic}")
        if seed_keywords:
            to_visit.extend([f"kw_{kw.lower()}" for kw in seed_keywords])

        visited = set()
        while to_visit:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)

            neighbors = self.edges.get(current, [])
            for n in neighbors:
                if n.startswith("chunk_"):
                    related_chunk_ids.add(n.replace("chunk_", ""))
                elif n not in visited:
                    to_visit.append(n)

            if len(visited) > 50:
                break

        return list(related_chunk_ids)

    def save(self) -> None:
        if not self.storage_path:
            return
        data = {
            "nodes": {k: {"id": v.id, "type": v.type, "metadata": v.metadata} for k, v in self.nodes.items()},
            "edges": self.edges,
        }
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(data, f)

    def load(self) -> bool:
        if not self.storage_path or not self.storage_path.exists():
            return False
        with open(self.storage_path, "r") as f:
            data = json.load(f)
            self.nodes = {k: GraphNode(**v) for k, v in data["nodes"].items()}
            self.edges = data["edges"]
        return True
