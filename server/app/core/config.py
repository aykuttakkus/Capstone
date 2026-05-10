from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INDEX_DATA_DIR = DATA_DIR / "store"
STORE_DATA_DIR = DATA_DIR / "store"

# Corpus paths
RAW_CORPUS_PATH = RAW_DATA_DIR / "sample_knowledge_base.json"
PROCESSED_CORPUS_PATH = DATA_DIR / "processed" / "processed_knowledge_base.json"
PROCESSED_CORPUS_VERSIONS_DIR = DATA_DIR / "processed" / "versions"
CORPUS_MANIFEST_PATH = DATA_DIR / "processed" / "corpus_manifest.json"
PDF_INVENTORY_PATH = RAW_DATA_DIR / "pdf_inventory.json"
PDF_INVENTORY_HISTORY_PATH = RAW_DATA_DIR / "pdf_inventory_history.json"
PDF_INVENTORY_VERSIONS_DIR = RAW_DATA_DIR / "pdf_inventory_versions"
PDF_SOURCE_DIR = RAW_DATA_DIR

# Legacy JSON index
INDEX_PATH = INDEX_DATA_DIR / "index.json"

# FAISS index paths
FAISS_INDEX_PATH = INDEX_DATA_DIR / "faiss.index"
FAISS_METADATA_PATH = INDEX_DATA_DIR / "faiss_metadata.json"
# numpy fallback
NUMPY_INDEX_PATH = INDEX_DATA_DIR / "faiss.index.npy"

# App settings
load_dotenv(PROJECT_ROOT / ".env")

APP_NAME = os.getenv("APP_NAME", "Calma")
DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "local")
RETRIEVAL_BACKEND = os.getenv("RETRIEVAL_BACKEND", "faiss")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "calma_chunks")
ENABLE_GRAPH_RAG = os.getenv("ENABLE_GRAPH_RAG", "false").lower() in {"1", "true", "yes", "on"}
GRAPH_RAG_MIN_CHUNKS = int(os.getenv("GRAPH_RAG_MIN_CHUNKS", "400"))
GRAPH_RAG_MIN_QUERY_TERMS = int(os.getenv("GRAPH_RAG_MIN_QUERY_TERMS", "5"))
ROLLOUT_MODE = os.getenv("ROLLOUT_MODE", "stable")
ROLLOUT_TRAFFIC_PERCENT = int(os.getenv("ROLLOUT_TRAFFIC_PERCENT", "0"))
ENABLE_QDRANT_FALLBACK = os.getenv("ENABLE_QDRANT_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}
ENABLE_OLLAMA_FALLBACK = os.getenv("ENABLE_OLLAMA_FALLBACK", "true").lower() in {"1", "true", "yes", "on"}
MODEL_CONTRACT_VERSION = os.getenv("MODEL_CONTRACT_VERSION", "v1")
SENSITIVE_LOG_REDACTION_ENABLED = os.getenv("SENSITIVE_LOG_REDACTION_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "true").lower() in {"1", "true", "yes", "on"}
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "3"))
RERANK_MAX_CHARS = int(os.getenv("RERANK_MAX_CHARS", "1200"))
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
]
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
TOP_K = int(os.getenv("TOP_K", "5"))

# Demo retention defaults
RAW_CHAT_RETENTION_DAYS = int(os.getenv("RAW_CHAT_RETENTION_DAYS", "90"))
SESSION_SUMMARY_RETENTION_DAYS = int(os.getenv("SESSION_SUMMARY_RETENTION_DAYS", "365"))
SCREENING_RETENTION_DAYS = int(os.getenv("SCREENING_RETENTION_DAYS", "365"))
CONSENT_RETENTION_DAYS = int(os.getenv("CONSENT_RETENTION_DAYS", "365"))
AUDIT_LOG_RETENTION_DAYS = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "365"))

# Evidence gate thresholds
EVIDENCE_MIN_SCORE = float(os.getenv("EVIDENCE_MIN_SCORE", "0.22"))
EVIDENCE_MIN_CHUNKS = int(os.getenv("EVIDENCE_MIN_CHUNKS", "1"))

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
