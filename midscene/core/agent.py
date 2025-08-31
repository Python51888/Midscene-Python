"""
Agent - Core automation controller that orchestrates AI and device interactions
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from .insight import Insight
from .types import (
    AbstractInterface, AgentOptions, UIContext, LocateResult, ExecutionResult,
    AssertResult, LocateOption, ExtractOption, TUserPrompt, InterfaceType,
    ScrollParam
)
from .ai_model import AIModelService, AIModelConfig


class TaskExecutor:
    """Task execution engine for agent operations"""
    
    def __init__(
        self,
        interface: AbstractInterface,
        insight: Insight,
        options: Optional[Dict] = None
    ):
        self.interface = interface
        self.insight = insight
        self.options = options or {}
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_ai_action(self, prompt: TUserPrompt, **kwargs) -> ExecutionResult:
        """Execute AI-driven action"""
        try:
            logger.info(f"Executing AI action: {prompt}")
            
            # Generate action plan using AI
            plan = await self._generate_action_plan(prompt, **kwargs)
            
            # Execute the plan
            result = await self._execute_plan(plan)
            
            # Record execution
            self.execution_history.append({
                "prompt": prompt,
                "plan": plan,
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"AI action failed: {e}")
            return ExecutionResult(success=False, error=str(e))
    
    async def _generate_action_plan(self, prompt: TUserPrompt, **kwargs) -> Dict[str, Any]:
        """Generate execution plan using AI"""
        context = await self.interface.get_context()
        
        # Build messages for action planning
        messages = [
            {
                "role": "system",
                "content": self._get_planning_system_prompt()
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"请分析当前页面，并制定执行以下操作的计划：{prompt}"
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
        
        # Get AI service from insight
        ai_service = self.insight.ai_service
        response = await ai_service.call_ai(messages=messages)
        
        # Parse action plan
        try:
            plan = json.loads(response["content"])
            return plan
        except json.JSONDecodeError:
            # Fallback: treat as simple action
            return {
                "type": "simple_action",
                "description": prompt,
                "steps": [{"action": "locate_and_interact", "target": prompt}]
            }
    
    async def _execute_plan(self, plan: Dict[str, Any]) -> ExecutionResult:
        """Execute action plan"""
        try:
            steps = plan.get("steps", [])
            results = []
            
            for step in steps:
                action = step.get("action")
                
                if action == "locate_and_interact":
                    result = await self._execute_locate_and_interact(step)
                elif action == "tap":
                    result = await self._execute_tap(step)
                elif action == "input":
                    result = await self._execute_input(step)
                elif action == "scroll":
                    result = await self._execute_scroll(step)
                else:
                    result = ExecutionResult(
                        success=False, 
                        error=f"Unknown action: {action}"
                    )
                
                results.append(result)
                
                if not result.success:
                    break
            
            overall_success = all(r.success for r in results)
            return ExecutionResult(
                success=overall_success,
                data={"steps": results}
            )
            
        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            return ExecutionResult(success=False, error=str(e))
    
    async def _execute_locate_and_interact(self, step: Dict[str, Any]) -> ExecutionResult:
        """Execute locate and interact step"""
        target = step.get("target", "")
        action_type = step.get("interaction", "tap")
        
        # Locate element
        locate_result = await self.insight.locate(target)
        
        if not locate_result.element:
            return ExecutionResult(
                success=False,
                error=f"Element not found: {target}"
            )
        
        # Interact with element
        element = locate_result.element
        
        if action_type == "tap":
            await element.tap()
        elif action_type == "input":
            text = step.get("text", "")
            await element.input_text(text)
        else:
            return ExecutionResult(
                success=False,
                error=f"Unknown interaction: {action_type}"
            )
        
        return ExecutionResult(
            success=True,
            data={"element": element, "action": action_type}
        )
    
    async def _execute_tap(self, step: Dict[str, Any]) -> ExecutionResult:
        """Execute tap step"""
        x = step.get("x")
        y = step.get("y")
        
        if x is not None and y is not None:
            await self.interface.tap(x, y)
            return ExecutionResult(success=True)
        
        target = step.get("target")
        if target:
            locate_result = await self.insight.locate(target)
            if locate_result.element:
                await locate_result.element.tap()
                return ExecutionResult(success=True)
        
        return ExecutionResult(
            success=False,
            error="No valid tap target specified"
        )
    
    async def _execute_input(self, step: Dict[str, Any]) -> ExecutionResult:
        """Execute input step"""
        text = step.get("text", "")
        target = step.get("target")
        
        if target:
            locate_result = await self.insight.locate(target)
            if locate_result.element:
                await locate_result.element.input_text(text)
                return ExecutionResult(success=True)
        else:
            await self.interface.input_text(text)
            return ExecutionResult(success=True)
        
        return ExecutionResult(
            success=False,
            error="Input target not found"
        )
    
    async def _execute_scroll(self, step: Dict[str, Any]) -> ExecutionResult:
        """Execute scroll step"""
        direction = step.get("direction", "down")
        distance = step.get("distance")
        
        await self.interface.scroll(direction, distance)
        return ExecutionResult(success=True)
    
    def _get_planning_system_prompt(self) -> str:
        """Get system prompt for action planning"""
        return """
