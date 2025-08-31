"""
Insight - AI-powered UI understanding and reasoning engine
"""

import asyncio
import base64
import json
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable

from loguru import logger
from pydantic import BaseModel

from .ai_model import AIModelService, AIModelConfig
from .types import (
    UIContext, BaseElement, LocateResult, ExecutionResult, AssertResult,
    AIUsageInfo, LocateOption, ExtractOption, TUserPrompt, InsightAction
)


class LocateResponse(BaseModel):
    """AI locate response schema"""
    elements: List[Dict[str, Any]]
    reasoning: str
    confidence: float
    errors: List[str] = []


class ExtractResponse(BaseModel):
    """AI extract response schema"""
    data: Any
    reasoning: str
    confidence: float
    errors: List[str] = []


class AssertResponse(BaseModel):
    """AI assert response schema"""
    passed: bool
    reasoning: str
    confidence: float
    message: str = ""


class Insight:
    """AI-powered UI understanding and reasoning engine"""
    
    def __init__(
        self,
        context_provider: Union[
            UIContext, 
            Callable[[InsightAction], Union[UIContext, Awaitable[UIContext]]]
        ],
        ai_service: Optional[AIModelService] = None,
        model_config: Optional[AIModelConfig] = None
    ):
        """Initialize Insight engine
        
        Args:
            context_provider: UI context or function to get context
            ai_service: AI model service instance
            model_config: AI model configuration
        """
        if callable(context_provider):
            self.context_provider = context_provider
        else:
            self.context_provider = lambda _: context_provider
            
        self.ai_service = ai_service or AIModelService()
        self.model_config = model_config
        self._dump_subscribers: List[Callable] = []
    
    async def locate(
        self, 
        prompt: TUserPrompt, 
        options: Optional[LocateOption] = None
    ) -> LocateResult:
        """Locate UI element using AI
        
        Args:
            prompt: Description of element to locate
            options: Locate options
            
        Returns:
            LocateResult containing found element or None
        """
        options = options or LocateOption()
        
        try:
            # Get UI context
            context = await self._get_context(InsightAction.LOCATE)
            
            # Build AI messages
            messages = self._build_locate_messages(prompt, context, options)
            
            # Call AI model
            response = await self.ai_service.call_ai(
                messages=messages,
                response_schema=LocateResponse,
                model_config=self.model_config
            )
            
            # Process response
            locate_response = LocateResponse(**response["content"])
            element = self._process_locate_response(locate_response, context)
            
            # Notify dump subscribers
            await self._notify_dump_subscribers({
                "type": "locate",
                "prompt": prompt,
                "element": element,
                "response": locate_response,
                "usage": response.get("usage")
            })
            
            return LocateResult(
                element=element,
                rect=element.rect if element else None
            )
            
        except Exception as e:
            logger.error(f"Locate failed: {e}")
            await self._notify_dump_subscribers({
                "type": "locate",
                "prompt": prompt,
                "error": str(e)
            })
            raise
    
    async def extract(
        self, 
        prompt: TUserPrompt, 
        options: Optional[ExtractOption] = None
    ) -> Dict[str, Any]:
        """Extract data from UI using AI
        
        Args:
            prompt: Description of data to extract
            options: Extract options
            
        Returns:
            Extracted data
        """
        options = options or ExtractOption()
        
        try:
            # Get UI context
            context = await self._get_context(InsightAction.EXTRACT)
            
            # Build AI messages
            messages = self._build_extract_messages(prompt, context, options)
            
            # Call AI model
            response = await self.ai_service.call_ai(
                messages=messages,
                response_schema=ExtractResponse,
                model_config=self.model_config
            )
            
            # Process response
            extract_response = ExtractResponse(**response["content"])
            
            # Notify dump subscribers
            await self._notify_dump_subscribers({
                "type": "extract",
                "prompt": prompt,
                "data": extract_response.data,
                "response": extract_response,
                "usage": response.get("usage")
            })
            
            result = {
                "data": extract_response.data,
                "usage": response.get("usage")
            }
            
            if options.return_thought:
                result["thought"] = extract_response.reasoning
            
            return result
            
        except Exception as e:
            logger.error(f"Extract failed: {e}")
            await self._notify_dump_subscribers({
                "type": "extract",
                "prompt": prompt,
                "error": str(e)
            })
            raise
    
    async def assert_condition(
        self, 
        assertion: TUserPrompt, 
        options: Optional[ExtractOption] = None
    ) -> AssertResult:
        """Assert condition using AI
        
        Args:
            assertion: Condition to assert
            options: Extract options
            
        Returns:
            AssertResult with pass/fail status
        """
        options = options or ExtractOption()
        
        try:
            # Get UI context
            context = await self._get_context(InsightAction.ASSERT)
            
            # Build AI messages
            messages = self._build_assert_messages(assertion, context, options)
            
            # Call AI model
            response = await self.ai_service.call_ai(
                messages=messages,
                response_schema=AssertResponse,
                model_config=self.model_config
            )
            
            # Process response
            assert_response = AssertResponse(**response["content"])
            
            # Notify dump subscribers
            await self._notify_dump_subscribers({
                "type": "assert",
                "assertion": assertion,
                "passed": assert_response.passed,
                "response": assert_response,
                "usage": response.get("usage")
            })
            
            return AssertResult(
                passed=assert_response.passed,
                thought=assert_response.reasoning,
                message=assert_response.message
            )
            
        except Exception as e:
            logger.error(f"Assert failed: {e}")
            await self._notify_dump_subscribers({
                "type": "assert",
                "assertion": assertion,
                "error": str(e)
            })
            raise
    
    async def describe(self, point: tuple[float, float]) -> Dict[str, Any]:
        """Describe element at specific point
        
        Args:
            point: (x, y) coordinates
            
        Returns:
            Description of element at point
        """
        try:
            context = await self._get_context(InsightAction.EXTRACT)
            
            messages = [
                {
                    "role": "system",
                    "content": self._get_describe_system_prompt()
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"请描述坐标 ({point[0]}, {point[1]}) 处的UI元素"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{context.screenshot_base64}"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.ai_service.call_ai(
                messages=messages,
                model_config=self.model_config
            )
            
            return {
                "description": response["content"],
                "usage": response.get("usage")
            }
            
        except Exception as e:
            logger.error(f"Describe failed: {e}")
            raise
    
    def add_dump_subscriber(self, subscriber: Callable):
        """Add dump subscriber for debugging"""
        self._dump_subscribers.append(subscriber)
    
    async def _get_context(self, action: InsightAction) -> UIContext:
        """Get UI context for action"""
        if asyncio.iscoroutinefunction(self.context_provider):
            return await self.context_provider(action)
        else:
            return self.context_provider(action)
    
    def _build_locate_messages(
        self, 
        prompt: TUserPrompt, 
        context: UIContext, 
        options: LocateOption
    ) -> List[Dict[str, Any]]:
        """Build messages for locate operation"""
        system_prompt = self._get_locate_system_prompt(options)
        
        user_content = [
            {
                "type": "text",
                "text": f"请定位以下UI元素：{prompt}"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{context.screenshot_base64}"
                }
            }
        ]
        
        if options.deep_think:
            user_content.append({
                "type": "text",
                "text": "请进行深度分析，仔细考虑元素的位置、特征和上下文。"
            })
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def _build_extract_messages(
        self, 
        prompt: TUserPrompt, 
        context: UIContext, 
        options: ExtractOption
    ) -> List[Dict[str, Any]]:
        """Build messages for extract operation"""
        system_prompt = self._get_extract_system_prompt()
        
        user_content = [
            {
                "type": "text",
                "text": f"请从当前页面提取以下数据：{prompt}"
            }
        ]
        
        if options.screenshot_included:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{context.screenshot_base64}"
                }
            })
        
        if options.dom_included:
            # Include DOM information if needed
            dom_info = self._get_dom_description(context)
            user_content.append({
                "type": "text",
                "text": f"页面结构信息：{dom_info}"
            })
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def _build_assert_messages(
        self, 
        assertion: TUserPrompt, 
        context: UIContext, 
        options: ExtractOption
    ) -> List[Dict[str, Any]]:
        """Build messages for assert operation"""
        system_prompt = self._get_assert_system_prompt()
        
        user_content = [
            {
                "type": "text",
                "text": f"请验证以下条件是否成立：{assertion}"
            }
        ]
        
        if options.screenshot_included:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{context.screenshot_base64}"
                }
            })
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def _process_locate_response(
        self, 
        response: LocateResponse, 
        context: UIContext
    ) -> Optional[BaseElement]:
        """Process locate response to find matching element"""
        if response.errors:
            logger.warning(f"AI locate errors: {response.errors}")
            return None
        
        if not response.elements:
            return None
        
        # For now, return the first element found
        # In a full implementation, we would match by ID or other criteria
        element_info = response.elements[0]
        
        # Find matching element in context
        for element in context.content:
            if self._element_matches(element, element_info):
                return element
        
        return None
    
    def _element_matches(self, element: BaseElement, info: Dict[str, Any]) -> bool:
        """Check if element matches AI description"""
        # Simple matching logic - can be enhanced
        if "id" in info:
            return element.id == info["id"]
        
        if "text" in info:
            return info["text"].lower() in element.content.lower()
        
        return False
    
    def _get_dom_description(self, context: UIContext) -> str:
        """Get DOM description from context"""
        elements = []
        for element in context.content:
            if element.is_visible:
                elements.append({
                    "id": element.id,
                    "content": element.content,
                    "type": element.node_type,
                    "rect": {
                        "left": element.rect.left,
                        "top": element.rect.top,
                        "width": element.rect.width,
                        "height": element.rect.height
                    }
                })
        
        return json.dumps(elements, ensure_ascii=False)
    
    async def _notify_dump_subscribers(self, dump_data: Dict[str, Any]):
        """Notify all dump subscribers"""
        for subscriber in self._dump_subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(dump_data)
                else:
                    subscriber(dump_data)
            except Exception as e:
                logger.warning(f"Dump subscriber failed: {e}")
    
    def _get_locate_system_prompt(self, options: LocateOption) -> str:
        """Get system prompt for locate operation"""
        return """
你是一个专业的UI自动化助手，能够通过分析截图准确定位UI元素。

请根据用户的描述，在截图中找到对应的UI元素。你需要：

1. 仔细观察截图中的所有UI元素
2. 根据用户描述找到最匹配的元素
3. 返回JSON格式的结果，包含：
   - elements: 找到的元素列表，每个元素包含id、坐标等信息
   - reasoning: 你的分析过程
   - confidence: 置信度(0-1)
   - errors: 如果有错误或找不到元素，在这里说明

请确保定位准确，如果不确定或找不到元素，请在errors中说明原因。
        """.strip()
    
    def _get_extract_system_prompt(self) -> str:
        """Get system prompt for extract operation"""
        return """
你是一个专业的数据提取助手，能够从UI截图和页面结构中提取结构化数据。

请根据用户的要求，从当前页面提取所需数据。你需要：

1. 仔细分析截图和页面结构
2. 识别相关的数据内容
3. 返回JSON格式的结果，包含：
   - data: 提取的数据，格式按用户要求
   - reasoning: 你的提取过程说明
   - confidence: 置信度(0-1)
   - errors: 如果提取失败，在这里说明原因

请确保数据准确完整，保持原始格式和结构。
        """.strip()
    
    def _get_assert_system_prompt(self) -> str:
        """Get system prompt for assert operation"""
        return """
你是一个专业的页面状态验证助手，能够通过分析截图判断页面状态是否符合预期。

请根据用户的断言条件，验证当前页面状态。你需要：

1. 仔细分析当前页面截图
2. 理解用户的断言条件
3. 返回JSON格式的结果，包含：
   - passed: 断言是否通过(true/false)
   - reasoning: 你的判断依据和分析过程
   - confidence: 置信度(0-1)
   - message: 如果断言失败，说明具体原因

请确保判断准确，提供清晰的分析依据。
        """.strip()
    
    def _get_describe_system_prompt(self) -> str:
        """Get system prompt for describe operation"""
        return """
你是一个专业的UI分析助手，能够详细描述指定位置的UI元素。

请分析截图中指定坐标位置的UI元素，提供详细描述，包括：
- 元素类型（按钮、文本、图片等）
- 元素内容（文本内容、标签等）
- 元素状态（可点击、已选中等）
- 元素特征（颜色、大小、位置等）

请用简洁准确的语言描述，便于后续的自动化操作定位。
        """.strip()