"""
Bridge mode implementation for Chrome extension integration
"""

import asyncio
import json
import websockets
from typing import Any, Dict, List, Optional
from loguru import logger

from ..core.types import (
    AbstractInterface, InterfaceType, UIContext, BaseElement, UINode, UITree,
    Size, Rect, Point, NodeType
)


class BridgeElement(BaseElement):
    """Bridge element wrapper"""
    
    def __init__(self, bridge: 'BridgeWebPage', **kwargs):
        self._bridge = bridge
        super().__init__(**kwargs)
    
    async def tap(self) -> None:
        """Click this element"""
        try:
            await self._bridge.send_command({
                "action": "click",
                "target": {"id": self.id}
            })
        except Exception as e:
            logger.error(f"Failed to click element: {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text to this element"""
        try:
            await self._bridge.send_command({
                "action": "input",
                "target": {"id": self.id},
                "text": text
            })
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise


class BridgeWebPage(AbstractInterface):
    """Bridge mode page interface for Chrome extension communication"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8765"):
        """Initialize bridge connection
        
        Args:
            websocket_url: WebSocket server URL
        """
        self.websocket_url = websocket_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self._command_id = 0
        self._response_futures: Dict[int, asyncio.Future] = {}
    
    @classmethod
    async def create(
        cls,
        websocket_url: str = "ws://localhost:8765",
        wait_for_connection: bool = True
    ) -> 'BridgeWebPage':
        """Create bridge connection
        
        Args:
            websocket_url: WebSocket server URL
            wait_for_connection: Wait for extension to connect
            
        Returns:
            BridgeWebPage instance
        """
        bridge = cls(websocket_url)
        
        if wait_for_connection:
            await bridge.connect()
        
        return bridge
    
    async def connect(self, timeout: float = 30.0) -> None:
        """Connect to Chrome extension"""
        try:
            logger.info(f"Waiting for extension connection on {self.websocket_url}")
            
            # Start WebSocket server and wait for extension to connect
            server = await websockets.serve(
                self._handle_connection,
                "localhost", 
                8765
            )
            
            # Wait for connection with timeout
            start_time = asyncio.get_event_loop().time()
            while not self.websocket and (asyncio.get_event_loop().time() - start_time) < timeout:
                await asyncio.sleep(0.1)
            
            if not self.websocket:
                raise TimeoutError("Extension connection timeout")
            
            logger.info("Extension connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to extension: {e}")
            raise
    
    async def _handle_connection(self, websocket, path):
        """Handle WebSocket connection from extension"""
        self.websocket = websocket
        logger.info("Extension connected")
        
        try:
            async for message in websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Extension disconnected")
            self.websocket = None
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
    
    async def _handle_message(self, message: str) -> None:
        """Handle message from extension"""
        try:
            data = json.loads(message)
            
            if "id" in data and data["id"] in self._response_futures:
                # Response to command
                future = self._response_futures.pop(data["id"])
                if not future.done():
                    future.set_result(data)
            else:
                # Unsolicited message from extension
                logger.debug(f"Received message: {data}")
                
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
    
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to extension and wait for response"""
        if not self.websocket:
            raise RuntimeError("Extension not connected")
        
        command_id = self._command_id
        self._command_id += 1
        
        command["id"] = command_id
        
        # Create future for response
        future = asyncio.Future()
        self._response_futures[command_id] = future
        
        try:
            # Send command
            await self.websocket.send(json.dumps(command))
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=30.0)
            
            if response.get("error"):
                raise Exception(f"Command failed: {response['error']}")
            
            return response
            
        except asyncio.TimeoutError:
            self._response_futures.pop(command_id, None)
            raise TimeoutError("Command timeout")
        except Exception as e:
            self._response_futures.pop(command_id, None)
            raise
    
    @property
    def interface_type(self) -> InterfaceType:
        """Get interface type"""
        return InterfaceType.WEB
    
    async def get_context(self) -> UIContext:
        """Get current UI context"""
        try:
            response = await self.send_command({"action": "getContext"})
            
            # Parse context data
            context_data = response["data"]
            
            # Convert to UIContext
            screenshot_base64 = context_data["screenshot"]
            size = Size(**context_data["size"])
            
            elements = []
            for elem_data in context_data["elements"]:
                rect = Rect(**elem_data["rect"])
                node_type = NodeType(elem_data.get("nodeType", "other"))
                
                element = BridgeElement(
                    bridge=self,
                    id=elem_data["id"],
                    content=elem_data["content"],
                    rect=rect,
                    center=tuple(elem_data["center"]),
                    node_type=node_type,
                    attributes=elem_data.get("attributes", {}),
                    is_visible=elem_data.get("isVisible", True)
                )
                elements.append(element)
            
            # Build tree
            tree_data = context_data.get("tree", {})
            tree = self._build_tree_from_data(tree_data)
            
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
            await self.send_command({
                "action": "tap",
                "coordinates": {"x": x, "y": y}
            })
        except Exception as e:
            logger.error(f"Failed to tap at ({x}, {y}): {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text to focused element"""
        try:
            await self.send_command({
                "action": "inputText",
                "text": text
            })
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise
    
    async def scroll(self, direction: str, distance: Optional[int] = None) -> None:
        """Scroll in direction"""
        try:
            await self.send_command({
                "action": "scroll",
                "direction": direction,
                "distance": distance or 500
            })
        except Exception as e:
            logger.error(f"Failed to scroll {direction}: {e}")
            raise
    
    async def navigate_to(self, url: str) -> None:
        """Navigate to URL"""
        try:
            await self.send_command({
                "action": "navigate",
                "url": url
            })
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise
    
    def _build_tree_from_data(self, tree_data: Dict[str, Any]) -> UITree:
        """Build UITree from extension data"""
        if not tree_data:
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
        
        # Convert tree data to UINode
        node_data = tree_data["node"]
        node = UINode(
            id=node_data["id"],
            content=node_data["content"],
            rect=Rect(**node_data["rect"]),
            center=tuple(node_data["center"]),
            node_type=NodeType(node_data.get("nodeType", "other")),
            attributes=node_data.get("attributes", {}),
            is_visible=node_data.get("isVisible", True),
            children=[]
        )
        
        # Build children recursively
        children = []
        for child_data in tree_data.get("children", []):
            child_tree = self._build_tree_from_data(child_data)
            children.append(child_tree)
        
        return UITree(node=node, children=children)
    
    async def close(self) -> None:
        """Close bridge connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None