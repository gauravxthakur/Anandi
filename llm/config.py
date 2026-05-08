import os
from typing import Literal

# LLM Backend Selection: 'ollama' or 'vps'
LLM_BACKEND: Literal["ollama", "vps"] = os.getenv("LLM_BACKEND", "ollama")

# Base URLs for different backends
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
VPS_BASE_URL = os.getenv("VPS_BASE_URL", "http://your-vps:8000/v1")

# Default model to use
LLM_MODEL = os.getenv("LLM_MODEL", "phi4-mini")

# Temperature for generation (0 = more deterministic)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

# Get the appropriate base URL based on backend
def get_base_url() -> str:
    if LLM_BACKEND == "ollama":
        return OLLAMA_BASE_URL
    elif LLM_BACKEND == "vps":
        return VPS_BASE_URL
    else:
        raise ValueError(f"Invalid LLM_BACKEND: {LLM_BACKEND}. Must be 'ollama' or 'vps'")
