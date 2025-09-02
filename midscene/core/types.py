"""
Core types and interfaces for Midscene Python
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable, Generic, TypeVar
from pydantic import BaseModel

# Type variables
ElementType = TypeVar('ElementType', bound='BaseElement')
T = TypeVar('T')


class InterfaceType(str, Enum):
    """Interface type enumeration"""
    WEB = "web"
    ANDROID = "android"


class NodeType(str, Enum):
    """UI Node type enumeration"""
    CONTAINER = "container"
    TEXT = "text"
    INPUT = "input"
    BUTTON = "button"
    IMAGE = "image"
    LINK = "link"
    OTHER = "other"


@dataclass
class Point:
    """2D Point representation"""
    x: float
    y: float


@dataclass
class Size:
    """Size representation"""
    width: float
    height: float


@dataclass
class Rect:
    """Rectangle representation"""
    left: float
    top: float
    width: float
    height: float
    
    @property
    def right(self) -> float:
        return self.left + self.width
    
    @property
    def bottom(self) -> float:
        return self.top + self.height
    
    @property
    def center(self) -> Point:
        return Point(
            x=self.left + self.width / 2,
            y=self.top + self.height / 2
        )


class BaseElement(BaseModel):
    """Base UI element interface"""
    id: str
    content: str
    rect: Rect
    center: tuple[float, float]
    node_type: NodeType = NodeType.OTHER
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_visible: bool = True
    xpaths: Optional[List[str]] = None
    
    async def tap(self) -> None:
        """Tap/click this element"""
        raise NotImplementedError
    
    async def input_text(self, text: str) -> None:
        """Input text to this element"""
        raise NotImplementedError


class UINode(BaseModel):
    """UI tree node representation"""
    id: str
    content: str
    rect: Rect
    center: tuple[float, float]
    node_type: NodeType
    attributes: Dict[str, Any] = field(default_factory=dict)
    is_visible: bool = True
    children: List['UINode'] = field(default_factory=list)


class UITree(BaseModel):
    """UI tree representation"""
    node: UINode
    children: List['UITree'] = field(default_factory=list)


class UIContext(BaseModel, Generic[ElementType]):
    """UI context containing screenshot and element information"""
    screenshot_base64: str
    size: Size
    content: List[ElementType]
    tree: UITree
    
    
class AIUsageInfo(BaseModel):
    """AI usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: Optional[float] = None


class LocateResult(BaseModel):
    """Element locate result"""
    element: Optional[BaseElement] = None
    rect: Optional[Rect] = None


class ExecutionResult(BaseModel, Generic[T]):
    """Generic execution result"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    usage: Optional[AIUsageInfo] = None


class AssertResult(BaseModel):
    """Assertion result"""
    passed: bool
    thought: str = ""
    message: str = ""


# Type aliases
TUserPrompt = Union[str, Dict[str, Any]]
ElementById = Callable[[str], Optional[BaseElement]]
OnTaskStartTip = Callable[[str], Union[None, Awaitable[None]]]


# Abstract interface for device/platform implementations
class AbstractInterface(ABC):
    """Abstract interface for platform implementations"""
    
    @property
    @abstractmethod
    def interface_type(self) -> InterfaceType:
        """Get interface type"""
        pass
    
    @abstractmethod
    async def get_context(self) -> UIContext:
        """Get current UI context"""
        pass
    
    @abstractmethod
    async def action_space(self) -> List[str]:
        """Get available actions"""
        pass
    
    @abstractmethod
    async def tap(self, x: float, y: float) -> None:
        """Tap at coordinates"""
        pass
    
    @abstractmethod
    async def input_text(self, text: str) -> None:
        """Input text"""
        pass
    
    @abstractmethod
    async def scroll(self, direction: str, distance: Optional[int] = None) -> None:
        """Scroll in direction"""
        pass


class InsightAction(str, Enum):
    """Insight action types"""
    LOCATE = "locate"
    EXTRACT = "extract"
    ASSERT = "assert"


@dataclass
class AgentOptions:
    """Agent configuration options"""
    test_id: Optional[str] = None
    cache_id: Optional[str] = None
    group_name: str = "Midscene Report"
    group_description: str = ""
    generate_report: bool = True
    auto_print_report_msg: bool = True
    ai_action_context: Optional[str] = None
    report_file_name: Optional[str] = None
    model_config: Optional[Callable] = None


@dataclass
class LocateOption:
    """Locate operation options"""
    prompt: Optional[TUserPrompt] = None
    deep_think: bool = False
    cacheable: bool = True
    xpath: Optional[str] = None
    ui_context: Optional[UIContext] = None


@dataclass
class ExtractOption:
    """Extract operation options"""
    dom_included: Union[bool, str] = False  # False, True, or 'visible-only'
    screenshot_included: bool = True
    return_thought: bool = False
    is_wait_for_assert: bool = False
    do_not_throw_error: bool = False


class ScrollParam(BaseModel):
    """Scroll parameters"""
    direction: str  # 'down', 'up', 'left', 'right'
    scroll_type: str  # 'once', 'untilBottom', 'untilTop', 'untilLeft', 'untilRight'
    distance: Optional[int] = None  # distance in pixels