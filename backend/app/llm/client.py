"""
GigMoney Guru - LLM Client

OpenAI-compatible client for generating conversation and explanations.
"""
import json
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from app.config import settings


class LLMClient:
    """
    OpenAI-compatible LLM client.
    Abstracts LLM calls for conversation and explainability agents.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.openai_api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Upgraded for better quality insights
        
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Generate text response from LLM.
        
        Args:
            prompt: User prompt with context
            system_prompt: System instructions
            temperature: Creativity (0-1)
            max_tokens: Max response length
            
        Returns:
            Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._fallback_response(prompt)
    
    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generate JSON response from LLM.
        
        Args:
            prompt: User prompt with context
            system_prompt: System instructions
            temperature: Lower for more deterministic JSON
            
        Returns:
            Parsed JSON dict
        """
        json_system = (system_prompt or "") + "\n\nRespond with valid JSON only."
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": json_system},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except Exception as e:
            print(f"LLM JSON Error: {e}")
            return {}
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Multi-turn chat with conversation history.
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            system_prompt: System instructions
            temperature: Creativity level
            
        Returns:
            Assistant response
        """
        all_messages = []
        
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        
        all_messages.extend(messages)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=all_messages,
                temperature=temperature,
                max_tokens=500,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"LLM Chat Error: {e}")
            return "Sorry, I'm having trouble right now. Please try again."
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when LLM fails."""
        if "allocation" in prompt.lower():
            return "Maine aaj ki kamai ko alag-alag buckets mein divide kar diya hai. Rent, EMI, aur fuel ke liye set aside ho gaya hai."
        elif "advance" in prompt.lower():
            return "Agar aapko is week cash ki zaroorat hai, toh main ek chhota advance suggest kar sakta hoon. No hidden fees, weekend mein repay ho jayega."
        elif "goal" in prompt.lower():
            return "Aapka savings goal achhi progress kar raha hai! Thoda aur effort se jaldi complete ho jayega."
        else:
            return "Main aapki madad karne ke liye yahan hoon. Kuch bhi poochho!"


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
