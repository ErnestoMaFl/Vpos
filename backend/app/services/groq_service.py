import os
import json
from enum import Enum
from typing import Dict, Any, Optional
from groq import AsyncGroq
from app.services.interfaces import STTProvider, LLMProvider
from app.core.config import settings

class GroqModel(Enum):
    LLAMA_3_70B = "llama-3.3-70b-versatile"
    LLAMA_3_8B = "llama-3.1-8b-instant"
    WHISPER_TURBO = "whisper-large-v3-turbo"
    WHISPER = "whisper-large-v3"
    MIXTRAL = "mixtral-8x7b-32768"

class GroqService(STTProvider, LLMProvider):
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        # TODO: Implement retries/circuit breaker here

    async def transcribe(self, audio_data: bytes) -> str:
        # Note: Groq requires file-like object with name
        # We might need to wrap audio_data in a BytesIO with a .name attribute
        # For now, this is a placeholder for the actual API call structure
        try:
            transcription = await self.client.audio.transcriptions.create(
                file=("audio.webm", audio_data),
                model=GroqModel.WHISPER_TURBO.value,
                # prompt="Contexto...", # Optional context
                response_format="json",
                language="es"
            )
            return transcription.text
        except Exception as e:
            # Fallback logic could go here (e.g., try standard Whisper)
            print(f"STT Error: {e}")
            raise e

    async def generate_response(self, prompt: str, system_message: str = None, json_mode: bool = False, model: str = None) -> str:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        # FALLBACK STRATEGY: 
        # Verified Available Models:
        # llama-3.1-8b-instant, qwen/qwen3-32b, moonshotai/kimi-k2-instruct
        
        fallback_chain = [
            model if model else GroqModel.LLAMA_3_70B.value, # Primary (might contain 70b)
            GroqModel.LLAMA_3_8B.value,                      # Fallback 1: Fast Llama
            "qwen/qwen3-32b",                                # Fallback 2: Qwen
            "moonshotai/kimi-k2-instruct"                    # Fallback 3: Kimi
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        fallback_chain = [x for x in fallback_chain if not (x in seen or seen.add(x))]

        response_format = {"type": "json_object"} if json_mode else None

        print(f"[DEBUG - GroqService] Starting LLM Call Chain: {fallback_chain}")
        import time
        start_time = time.time()
        
        last_error = None
        
        for current_model in fallback_chain:
            try:
                print(f"[DEBUG - GroqService] Attempting with model: {current_model}")
                chat_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model=current_model,
                    response_format=response_format,
                    temperature=0.1
                )
                duration = time.time() - start_time
                print(f"[DEBUG - GroqService] LLM Call Success ({current_model}) in {duration:.2f}s")
                return chat_completion.choices[0].message.content
                
            except Exception as e:
                # Check for Rate Limit (429) or Server Error (5xx)
                error_msg = str(e).lower()
                is_retryable = "429" in error_msg or "rate limit" in error_msg or "503" in error_msg or "500" in error_msg
                
                print(f"[WARNING - GroqService] Model {current_model} failed. Error: {e}")
                last_error = e
                
                if not is_retryable:
                    # If it's a validation error or bad request, don't retry with other models (they will likely fail too)
                    # BUT for now, let's be aggressive and retry everything unless we are sure.
                    pass 
                
                # Continue to next model in loop
        
        # If we exited the loop, all models failed
        print(f"[ERROR - GroqService] All models in chain failed. Total time: {time.time() - start_time:.2f}s")
        raise last_error

    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any], system_message: str = None) -> Dict[str, Any]:
        # Append schema instruction to prompt if not using function calling (Groq supports JSON mode well)
        schema_instruction = f"\n\nResponde EXCLUSIVAMENTE en formato JSON válido que cumpla este esquema:\n{json.dumps(schema, indent=2)}"
        full_system = (system_message or "Eres un asistente útil.") + schema_instruction
        
        response_text = await self.generate_response(prompt, system_message=full_system, json_mode=True)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Simple retry or fix logic could exist here
            raise ValueError("LLM did not return valid JSON")

groq_service = GroqService()
