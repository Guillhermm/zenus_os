"""
Vision Operations

Screenshot analysis and UI automation using vision AI.

Features:
- Screenshot capture
- Image analysis via GPT-4V or Claude 3
- UI element detection
- Mouse/keyboard automation
- OCR text extraction
"""

import os
import base64
from io import BytesIO
from typing import Optional, Dict, List, Tuple


class VisionOps:
    """
    Vision-based operations
    
    Combines screenshot analysis with UI automation.
    """
    
    def __init__(self):
        self.last_screenshot = None
        self._pyautogui = None
        self._pil_image = None
        self._pil_imagegrab = None
    
    @property
    def pyautogui(self):
        """Lazy-load pyautogui"""
        if self._pyautogui is None:
            try:
                import pyautogui
                self.pyautogui.FAILSAFE = True
                self.pyautogui.PAUSE = 0.5
                self._pyautogui = pyautogui
            except Exception as e:
                raise RuntimeError(f"PyAutoGUI not available: {e}")
        return self._pyautogui
    
    @property
    def PIL_Image(self):
        """Lazy-load PIL Image"""
        if self._pil_image is None:
            try:
                from PIL import Image
                self._pil_image = Image
            except Exception as e:
                raise RuntimeError(f"PIL not available: {e}")
        return self._pil_image
    
    @property
    def PIL_ImageGrab(self):
        """Lazy-load PIL ImageGrab"""
        if self._pil_imagegrab is None:
            try:
                from PIL import ImageGrab
                self._pil_imagegrab = ImageGrab
            except Exception as e:
                raise RuntimeError(f"PIL not available: {e}")
        return self._pil_imagegrab
    
    @property
    def screen_size(self):
        """Get screen size"""
        return self.self.pyautogui.size()
    
    # ====================
    # Screenshot Operations
    # ====================
    
    def screenshot(self, region: Optional[Tuple[int, int, int, int]] = None, save_path: Optional[str] = None) -> str:
        """
        Capture screenshot
        
        Args:
            region: (x, y, width, height) tuple for partial screenshot
            save_path: Path to save screenshot (optional)
        
        Returns:
            Path to saved screenshot or status message
        
        Examples:
            screenshot()  # Full screen
            screenshot(region=(0, 0, 800, 600))  # Partial
            screenshot(save_path="/tmp/screen.png")  # Save to file
        """
        try:
            if region:
                screenshot = self.pyautogui.screenshot(region=region)
            else:
                screenshot = self.pyautogui.screenshot()
            
            self.last_screenshot = screenshot
            
            if save_path:
                screenshot.save(save_path)
                return f"Screenshot saved to {save_path}"
            else:
                # Save to temp
                temp_path = "/tmp/zenus_screenshot.png"
                screenshot.save(temp_path)
                return f"Screenshot captured: {temp_path}"
        
        except Exception as e:
            return f"Screenshot failed: {str(e)}"
    
    def analyze_screenshot(self, prompt: str, screenshot_path: Optional[str] = None) -> str:
        """
        Analyze screenshot with AI vision
        
        Args:
            prompt: What to analyze (e.g., "What's on the screen?", "Find the submit button")
            screenshot_path: Path to screenshot (uses last if not provided)
        
        Returns:
            AI analysis result
        
        Examples:
            analyze_screenshot("What's on my screen?")
            analyze_screenshot("Find all buttons", "/tmp/screen.png")
            analyze_screenshot("What text is in the top left corner?")
        """
        # Load screenshot
        if screenshot_path:
            try:
                image = self.PIL_Image.open(screenshot_path)
            except Exception as e:
                return f"Failed to load image: {str(e)}"
        elif self.last_screenshot:
            image = self.last_screenshot
        else:
            return "No screenshot available. Call screenshot() first."
        
        # Convert to base64 for API
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Call vision API
        try:
            from zenus_core.brain.llm.factory import get_llm
            llm = get_llm()
            
            # Check if LLM supports vision
            if hasattr(llm, 'analyze_image'):
                result = llm.analyze_image(img_base64, prompt)
                return result
            else:
                return "Current LLM doesn't support vision. Use GPT-4V or Claude 3."
        
        except Exception as e:
            return f"Vision analysis failed: {str(e)}"
    
    def find_on_screen(self, description: str) -> str:
        """
        Find UI element on screen
        
        Args:
            description: What to find (e.g., "the blue submit button")
        
        Returns:
            Location description or coordinates
        
        Examples:
            find_on_screen("the submit button")
            find_on_screen("the search box")
            find_on_screen("the red X in top right")
        """
        # Take screenshot if needed
        if not self.last_screenshot:
            self.screenshot()
        
        # Analyze with specific prompt
        prompt = f"Find the location of: {description}. Give pixel coordinates (x, y) if possible."
        result = self.analyze_screenshot(prompt)
        
        return result
    
    # ====================
    # Mouse Operations
    # ====================
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, description: Optional[str] = None) -> str:
        """
        Click at location or on described element
        
        Args:
            x: X coordinate (optional if description provided)
            y: Y coordinate (optional if description provided)
            description: Element description (e.g., "submit button")
        
        Returns:
            Result message
        
        Examples:
            click(100, 200)  # Click at coordinates
            click(description="the submit button")  # Find and click
        """
        try:
            if description:
                # Find element first
                location = self.find_on_screen(description)
                # TODO: Parse coordinates from vision response
                return f"Found: {location}. Parsing coordinates not yet implemented."
            
            elif x is not None and y is not None:
                self.pyautogui.click(x, y)
                return f"Clicked at ({x}, {y})"
            
            else:
                return "Provide either (x, y) coordinates or element description"
        
        except Exception as e:
            return f"Click failed: {str(e)}"
    
    def double_click(self, x: int, y: int) -> str:
        """Double-click at location"""
        try:
            self.pyautogui.doubleClick(x, y)
            return f"Double-clicked at ({x}, {y})"
        except Exception as e:
            return f"Double-click failed: {str(e)}"
    
    def right_click(self, x: int, y: int) -> str:
        """Right-click at location"""
        try:
            self.pyautogui.rightClick(x, y)
            return f"Right-clicked at ({x}, {y})"
        except Exception as e:
            return f"Right-click failed: {str(e)}"
    
    def move_to(self, x: int, y: int, duration: float = 0.5) -> str:
        """Move mouse to location"""
        try:
            self.pyautogui.moveTo(x, y, duration=duration)
            return f"Moved to ({x}, {y})"
        except Exception as e:
            return f"Move failed: {str(e)}"
    
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 1.0) -> str:
        """Drag from (x1, y1) to (x2, y2)"""
        try:
            self.pyautogui.moveTo(x1, y1)
            self.pyautogui.drag(x2 - x1, y2 - y1, duration=duration)
            return f"Dragged from ({x1}, {y1}) to ({x2}, {y2})"
        except Exception as e:
            return f"Drag failed: {str(e)}"
    
    # ====================
    # Keyboard Operations
    # ====================
    
    def type_text(self, text: str, interval: float = 0.05) -> str:
        """
        Type text
        
        Args:
            text: Text to type
            interval: Delay between keystrokes (seconds)
        
        Returns:
            Result message
        """
        try:
            self.pyautogui.write(text, interval=interval)
            return f"Typed: {text[:50]}..."
        except Exception as e:
            return f"Type failed: {str(e)}"
    
    def press_key(self, key: str) -> str:
        """Press keyboard key"""
        try:
            self.pyautogui.press(key)
            return f"Pressed key: {key}"
        except Exception as e:
            return f"Key press failed: {str(e)}"
    
    def hotkey(self, *keys: str) -> str:
        """Press key combination"""
        try:
            self.pyautogui.hotkey(*keys)
            return f"Pressed hotkey: {'+'.join(keys)}"
        except Exception as e:
            return f"Hotkey failed: {str(e)}"
    
    # ====================
    # Advanced Operations
    # ====================
    
    def fill_form(self, field_values: Dict[str, str]) -> str:
        """
        Fill form fields using vision + automation
        
        Args:
            field_values: Dict of field_name -> value
        
        Returns:
            Result message
        
        Example:
            fill_form({"Name": "John", "Email": "john@example.com"})
        """
        results = []
        
        for field_name, value in field_values.items():
            # Find field
            location = self.find_on_screen(f"{field_name} field")
            # TODO: Parse coordinates and click
            results.append(f"{field_name}: {location}")
        
        return "\n".join(results)
    
    def get_screen_text(self) -> str:
        """
        Extract all text from screen using OCR
        
        Returns:
            All visible text
        """
        if not self.last_screenshot:
            self.screenshot()
        
        prompt = "Extract all readable text from this screenshot. Return just the text."
        result = self.analyze_screenshot(prompt)
        
        return result
    
    def wait_for_element(self, description: str, timeout: int = 10) -> str:
        """
        Wait for element to appear
        
        Args:
            description: Element to wait for
            timeout: Maximum wait time (seconds)
        
        Returns:
            Result message
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self.screenshot()
            result = self.find_on_screen(description)
            
            if "found" in result.lower() or "located" in result.lower():
                return f"Element appeared: {description}"
            
            time.sleep(1)
        
        return f"Timeout waiting for: {description}"


# Register with tool registry
def register():
    """Register VisionOps with tool registry"""
    from zenus_core.tools.registry import register_tool
    register_tool("VisionOps", VisionOps())
