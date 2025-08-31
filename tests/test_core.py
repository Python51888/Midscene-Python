"""
Test suite for Midscene Python core functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from midscene.core.types import UIContext, Size, Rect, BaseElement, NodeType
from midscene.core.insight import Insight
from midscene.core.agent import Agent


class MockInterface:
    """Mock interface for testing"""
    
    def __init__(self):
        self.interface_type = "mock"
        self._context = None
    
    async def get_context(self):
        if self._context:
            return self._context
        
        # Return mock context
        return UIContext(
            screenshot_base64="mock_screenshot",
            size=Size(width=1920, height=1080),
            content=[
                BaseElement(
                    id="test_element",
                    content="Test Button",
                    rect=Rect(left=100, top=100, width=200, height=50),
                    center=(200, 125),
                    node_type=NodeType.BUTTON
                )
            ],
            tree=Mock()
        )
    
    async def action_space(self):
        return ["tap", "input", "scroll"]
    
    async def tap(self, x, y):
        pass
    
    async def input_text(self, text):
        pass
    
    async def scroll(self, direction, distance=None):
        pass


@pytest.fixture
def mock_interface():
    """Mock interface fixture"""
    return MockInterface()


@pytest.fixture
def mock_ai_service():
    """Mock AI service fixture"""
    ai_service = Mock()
    ai_service.call_ai = AsyncMock(return_value={
        "content": {
            "elements": [{"id": "test_element", "reason": "test"}],
            "reasoning": "test reasoning",
            "confidence": 0.9,
            "errors": []
        },
        "usage": {"total_tokens": 100}
    })
    return ai_service


class TestInsight:
    """Test Insight AI engine"""
    
    @pytest.mark.asyncio
    async def test_locate_element(self, mock_interface, mock_ai_service):
        """Test element location"""
        insight = Insight(
            context_provider=mock_interface.get_context,
            ai_service=mock_ai_service
        )
        
        result = await insight.locate("test button")
        
        assert result.element is not None
        assert result.element.id == "test_element"
        mock_ai_service.call_ai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extract_data(self, mock_interface, mock_ai_service):
        """Test data extraction"""
        # Mock extract response
        mock_ai_service.call_ai.return_value = {
            "content": {
                "data": {"title": "Test Page", "items": ["item1", "item2"]},
                "reasoning": "extracted data",
                "confidence": 0.9,
                "errors": []
            },
            "usage": {"total_tokens": 150}
        }
        
        insight = Insight(
            context_provider=mock_interface.get_context,
            ai_service=mock_ai_service
        )
        
        result = await insight.extract("extract page data")
        
        assert result["data"]["title"] == "Test Page"
        assert len(result["data"]["items"]) == 2
    
    @pytest.mark.asyncio
    async def test_assert_condition(self, mock_interface, mock_ai_service):
        """Test condition assertion"""
        # Mock assert response
        mock_ai_service.call_ai.return_value = {
            "content": {
                "passed": True,
                "reasoning": "condition is met",
                "confidence": 0.95,
                "message": "success"
            },
            "usage": {"total_tokens": 80}
        }
        
        insight = Insight(
            context_provider=mock_interface.get_context,
            ai_service=mock_ai_service
        )
        
        result = await insight.assert_condition("page is loaded")
        
        assert result.passed is True
        assert result.thought == "condition is met"


class TestAgent:
    """Test Agent functionality"""
    
    @pytest.mark.asyncio
    async def test_agent_creation(self, mock_interface):
        """Test agent creation"""
        agent = Agent(mock_interface)
        
        assert agent.interface == mock_interface
        assert agent.insight is not None
        assert agent.task_executor is not None
        assert agent.destroyed is False
    
    @pytest.mark.asyncio
    async def test_ai_locate(self, mock_interface, mock_ai_service):
        """Test AI locate through agent"""
        agent = Agent(mock_interface)
        agent.insight.ai_service = mock_ai_service
        
        result = await agent.ai_locate("test button")
        
        assert result.element is not None
        assert result.element.id == "test_element"
    
    @pytest.mark.asyncio
    async def test_ai_extract(self, mock_interface, mock_ai_service):
        """Test AI extract through agent"""
        # Mock extract response
        mock_ai_service.call_ai.return_value = {
            "content": {
                "data": {"username": "testuser"},
                "reasoning": "extracted username",
                "confidence": 0.9,
                "errors": []
            },
            "usage": {"total_tokens": 100}
        }
        
        agent = Agent(mock_interface)
        agent.insight.ai_service = mock_ai_service
        
        result = await agent.ai_extract("extract username")
        
        assert result["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_ai_assert_success(self, mock_interface, mock_ai_service):
        """Test AI assert success"""
        # Mock assert response
        mock_ai_service.call_ai.return_value = {
            "content": {
                "passed": True,
                "reasoning": "condition met",
                "confidence": 0.9,
                "message": "success"
            },
            "usage": {"total_tokens": 80}
        }
        
        agent = Agent(mock_interface)
        agent.insight.ai_service = mock_ai_service
        
        # Should not raise exception
        await agent.ai_assert("page is loaded")
    
    @pytest.mark.asyncio
    async def test_ai_assert_failure(self, mock_interface, mock_ai_service):
        """Test AI assert failure"""
        # Mock assert response
        mock_ai_service.call_ai.return_value = {
            "content": {
                "passed": False,
                "reasoning": "condition not met",
                "confidence": 0.9,
                "message": "login failed"
            },
            "usage": {"total_tokens": 80}
        }
        
        agent = Agent(mock_interface)
        agent.insight.ai_service = mock_ai_service
        
        # Should raise AssertionError
        with pytest.raises(AssertionError):
            await agent.ai_assert("user is logged in")
    
    @pytest.mark.asyncio
    async def test_basic_actions(self, mock_interface):
        """Test basic agent actions"""
        agent = Agent(mock_interface)
        
        # Test tap
        await agent.tap(100, 200)
        
        # Test input
        await agent.input_text("test text")
        
        # Test scroll
        from midscene.core.types import ScrollParam
        scroll_param = ScrollParam(direction="down", scroll_type="once", distance=500)
        await agent.scroll(scroll_param)
    
    @pytest.mark.asyncio
    async def test_agent_destroy(self, mock_interface):
        """Test agent destruction"""
        agent = Agent(mock_interface)
        
        await agent.destroy()
        
        assert agent.destroyed is True
        
        # Should raise error when using destroyed agent
        with pytest.raises(RuntimeError):
            await agent.ai_locate("test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])