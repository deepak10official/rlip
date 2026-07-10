"""Runtime settings for the billing agent workflow."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseModel):
    project_root: Path = PROJECT_ROOT
    documents_root: Path = PROJECT_ROOT / "documents"
    memory_root: Path = PROJECT_ROOT / ".agent_memory"
    results_root: Path = Path(os.getenv("AUDIT_RESULTS_ROOT", PROJECT_ROOT / "backend" / "results"))
    model: str = os.getenv("OPENAI_MODEL", "gpt-5.5")
    fast_model: str = os.getenv("OPENAI_FAST_MODEL", "gpt-5.4-mini")
    vision_model: str = os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gpt-5.5"))
    max_document_chars: int = int(os.getenv("MAX_DOCUMENT_CHARS", "9000"))
    max_vision_pages_per_document: int = int(os.getenv("MAX_VISION_PAGES_PER_DOCUMENT", "2"))

    @property
    def api_key_present(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))


settings = Settings()
