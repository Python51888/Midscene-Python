"""
Selenium WebDriver integration for Midscene
"""

import base64
import json
from io import BytesIO
from typing import Any, Dict, List, Optional, Union

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from PIL import Image
from loguru import logger

from ..core.types import (
    AbstractInterface, InterfaceType, UIContext, BaseElement, UINode, UITree,
    Size, Rect, Point, NodeType
)


class SeleniumElement(BaseElement):
    """Selenium web element wrapper"""
    
    def __init__(self, element: WebElement, **kwargs):
        self._web_element = element
        super().__init__(**kwargs)
    
    async def tap(self) -> None:
        """Click this element"""
        try:
            self._web_element.click()
        except Exception as e:
            logger.error(f"Failed to click element: {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text to this element"""
        try:
            self._web_element.clear()
            self._web_element.send_keys(text)
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise


class SeleniumWebPage(AbstractInterface):
    """Selenium WebDriver page interface"""
    
    def __init__(self, driver: webdriver.Chrome):
        """Initialize with Chrome driver
        
        Args:
            driver: Chrome WebDriver instance
        """
        self.driver = driver
        self._action_chains = ActionChains(driver)
        
    @classmethod
    def create(
        cls,
        headless: bool = False,
        window_size: tuple[int, int] = (1920, 1080),
        user_data_dir: Optional[str] = None,
        **chrome_options
    ) -> 'SeleniumWebPage':
        """Create new Chrome WebDriver instance
        
        Args:
            headless: Run in headless mode
            window_size: Browser window size
            user_data_dir: Chrome user data directory
            **chrome_options: Additional Chrome options
            
        Returns:
            SeleniumWebPage instance
        """
        options = webdriver.ChromeOptions()
        
        if headless:
            options.add_argument('--headless')
        
        options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
        
        if user_data_dir:
            options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Add common Chrome options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # Add custom options
        for key, value in chrome_options.items():
            if value is True:
                options.add_argument(f'--{key}')
            elif value is not False:
                options.add_argument(f'--{key}={value}')
        
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(*window_size)
        
        return cls(driver)
    
    @property
    def interface_type(self) -> InterfaceType:
        """Get interface type"""
        return InterfaceType.WEB
    
    async def get_context(self) -> UIContext:
        """Get current UI context"""
        try:
            # Take screenshot
            screenshot_base64 = self._take_screenshot()
            
            # Get page size
            size = self._get_page_size()
            
            # Extract DOM elements
            elements = self._extract_elements()
            
            # Build UI tree
            tree = self._build_ui_tree()
            
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
            "input", "type", "clear",
            "scroll", "scroll_up", "scroll_down", "scroll_left", "scroll_right",
            "hover", "drag", "key_press", "navigate"
        ]
    
    async def tap(self, x: float, y: float) -> None:
        """Tap at coordinates"""
        try:
            self._action_chains.move_by_offset(x, y).click().perform()
            self._action_chains.reset_actions()
        except Exception as e:
            logger.error(f"Failed to tap at ({x}, {y}): {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text to focused element"""
        try:
            active_element = self.driver.switch_to.active_element
            active_element.send_keys(text)
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise
    
    async def scroll(self, direction: str, distance: Optional[int] = None) -> None:
        """Scroll in direction"""
        try:
            distance = distance or 500
            
            if direction == "down":
                self.driver.execute_script(f"window.scrollBy(0, {distance});")
            elif direction == "up":
                self.driver.execute_script(f"window.scrollBy(0, -{distance});")
            elif direction == "right":
                self.driver.execute_script(f"window.scrollBy({distance}, 0);")
            elif direction == "left":
                self.driver.execute_script(f"window.scrollBy(-{distance}, 0);")
            else:
                raise ValueError(f"Invalid scroll direction: {direction}")
                
        except Exception as e:
            logger.error(f"Failed to scroll {direction}: {e}")
            raise
    
    async def navigate_to(self, url: str) -> None:
        """Navigate to URL"""
        try:
            self.driver.get(url)
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
    
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: float = 10.0,
        by: By = By.CSS_SELECTOR
    ) -> WebElement:
        """Wait for element to be present"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            raise TimeoutError(f"Element not found: {selector}")
    
    async def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript"""
        return self.driver.execute_script(script, *args)
    
    def close(self) -> None:
        """Close the browser"""
        try:
            self.driver.quit()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    def _take_screenshot(self) -> str:
        """Take screenshot and return base64 string"""
        try:
            # Take screenshot as PNG bytes
            screenshot_bytes = self.driver.get_screenshot_as_png()
            
            # Convert to base64
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return screenshot_base64
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise
    
    def _get_page_size(self) -> Size:
        """Get page viewport size"""
        try:
            viewport_size = self.driver.execute_script("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                };
            """)
            
            return Size(
                width=viewport_size['width'],
                height=viewport_size['height']
            )
            
        except Exception as e:
            logger.error(f"Failed to get page size: {e}")
            return Size(width=1920, height=1080)
    
    def _extract_elements(self) -> List[SeleniumElement]:
        """Extract all visible elements from page"""
        try:
            # Use JavaScript to extract element information
            script = """
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
                
                elements.push({
                    id: `element_${index}`,
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
                    },
                    xpath: getXPath(el)
                });
            });
            
            function getXPath(element) {
                if (element.id !== '') {
                    return `//*[@id="${element.id}"]`;
                }
                if (element === document.body) {
                    return '/html/body';
                }
                
                let ix = 0;
                const siblings = element.parentNode?.childNodes || [];
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            return elements;
            """
            
            element_data = self.driver.execute_script(script)
            
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
                
                element = SeleniumElement(
                    element=None,  # We don't store the actual WebElement
                    id=data['id'],
                    content=data['content'],
                    rect=rect,
                    center=tuple(data['center']),
                    node_type=node_type,
                    attributes=data['attributes'],
                    is_visible=True,
                    xpaths=[data['xpath']] if data['xpath'] else None
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
    
    def _build_ui_tree(self) -> UITree:
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
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()