你是一个专业的UI自动化规划助手，能够分析页面并制定操作计划。

请根据用户的操作要求，分析当前页面截图，制定详细的执行计划。

返回JSON格式的计划，包含：
{
    "type": "计划类型",
    "description": "计划描述", 
    "steps": [
        {
            "action": "动作类型(locate_and_interact/tap/input/scroll)",
            "target": "目标描述(用于定位)",
            "interaction": "交互类型(tap/input)",
            "text": "输入文本(仅input时)",
            "x": "坐标x(仅tap时)",
            "y": "坐标y(仅tap时)",
            "direction": "滚动方向(仅scroll时)"
        }
    ]
}

支持的动作类型：
- locate_and_interact: 定位元素并交互
- tap: 点击指定坐标或元素
- input: 输入文本
- scroll: 滚动页面

请确保计划步骤清晰、可执行。
        """.strip()


class Agent:
    """Core Agent class that orchestrates AI model and device interactions"""
    
    def __init__(
        self,
        interface: AbstractInterface,
        options: Optional[AgentOptions] = None
    ):
        """Initialize Agent
        
        Args:
            interface: Platform interface (web/android)
            options: Agent configuration options
        """
        self.interface = interface
        self.options = options or AgentOptions()
        
        # Initialize AI service
        self.ai_service = AIModelService()
        
        # Initialize insight engine
        self.insight = Insight(
            context_provider=self._get_ui_context,
            ai_service=self.ai_service,
            model_config=self._get_model_config()
        )
        
        # Initialize task executor
        self.task_executor = TaskExecutor(
            interface=interface,
            insight=self.insight,
            options={"agent_options": self.options}
        )
        
        # Execution state
        self.destroyed = False
        self.frozen_context: Optional[UIContext] = None
        
        logger.info(f"Agent initialized for {interface.interface_type}")
    
    async def ai_action(self, prompt: TUserPrompt, **kwargs) -> None:
        """Execute AI-driven action
        
        Args:
            prompt: Natural language description of action
            **kwargs: Additional options
        """
        self._check_not_destroyed()
        
        result = await self.task_executor.execute_ai_action(prompt, **kwargs)
        
        if not result.success:
            raise Exception(f"AI action failed: {result.error}")
    
    async def ai_locate(
        self, 
        prompt: TUserPrompt, 
        options: Optional[LocateOption] = None
    ) -> LocateResult:
        """Locate UI element using AI
        
        Args:
            prompt: Description of element to locate
            options: Locate options
            
        Returns:
            LocateResult containing found element
        """
        self._check_not_destroyed()
        return await self.insight.locate(prompt, options)
    
    async def ai_extract(
        self, 
        prompt: TUserPrompt, 
        options: Optional[ExtractOption] = None
    ) -> Any:
        """Extract data from UI using AI
        
        Args:
            prompt: Description of data to extract
            options: Extract options
            
        Returns:
            Extracted data
        """
        self._check_not_destroyed()
        result = await self.insight.extract(prompt, options)
        return result["data"]
    
    async def ai_assert(
        self, 
        assertion: TUserPrompt, 
        message: Optional[str] = None,
        options: Optional[ExtractOption] = None
    ) -> None:
        """Assert condition using AI
        
        Args:
            assertion: Condition to assert
            message: Custom error message
            options: Extract options
            
        Raises:
            AssertionError: If assertion fails
        """
        self._check_not_destroyed()
        result = await self.insight.assert_condition(assertion, options)
        
        if not result.passed:
            error_msg = message or f"Assertion failed: {assertion}"
            if result.message:
                error_msg += f"\nReason: {result.message}"
            raise AssertionError(error_msg)
    
    async def ai_wait_for(
        self,
        condition: TUserPrompt,
        timeout_ms: int = 10000,
        check_interval_ms: int = 1000
    ) -> None:
        """Wait for condition to be true
        
        Args:
            condition: Condition to wait for
            timeout_ms: Timeout in milliseconds
            check_interval_ms: Check interval in milliseconds
        """
        self._check_not_destroyed()
        
        start_time = asyncio.get_event_loop().time()
        timeout_seconds = timeout_ms / 1000
        check_interval_seconds = check_interval_ms / 1000
        
        while True:
            try:
                result = await self.insight.assert_condition(
                    condition, 
                    ExtractOption(do_not_throw_error=True)
                )
                
                if result.passed:
                    return
                    
            except Exception as e:
                logger.debug(f"Wait for condition check failed: {e}")
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout_seconds:
                raise TimeoutError(f"Timeout waiting for condition: {condition}")
            
            # Wait before next check
            await asyncio.sleep(check_interval_seconds)
    
    async def tap(self, x: float, y: float) -> None:
        """Tap at coordinates
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self._check_not_destroyed()
        await self.interface.tap(x, y)
    
    async def input_text(self, text: str) -> None:
        """Input text
        
        Args:
            text: Text to input
        """
        self._check_not_destroyed()
        await self.interface.input_text(text)
    
    async def scroll(self, params: ScrollParam) -> None:
        """Scroll page
        
        Args:
            params: Scroll parameters
        """
        self._check_not_destroyed()
        await self.interface.scroll(params.direction, params.distance)
    
    async def get_context(self) -> UIContext:
        """Get current UI context"""
        self._check_not_destroyed()
        return await self._get_ui_context("manual")
    
    def freeze_context(self) -> None:
        """Freeze current UI context for consistent operations"""
        # Implementation would freeze the current context
        pass
    
    def unfreeze_context(self) -> None:
        """Unfreeze UI context"""
        self.frozen_context = None
    
    async def destroy(self) -> None:
        """Destroy agent and cleanup resources"""
        if not self.destroyed:
            logger.info("Destroying agent")
            self.destroyed = True
            
            # Cleanup implementation
            # e.g., close browser, disconnect from device, etc.
    
    def _check_not_destroyed(self) -> None:
        """Check if agent is not destroyed"""
        if self.destroyed:
            raise RuntimeError("Agent has been destroyed")
    
    async def _get_ui_context(self, action: str) -> UIContext:
        """Get UI context for insight operations"""
        if self.frozen_context:
            return self.frozen_context
        
        return await self.interface.get_context()
    
    def _get_model_config(self) -> Optional[AIModelConfig]:
        """Get AI model configuration"""
        if self.options.model_config:
            return self.options.model_config()
        return None
    
    @property
    def interface_type(self) -> InterfaceType:
        """Get interface type"""
        return self.interface.interface_type