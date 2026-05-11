from openai import OpenAI
from .config import get_base_url, LLM_MODEL, LLM_TEMPERATURE


class LLMClient:
    """OpenAI-compatible client for Ollama and VPS backends."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize LLM client with OpenAI-compatible API.
        
        Args:
            base_url: Optional override for base URL. If not provided,
                     uses URL from config based on LLM_BACKEND env var.
        """
        if base_url is None:
            base_url = get_base_url()
        
        # OpenAI-compatible client (dummy API key for local Ollama)
        self.client = OpenAI(
            base_url=base_url,
            api_key="dummy"  # Ollama doesn't require real API key
        )
        self.model = LLM_MODEL
        self.temperature = LLM_TEMPERATURE
    
    def chat(self, messages: list) -> str:
        """
        Send chat messages to LLM and return response text.
        
        Args:
            messages: List of message dicts in OpenAI format:
                      [{"role": "user", "content": "..."}, ...]
        
        Returns:
            str: The model's response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content
    
    def chat_with_system(self, system_prompt: str, user_prompt: str) -> str:
        """
        Convenience method for system + user prompt pattern.
        
        Args:
            system_prompt: System message content
            user_prompt: User message content
        
        Returns:
            str: The model's response text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat(messages)
