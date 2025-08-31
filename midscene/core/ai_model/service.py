"""
AI Model Service - Unified interface for different AI providers
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Union

import httpx
from loguru import logger
from pydantic import BaseModel

from ..types import AIUsageInfo


class AIModelConfig(BaseModel):
    """AI model configuration"""
    provider: str  # openai, anthropic, qwen, gemini
    model: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 60


class AIProvider(ABC):
    """Abstract base class for AI service providers"""
    
    @abstractmethod
    async def call(
        self,
        messages: List[Dict[str, Any]],
        config: AIModelConfig,
        response_schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call AI service"""
        pass


class AIModelService:
    """Unified AI model service interface"""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self._register_providers()
    
    def _register_providers(self):
        """Register available AI providers"""
        from .providers import (
            OpenAIProvider, 
            AnthropicProvider, 
            QwenProvider, 
            GeminiProvider
        )
        
        self.providers['openai'] = OpenAIProvider()
        self.providers['anthropic'] = AnthropicProvider()
        self.providers['qwen'] = QwenProvider()
        self.providers['gemini'] = GeminiProvider()
    
    async def call_ai(
        self,
        messages: List[Dict[str, Any]], 
        response_schema: Optional[Type[BaseModel]] = None,
        model_config: Optional[AIModelConfig] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call AI model with unified interface"""
        config = model_config or self._get_default_config()
        provider = self.providers.get(config.provider)
        
        if not provider:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        try:
            logger.debug(f"Calling AI provider: {config.provider}")
            result = await provider.call(
                messages=messages,
                config=config,
                response_schema=response_schema,
                **kwargs
            )
            return result
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            raise
    
    def _get_default_config(self) -> AIModelConfig:
        """Get default configuration"""
        import os
        
        # Try to get from environment variables
        provider = os.getenv('MIDSCENE_AI_PROVIDER', 'openai')
        model = os.getenv('MIDSCENE_AI_MODEL', 'gpt-4-vision-preview')
        api_key = os.getenv('MIDSCENE_AI_API_KEY', '')
        base_url = os.getenv('MIDSCENE_AI_BASE_URL')
        
        if not api_key:
            raise ValueError(
                "AI API key not configured. Set MIDSCENE_AI_API_KEY environment variable."
            )
        
        return AIModelConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url
        )


def parse_json_response(content: str) -> Dict[str, Any]:
    """Parse JSON response from AI model"""
    try:
        # Try to parse as JSON directly
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON-like content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Failed to parse JSON from response: {content}")


def create_usage_info(usage_data: Dict[str, Any]) -> AIUsageInfo:
    """Create AIUsageInfo from provider response"""
    return AIUsageInfo(
        prompt_tokens=usage_data.get('prompt_tokens', 0),
        completion_tokens=usage_data.get('completion_tokens', 0),
        total_tokens=usage_data.get('total_tokens', 0),
        cost=usage_data.get('cost')
    )