"""
Web integration module for Midscene Python
"""

from .selenium_page import SeleniumWebPage
from .playwright_page import PlaywrightWebPage
from .bridge import BridgeWebPage

__all__ = [
    "SeleniumWebPage",
    "PlaywrightWebPage", 
    "BridgeWebPage",
]