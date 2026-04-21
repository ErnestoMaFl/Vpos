from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class STTProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio bytes to text."""
        pass

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, system_message: str = None, json_mode: bool = False) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any], system_message: str = None) -> Dict[str, Any]:
        """Generate a structured JSON response matching a schema."""
        pass
