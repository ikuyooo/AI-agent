import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL    = os.getenv("LLM_MODEL",    "gpt-4o-mini")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.2:3b")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY",  "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
EMBEDDING_MODEL    = os.getenv("EMBEDDING_MODEL",    "all-MiniLM-L6-v2")

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/research_agent.db")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "data/vector_db")

CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE",    "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
SECTION_CONFIDENCE_THRESHOLD = float(os.getenv("SECTION_CONFIDENCE_THRESHOLD", "0.3"))

KNOWN_SECTIONS = [
    "abstract", "introduction", "related work", "background",
    "literature review", "methodology", "method", "methods",
    "proposed method", "approach", "experiment", "experiments",
    "experimental setup", "evaluation", "results", "result",
    "discussion", "conclusion", "conclusions", "limitation",
    "limitations", "future work", "references", "acknowledgment",
]
