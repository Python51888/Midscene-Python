"""
Android device management using ADB
"""

import asyncio
import base64
import json
import subprocess
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from loguru import logger
from pydantic import BaseModel

from ..core.types import (
    AbstractInterface, InterfaceType, UIContext, BaseElement, UINode, UITree,
    Size, Rect, Point, NodeType
)


class AndroidElement(BaseElement):
    """Android UI element wrapper"""
    
    def __init__(self, device: 'AndroidDevice', **kwargs):
        self._device = device
        super().__init__(**kwargs)
    
    async def tap(self) -> None:
        """Tap this element"""
        try:
            center = self.center
            await self._device.tap(center[0], center[1])
        except Exception as e:
            logger.error(f"Failed to tap element: {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text to this element"""
        try:
            # First tap to focus
            await self.tap()
            await asyncio.sleep(0.5)
            
            # Clear existing text
            await self._device.clear_text()
            
            # Input new text
            await self._device.input_text(text)
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise


class AndroidDeviceConfig(BaseModel):
    """Android device configuration"""
    device_id: str
    adb_path: str = "adb"
    auto_dismiss_keyboard: bool = True
    use_ime: bool = True
    display_id: int = 0
    timeout: int = 30


class AndroidDevice(AbstractInterface):
    """Android device interface using ADB"""
    
    def __init__(self, device_id: str, config: Optional[AndroidDeviceConfig] = None):
        """Initialize Android device
        
        Args:
            device_id: Android device ID
            config: Device configuration
        """
        self.device_id = device_id
        self.config = config or AndroidDeviceConfig(device_id=device_id)
        self._connected = False
        self._screen_size: Optional[Size] = None
    
    @classmethod
    async def create(cls, device_id: Optional[str] = None) -> 'AndroidDevice':
        """Create Android device instance
        
        Args:
            device_id: Device ID, if None will use first available device
            
        Returns:
            AndroidDevice instance
        """
        if not device_id:
            devices = await cls.list_devices()
            if not devices:
                raise RuntimeError("No Android devices found")
            device_id = devices[0]
        
        device = cls(device_id)
        await device.connect()
        return device
    
    @classmethod
    async def list_devices(cls) -> List[str]:
        """List available Android devices"""
        try:
            result = await cls._run_adb_command(["devices"])
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            devices = []
            for line in lines:
                if '\t' in line:
                    device_id = line.split('\t')[0]
                    if device_id:
                        devices.append(device_id)
            
            return devices
            
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []
    
    async def connect(self) -> None:
        """Connect to Android device"""
        try:
            # Check if device is available
            devices = await self.list_devices()
            if self.device_id not in devices:
                raise RuntimeError(f"Device {self.device_id} not found")
            
            # Get screen size
            await self._get_screen_size()
            
            # Setup IME if needed
            if self.config.use_ime:
                await self._setup_ime()
            
            self._connected = True
            logger.info(f"Connected to Android device: {self.device_id}")
            
        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            raise
    
    @property
    def interface_type(self) -> InterfaceType:
        """Get interface type"""
        return InterfaceType.ANDROID
    
    async def get_context(self) -> UIContext:
        """Get current UI context"""
        try:
            # Take screenshot
            screenshot_base64 = await self._take_screenshot()
            
            # Get UI dump
            ui_elements = await self._get_ui_elements()
            
            # Build UI tree
            tree = await self._build_ui_tree()
            
            return UIContext(
                screenshot_base64=screenshot_base64,
                size=self._screen_size or Size(width=1080, height=1920),
                content=ui_elements,
                tree=tree
            )
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            raise
    
    async def action_space(self) -> List[str]:
        """Get available actions"""
        return [
            "tap", "long_press", "swipe", "scroll",
            "input", "clear", "back", "home", "recent",
            "volume_up", "volume_down", "power",
            "install_app", "launch_app", "stop_app"
        ]
    
    async def tap(self, x: float, y: float) -> None:
        """Tap at coordinates"""
        try:
            await self._run_adb_command([
                "-s", self.device_id, "shell", "input", "tap", str(int(x)), str(int(y))
            ])
        except Exception as e:
            logger.error(f"Failed to tap at ({x}, {y}): {e}")
            raise
    
    async def long_press(self, x: float, y: float, duration: int = 1000) -> None:
        """Long press at coordinates"""
        try:
            await self._run_adb_command([
                "-s", self.device_id, "shell", "input", "swipe", 
                str(int(x)), str(int(y)), str(int(x)), str(int(y)), str(duration)
            ])
        except Exception as e:
            logger.error(f"Failed to long press at ({x}, {y}): {e}")
            raise
    
    async def swipe(
        self, 
        start_x: float, start_y: float, 
        end_x: float, end_y: float, 
        duration: int = 300
    ) -> None:
        """Swipe between coordinates"""
        try:
            await self._run_adb_command([
                "-s", self.device_id, "shell", "input", "swipe",
                str(int(start_x)), str(int(start_y)), 
                str(int(end_x)), str(int(end_y)), str(duration)
            ])
        except Exception as e:
            logger.error(f"Failed to swipe: {e}")
            raise
    
    async def input_text(self, text: str) -> None:
        """Input text"""
        try:
            # Escape special characters
            escaped_text = text.replace(' ', '%s').replace('&', '\\&')
            await self._run_adb_command([
                "-s", self.device_id, "shell", "input", "text", escaped_text
            ])
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            raise
    
    async def clear_text(self) -> None:
        """Clear text in focused field"""
        try:
            # Select all and delete
            await self.key_event("KEYCODE_MOVE_END")
            await self.key_event("KEYCODE_SHIFT_LEFT")
            await self.key_event("KEYCODE_MOVE_HOME")
            await self.key_event("KEYCODE_DEL")
        except Exception as e:
            logger.error(f"Failed to clear text: {e}")
            raise
    
    async def scroll(self, direction: str, distance: Optional[int] = None) -> None:
        """Scroll in direction"""
        try:
            if not self._screen_size:
                await self._get_screen_size()
            
            center_x = self._screen_size.width // 2
            center_y = self._screen_size.height // 2
            distance = distance or 500
            
            if direction == "down":
                await self.swipe(center_x, center_y + distance//2, center_x, center_y - distance//2)
            elif direction == "up":
                await self.swipe(center_x, center_y - distance//2, center_x, center_y + distance//2)
            elif direction == "left":
                await self.swipe(center_x + distance//2, center_y, center_x - distance//2, center_y)
            elif direction == "right":
                await self.swipe(center_x - distance//2, center_y, center_x + distance//2, center_y)
            else:
                raise ValueError(f"Invalid scroll direction: {direction}")
                
        except Exception as e:
            logger.error(f"Failed to scroll {direction}: {e}")
            raise
    
    async def key_event(self, key_code: str) -> None:
        """Send key event"""
        try:
            await self._run_adb_command([
                "-s", self.device_id, "shell", "input", "keyevent", key_code
            ])
        except Exception as e:
            logger.error(f"Failed to send key event {key_code}: {e}")
            raise
    
    async def back(self) -> None:
        """Press back button"""
        await self.key_event("KEYCODE_BACK")
    
    async def home(self) -> None:
        """Press home button"""
        await self.key_event("KEYCODE_HOME")
    
    async def recent(self) -> None:
        """Press recent apps button"""
        await self.key_event("KEYCODE_APP_SWITCH")
    
    async def install_app(self, apk_path: str) -> None:
        """Install APK"""
        try:
            await self._run_adb_command([
                "-s", self.device_id, "install", apk_path
            ])
        except Exception as e:
            logger.error(f"Failed to install app: {e}")
            raise
    
    async def launch_app(self, package_name: str, activity: Optional[str] = None) -> None:
        """Launch app"""
        try:
            if activity:
                component = f"{package_name}/{activity}"
            else:
                component = package_name
            
            await self._run_adb_command([
                "-s", self.device_id, "shell", "am", "start", "-n", component
            ])
        except Exception as e:
            logger.error(f"Failed to launch app: {e}")
            raise
    
    async def stop_app(self, package_name: str) -> None:
        """Stop app"""
        try:
            await self._run_adb_command([
                "-s", self.device_id, "shell", "am", "force-stop", package_name
            ])
        except Exception as e:
            logger.error(f"Failed to stop app: {e}")
            raise
    
    async def _take_screenshot(self) -> str:
        """Take screenshot and return base64 string"""
        try:
            # Take screenshot using screencap
            result = await self._run_adb_command([
                "-s", self.device_id, "shell", "screencap", "-p"
            ], capture_output=True)
            
            # Convert bytes to base64
            screenshot_base64 = base64.b64encode(result.stdout).decode('utf-8')
            
            return screenshot_base64
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise
    
    async def _get_ui_elements(self) -> List[AndroidElement]:
        """Get UI elements using uiautomator dump"""
        try:
            # Get UI dump
            await self._run_adb_command([
                "-s", self.device_id, "shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"
            ])
            
            # Pull dump file
            result = await self._run_adb_command([
                "-s", self.device_id, "shell", "cat", "/sdcard/ui_dump.xml"
            ], capture_output=True)
            
            xml_content = result.stdout.decode('utf-8')
            
            # Parse XML
            root = ET.fromstring(xml_content)
            elements = []
            
            def parse_node(node, index=0):
                if node.tag == "node":
                    bounds = node.get("bounds", "")
                    if bounds:
                        # Parse bounds [x1,y1][x2,y2]
                        coords = bounds.replace('][', ',').replace('[', '').replace(']', '').split(',')
                        if len(coords) == 4:
                            x1, y1, x2, y2 = map(int, coords)
                            
                            rect = Rect(
                                left=x1, top=y1,
                                width=x2-x1, height=y2-y1
                            )
                            
                            content = node.get("text", "") or node.get("content-desc", "")
                            class_name = node.get("class", "")
                            
                            # Determine node type
                            node_type = self._get_android_node_type(class_name)
                            
                            element = AndroidElement(
                                device=self,
                                id=f"element_{index}",
                                content=content,
                                rect=rect,
                                center=(x1 + (x2-x1)/2, y1 + (y2-y1)/2),
                                node_type=node_type,
                                attributes={
                                    "class": class_name,
                                    "package": node.get("package", ""),
                                    "clickable": node.get("clickable", "false") == "true",
                                    "enabled": node.get("enabled", "false") == "true",
                                    "focused": node.get("focused", "false") == "true",
                                    "selected": node.get("selected", "false") == "true",
                                },
                                is_visible=rect.width > 0 and rect.height > 0
                            )
                            
                            if element.is_visible:
                                elements.append(element)
                
                # Process children
                for child in node:
                    parse_node(child, len(elements))
            
            parse_node(root)
            return elements
            
        except Exception as e:
            logger.error(f"Failed to get UI elements: {e}")
            return []
    
    def _get_android_node_type(self, class_name: str) -> NodeType:
        """Determine node type from Android class name"""
        class_name = class_name.lower()
        
        if "button" in class_name:
            return NodeType.BUTTON
        elif "edittext" in class_name or "textfield" in class_name:
            return NodeType.INPUT
        elif "textview" in class_name or "text" in class_name:
            return NodeType.TEXT
        elif "imageview" in class_name or "image" in class_name:
            return NodeType.IMAGE
        elif "linearlayout" in class_name or "relativelayout" in class_name or "framelayout" in class_name:
            return NodeType.CONTAINER
        else:
            return NodeType.OTHER
    
    async def _build_ui_tree(self) -> UITree:
        """Build UI tree structure"""
        # Simplified implementation - return minimal tree
        root_node = UINode(
            id="root",
            content="",
            rect=Rect(left=0, top=0, width=self._screen_size.width if self._screen_size else 1080, 
                     height=self._screen_size.height if self._screen_size else 1920),
            center=(540, 960),
            node_type=NodeType.CONTAINER,
            attributes={},
            is_visible=True,
            children=[]
        )
        
        return UITree(node=root_node, children=[])
    
    async def _get_screen_size(self) -> None:
        """Get device screen size"""
        try:
            result = await self._run_adb_command([
                "-s", self.device_id, "shell", "wm", "size"
            ], capture_output=True)
            
            output = result.stdout.decode('utf-8').strip()
            # Parse output like "Physical size: 1080x1920"
            if ":" in output:
                size_str = output.split(":")[-1].strip()
                if "x" in size_str:
                    width, height = map(int, size_str.split("x"))
                    self._screen_size = Size(width=width, height=height)
                    return
            
            # Fallback
            self._screen_size = Size(width=1080, height=1920)
            
        except Exception as e:
            logger.warning(f"Failed to get screen size: {e}")
            self._screen_size = Size(width=1080, height=1920)
    
    async def _setup_ime(self) -> None:
        """Setup input method for text input"""
        try:
            # This would setup a custom IME for better text input
            # For now, just use default
            pass
        except Exception as e:
            logger.warning(f"Failed to setup IME: {e}")
    
    @staticmethod
    async def _run_adb_command(
        args: List[str], 
        capture_output: bool = False,
        timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """Run ADB command"""
        try:
            if capture_output:
                result = await asyncio.create_subprocess_exec(
                    "adb", *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=timeout)
                
                return subprocess.CompletedProcess(
                    args=["adb"] + args,
                    returncode=result.returncode,
                    stdout=stdout,
                    stderr=stderr
                )
            else:
                result = await asyncio.create_subprocess_exec("adb", *args)
                returncode = await asyncio.wait_for(result.wait(), timeout=timeout)
                
                return subprocess.CompletedProcess(
                    args=["adb"] + args,
                    returncode=returncode
                )
                
        except asyncio.TimeoutError:
            raise TimeoutError(f"ADB command timeout: {args}")
        except Exception as e:
            logger.error(f"ADB command failed: {args}, error: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from device"""
        self._connected = False
        logger.info(f"Disconnected from device: {self.device_id}")
    
    def __del__(self):
        """Cleanup on deletion"""
        if self._connected:
            # Note: Can't use async in __del__, this is just for cleanup tracking
            logger.debug(f"Device {self.device_id} being garbage collected")