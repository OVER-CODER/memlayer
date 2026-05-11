"""
LLM service layer with Gemini integration.
Designed to be model-agnostic for future extensibility.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import google.generativeai as genai
from app.core.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def generate_with_context(self, context: str, query: str, **kwargs) -> str:
        """Generate a response with contextualized prompt."""
        pass


class GeminiProvider(LLMProvider):
    """Gemini API integration."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-pro"):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name

        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY env var.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from Gemini."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", 0.7),
                    top_p=kwargs.get("top_p", 0.9),
                    top_k=kwargs.get("top_k", 40),
                    max_output_tokens=kwargs.get("max_tokens", 2048),
                ),
                safety_settings=kwargs.get("safety_settings", []),
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")

    def generate_with_context(self, context: str, query: str, **kwargs) -> str:
        """Generate response with contextualized prompt."""
        system_prompt = """You are a helpful AI assistant with access to a persistent semantic memory system. 
Use the provided context and memory to give accurate, personalized responses.
Refer to relevant memories when they provide useful context."""

        full_prompt = f"""{system_prompt}

{context}

Query: {query}

Response:"""

        return self.generate(full_prompt, **kwargs)


class LLMService:
    """Service for LLM interactions with pluggable providers."""

    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or GeminiProvider()

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response."""
        return self.provider.generate(prompt, **kwargs)

    def generate_with_context(self, context: str, query: str, **kwargs) -> str:
        """Generate response with context."""
        return self.provider.generate_with_context(context, query, **kwargs)

    def extract_memory_objects(self, response: str) -> List[Dict]:
        """
        Extract potential memory objects from the response.
        This is a simple implementation that identifies important facts.
        """
        # In a real system, this could use NER or structured extraction
        # For now, we'll flag responses as potential memories
        return [
            {
                "type": "response",
                "content": response,
                "importance": 0.7,
            }
        ]


# Global LLM service instance
_llm_service: LLMService = None


def get_llm_service() -> LLMService:
    """Get or create the global LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
