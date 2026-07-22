"""Centralized configuration loaded from environment variables."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    chroma_db_dir: str = os.getenv("CHROMA_DB_DIR", "./chroma_db")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./habit_coach.db")
    llm_model_name: str = os.getenv("LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
    hf_token: str | None = os.getenv("HF_TOKEN", None)
    llm_provider: str = os.getenv("LLM_PROVIDER", "together")

    @property
    def sqlite_path(self) -> str:
        return self.database_url.replace("sqlite:///", "")


settings = Settings()
