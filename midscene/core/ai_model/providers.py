"""
AI Model Providers - Implementations for different AI services
"""

import json
from typing import Any, Dict, List, Optional, Type

import httpx
from loguru import logger
from pydantic import BaseModel

from .service import AIProvider, AIModelConfig, parse_json_response, create_usage_info


class OpenAIProvider(AIProvider):
    """OpenAI API provider"""
    
    async def call(
        self,
        messages: List[Dict[str, Any]], 
        config: AIModelConfig,
        response_schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call OpenAI API"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
        
        # Support structured output for compatible models
        if response_schema and "gpt-4" in config.model:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "schema": response_schema.model_json_schema()
                }
            }
        
        base_url = config.base_url or "https://api.openai.com"
        url = f"{base_url}/v1/chat/completions"
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            if response_schema:
                try:
                    parsed = parse_json_response(content)
                    validated = response_schema(**parsed)
                    return {
                        "content": validated.model_dump(),
                        "usage": create_usage_info(result.get('usage', {}))
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse structured response: {e}")
                    return {
                        "content": {"error": str(e), "raw_content": content},
                        "usage": create_usage_info(result.get('usage', {}))
                    }
            
            return {
                "content": content,
                "usage": create_usage_info(result.get('usage', {}))
            }


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider"""
    
    async def call(
        self,
        messages: List[Dict[str, Any]], 
        config: AIModelConfig,
        response_schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call Anthropic API"""
        headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert messages format for Anthropic
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        payload = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": anthropic_messages
        }
        
        if system_message:
            payload["system"] = system_message
        
        base_url = config.base_url or "https://api.anthropic.com"
        url = f"{base_url}/v1/messages"
        
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['content'][0]['text']
            
            if response_schema:
                try:
                    parsed = parse_json_response(content)
                    validated = response_schema(**parsed)
                    return {
                        "content": validated.model_dump(),
                        "usage": create_usage_info(result.get('usage', {}))
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse structured response: {e}")
                    return {
                        "content": {"error": str(e), "raw_content": content},
                        "usage": create_usage_info(result.get('usage', {}))
                    }
            
            return {
                "content": content,
                "usage": create_usage_info(result.get('usage', {}))
            }


class QwenProvider(AIProvider):
    """Alibaba Qwen API provider"""
    
    async def call(
        self,
        messages: List[Dict[str, Any]], 
        config: AIModelConfig,
        response_schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call Qwen API"""
        try:
            import dashscope
        except ImportError:
            raise ImportError("dashscope is required for Qwen provider. Install with: pip install dashscope")
        
        dashscope.api_key = config.api_key
        
        # Convert messages for Qwen
        qwen_messages = []
        for msg in messages:
            qwen_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        response = await dashscope.Generation.acall(
            model=config.model,
            messages=qwen_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            result_format='message'
        )
        
        if response.status_code == 200:
            content = response.output.choices[0]['message']['content']
            
            if response_schema:
                try:
                    parsed = parse_json_response(content)
                    validated = response_schema(**parsed)
                    return {
                        "content": validated.model_dump(),
                        "usage": create_usage_info(response.usage)
                    }
                except Exception as e:
                    logger.warning(f"Failed to parse structured response: {e}")
                    return {
                        "content": {"error": str(e), "raw_content": content},
                        "usage": create_usage_info(response.usage)
                    }
            
            return {
                "content": content,
                "usage": create_usage_info(response.usage)
            }
        else:
            raise Exception(f"Qwen API error: {response.message}")


class GeminiProvider(AIProvider):
    """Google Gemini API provider"""
    
    async def call(
        self,
        messages: List[Dict[str, Any]], 
        config: AIModelConfig,
        response_schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Call Gemini API"""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai is required for Gemini provider. Install with: pip install google-generativeai")
        
        genai.configure(api_key=config.api_key)
        model = genai.GenerativeModel(config.model)
        
        # Convert messages format for Gemini
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # Gemini doesn't have system role, prepend to first user message
                continue
            elif msg["role"] == "user":
                if isinstance(msg["content"], list):
                    # Handle multimodal content
                    parts = []
                    for part in msg["content"]:
                        if part["type"] == "text":
                            parts.append(part["text"])
                        elif part["type"] == "image_url":
                            # Convert base64 image to Gemini format
                            import base64
                            import io
                            from PIL import Image
                            
                            image_data = part["image_url"]["url"]
                            if image_data.startswith("data:image"):
                                image_data = image_data.split(",")[1]
                            
                            image_bytes = base64.b64decode(image_data)
                            image = Image.open(io.BytesIO(image_bytes))
                            parts.append(image)
                    
                    gemini_messages.append({"role": "user", "parts": parts})
                else:
                    gemini_messages.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg["content"]]})
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=config.max_tokens,
            temperature=config.temperature
        )
        
        response = await model.generate_content_async(
            gemini_messages,
            generation_config=generation_config
        )
        
        content = response.text
        
        if response_schema:
            try:
                parsed = parse_json_response(content)
                validated = response_schema(**parsed)
                return {
                    "content": validated.model_dump(),
                    "usage": create_usage_info({
                        "prompt_tokens": response.usage_metadata.prompt_token_count,
                        "completion_tokens": response.usage_metadata.candidates_token_count,
                        "total_tokens": response.usage_metadata.total_token_count
                    })
                }
            except Exception as e:
                logger.warning(f"Failed to parse structured response: {e}")
                return {
                    "content": {"error": str(e), "raw_content": content},
                    "usage": create_usage_info({
                        "prompt_tokens": response.usage_metadata.prompt_token_count,
                        "completion_tokens": response.usage_metadata.candidates_token_count,
                        "total_tokens": response.usage_metadata.total_token_count
                    })
                }
        
        return {
            "content": content,
            "usage": create_usage_info({
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count
            })
        }