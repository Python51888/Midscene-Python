"""
Midscene Python - AI-powered automation framework

A Python implementation of Midscene, providing AI-driven automation
capabilities for Web and Android platforms.
"""

from .core.agent import Agent
from .core.insight import Insight
from .core.types import UIContext, LocateResult, ExecutionResult

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "Insight", 
    "UIContext",
    "LocateResult",
    "ExecutionResult",
]