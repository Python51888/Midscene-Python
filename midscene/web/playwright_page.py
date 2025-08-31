"""
Playwright integration for Midscene
"""

import base64
import json
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from loguru import logger

from ..core.types import (
    AbstractInterface, InterfaceType, UIContext, BaseElement, UINode, UITree,
    Size, Rect, Point, NodeType
)


class PlaywrightElement(BaseElement):
    """Playwright element wrapper"""
    
    def __init__(self, page: Page, selector: str, **kwargs):
        self._page = page
        self._selector = selector
        super().__init__(**kwargs)
    
    async def tap(self) -> None:
        """Click this element"""
        try:
            await self._page.click(self._selector)
        except Exception as e:
            logger.error(f"Failed to click element: {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text to this element"""
        try:
            await self._page.fill(self._selector, text)
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise


class PlaywrightWebPage(AbstractInterface):
    """Playwright page interface"""
    
    def __init__(self, page: Page, context: BrowserContext, browser: Browser):
        """Initialize with Playwright page
        
        Args:
            page: Playwright page instance
            context: Browser context
            browser: Browser instance
        """
        self.page = page
        self.context = context
        self.browser = browser
    
    @classmethod
    async def create(
        cls,
        headless: bool = False,
        viewport_size: tuple[int, int] = (1920, 1080),
        user_data_dir: Optional[str] = None,
        **browser_options
    ) -> 'PlaywrightWebPage':
        """Create new Playwright page instance
        
        Args:
            headless: Run in headless mode
            viewport_size: Browser viewport size
            user_data_dir: Browser user data directory
            **browser_options: Additional browser options
            
        Returns:
            PlaywrightWebPage instance
        """
        playwright = await async_playwright().start()
        
        launch_options = {
            "headless": headless,
            **browser_options
        }
        
        if user_data_dir:
            launch_options["user_data_dir"] = user_data_dir
        
        browser = await playwright.chromium.launch(**launch_options)
        
        context = await browser.new_context(
            viewport={"width": viewport_size[0], "height": viewport_size[1]}
        )
        
        page = await context.new_page()
        
        return cls(page, context, browser)
    
    @property
    def interface_type(self) -> InterfaceType:
        """Get interface type"""
        return InterfaceType.WEB
    
    async def get_context(self) -> UIContext:
        """Get current UI context"""
        try:
            # Take screenshot
            screenshot_base64 = await self._take_screenshot()
            
            # Get page size
            size = await self._get_page_size()
            
            # Extract DOM elements
            elements = await self._extract_elements()
            
            # Build UI tree
            tree = await self._build_ui_tree()
            
            return UIContext(
                screenshot_base64=screenshot_base64,
                size=size,
                content=elements,
                tree=tree
            )
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            raise
    
    async def action_space(self) -> List[str]:
        """Get available actions"""
        return [
            "tap", "click", "double_click", "right_click",
            "input", "type", "fill", "clear",
            "scroll", "scroll_up", "scroll_down", "scroll_left", "scroll_right",
            "hover", "drag", "key_press", "navigate", "reload",
            "go_back", "go_forward"
        ]
    
    async def tap(self, x: float, y: float) -> None:
        """Tap at coordinates"""
        try:
            await self.page.mouse.click(x, y)
        except Exception as e:
            logger.error(f"Failed to tap at ({x}, {y}): {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text to focused element"""
        try:
            await self.page.keyboard.type(text)
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise
    
    async def scroll(self, direction: str, distance: Optional[int] = None) -> None:
        """Scroll in direction"""
        try:
            distance = distance or 500
            
            if direction == "down":
                await self.page.mouse.wheel(0, distance)
            elif direction == "up":
                await self.page.mouse.wheel(0, -distance)
            elif direction == "right":
                await self.page.mouse.wheel(distance, 0)
            elif direction == "left":
                await self.page.mouse.wheel(-distance, 0)
            else:
                raise ValueError(f"Invalid scroll direction: {direction}")
                
        except Exception as e:
            logger.error(f"Failed to scroll {direction}: {e}")
            raise
    
    async def navigate_to(self, url: str) -> None:
        """Navigate to URL"""
        try:
            await self.page.goto(url, wait_until="networkidle")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: float = 10000
    ) -> None:
        """Wait for element to be present"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            raise TimeoutError(f"Element not found: {selector}")
    
    async def evaluate_script(self, script: str, *args) -> Any:
        """Evaluate JavaScript"""
        return await self.page.evaluate(script, *args)
    
    async def close(self) -> None:
        """Close the browser"""
        try:
            await self.context.close()
            await self.browser.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    async def _take_screenshot(self) -> str:
        """Take screenshot and return base64 string"""
        try:
            # Take screenshot as bytes
            screenshot_bytes = await self.page.screenshot(type="png")
            
            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return screenshot_base64
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise
    
    async def _get_page_size(self) -> Size:
        """Get page viewport size"""
        try:
            viewport_size = await self.page.evaluate("""
                () => ({
                    width: window.innerWidth,
                    height: window.innerHeight
                })
            """)
            
            return Size(
                width=viewport_size['width'],
                height=viewport_size['height']
            )
            
        except Exception as e:
            logger.error(f"Failed to get page size: {e}")
            return Size(width=1920, height=1080)
    
    async def _extract_elements(self) -> List[PlaywrightElement]:
        """Extract all visible elements from page"""
        try:
            # Use JavaScript to extract element information
            element_data = await self.page.evaluate("""
                () => {
                    const elements = [];
                    const allElements = document.querySelectorAll('*');
                    
                    allElements.forEach((el, index) => {
                        const rect = el.getBoundingClientRect();
                        
                        // Skip elements that are not visible
                        if (rect.width === 0 || rect.height === 0 || 
                            rect.top < 0 || rect.left < 0 ||
                            getComputedStyle(el).visibility === 'hidden' ||
                            getComputedStyle(el).display === 'none') {
                            return;
                        }
                        
                        // Generate a selector for this element
                        const selector = generateSelector(el);
                        
                        elements.push({
                            id: `element_${index}`,
                            selector: selector,
                            tagName: el.tagName.toLowerCase(),
                            content: el.textContent?.trim() || el.getAttribute('alt') || el.getAttribute('title') || '',
                            rect: {
                                left: rect.left,
                                top: rect.top,
                                width: rect.width,
                                height: rect.height
                            },
                            center: [rect.left + rect.width / 2, rect.top + rect.height / 2],
                            attributes: {
                                id: el.id,
                                className: el.className,
                                type: el.type,
                                name: el.name,
                                href: el.href,
                                src: el.src,
                                value: el.value,
                                placeholder: el.placeholder
                            }
                        });
                    });
                    
                    function generateSelector(element) {
                        if (element.id) {
                            return `#${element.id}`;
                        }
                        
                        let path = element.tagName.toLowerCase();
                        let parent = element.parentElement;
                        
                        while (parent && parent !== document.body) {
                            const siblings = Array.from(parent.children);
                            const index = siblings.indexOf(element) + 1;
                            path = `${parent.tagName.toLowerCase()}:nth-child(${index}) > ${path}`;
                            element = parent;
                            parent = element.parentElement;
                        }
                        
                        return path;
                    }
                    
                    return elements;
                }
            """)
            
            elements = []
            for data in element_data:
                rect_data = data['rect']
                rect = Rect(
                    left=rect_data['left'],
                    top=rect_data['top'],
                    width=rect_data['width'],
                    height=rect_data['height']
                )
                
                # Determine node type
                tag_name = data['tagName']
                node_type = self._get_node_type(tag_name, data['attributes'])
                
                element = PlaywrightElement(
                    page=self.page,
                    selector=data['selector'],
                    id=data['id'],
                    content=data['content'],
                    rect=rect,
                    center=tuple(data['center']),
                    node_type=node_type,
                    attributes=data['attributes'],
                    is_visible=True
                )
                
                elements.append(element)
            
            return elements
            
        except Exception as e:
            logger.error(f"Failed to extract elements: {e}")
            return []
    
    def _get_node_type(self, tag_name: str, attributes: Dict[str, Any]) -> NodeType:
        """Determine node type from tag name and attributes"""
        if tag_name in ['input', 'textarea']:
            input_type = attributes.get('type', '').lower()
            if input_type in ['text', 'password', 'email', 'search', 'url', 'tel']:
                return NodeType.INPUT
            elif input_type in ['button', 'submit', 'reset']:
                return NodeType.BUTTON
        elif tag_name in ['button']:
            return NodeType.BUTTON
        elif tag_name in ['a']:
            return NodeType.LINK
        elif tag_name in ['img']:
            return NodeType.IMAGE
        elif tag_name in ['div', 'span', 'section', 'article', 'header', 'footer', 'nav']:
            return NodeType.CONTAINER
        elif tag_name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'label', 'td', 'th']:
            return NodeType.TEXT
        else:
            return NodeType.OTHER
    
    async def _build_ui_tree(self) -> UITree:
        """Build UI tree structure"""
        try:
            # Simplified tree building - just create a root container
            # In a full implementation, we would parse the actual DOM tree
            root_node = UINode(
                id="root",
                content="",
                rect=Rect(left=0, top=0, width=1920, height=1080),
                center=(960, 540),
                node_type=NodeType.CONTAINER,
                attributes={},
                is_visible=True,
                children=[]
            )
            
            return UITree(node=root_node, children=[])
            
        except Exception as e:
            logger.error(f"Failed to build UI tree: {e}")
            # Return minimal tree
            root_node = UINode(
                id="root",
                content="",
                rect=Rect(left=0, top=0, width=1920, height=1080),
                center=(960, 540),
                node_type=NodeType.CONTAINER,
                attributes={},
                is_visible=True,
                children=[]
            )
            return UITree(node=root_node, children=[])
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()