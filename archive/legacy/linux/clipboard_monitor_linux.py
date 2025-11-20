"""
Linux Clipboard Monitor
Uses Xlib to access X11 clipboard
"""

import structlog
from typing import Optional

logger = structlog.get_logger()

# Try to import Xlib
try:
    from Xlib import X, display
    HAS_XLIB = True
except ImportError:
    HAS_XLIB = False
    logger.warning("python-xlib not available, clipboard monitoring disabled")


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.monitors.clipboard_monitor import ClipboardMonitor


class LinuxClipboardMonitor(ClipboardMonitor):
    """
    Linux-specific clipboard monitor using Xlib
    """

    def __init__(self, agent, poll_interval: int = 2):
        """
        Initialize Linux clipboard monitor

        Args:
            agent: Parent agent instance
            poll_interval: Polling interval in seconds
        """
        super().__init__(agent, poll_interval)

        if not HAS_XLIB:
            logger.error("python-xlib not available, cannot monitor clipboard")

        self.display_obj = None
        if HAS_XLIB:
            try:
                self.display_obj = display.Display()
            except Exception as e:
                logger.error(
                    "Failed to connect to X display",
                    error=str(e)
                )

    def get_clipboard_content(self) -> Optional[str]:
        """
        Get current clipboard content using Xlib

        Returns:
            Clipboard content as string, or None if unavailable
        """
        if not HAS_XLIB or not self.display_obj:
            return None

        try:
            # Get clipboard selection
            clipboard = self.display_obj.get_selection_owner(
                self.display_obj.get_atom("CLIPBOARD")
            )

            if clipboard == X.NONE:
                return None

            # Try to get UTF8_STRING first
            clipboard_text = None

            try:
                # Request clipboard content
                window = self.display_obj.screen().root.create_window(
                    0, 0, 1, 1, 0, X.CopyFromParent
                )

                window.convert_selection(
                    self.display_obj.get_atom("CLIPBOARD"),
                    self.display_obj.get_atom("UTF8_STRING"),
                    self.display_obj.get_atom("XSEL_DATA"),
                    X.CurrentTime
                )

                self.display_obj.sync()

                # Get property
                prop = window.get_full_property(
                    self.display_obj.get_atom("XSEL_DATA"),
                    X.AnyPropertyType
                )

                if prop and prop.value:
                    clipboard_text = prop.value.decode('utf-8', errors='ignore')

                window.destroy()

            except Exception as e:
                logger.debug(
                    "Could not get clipboard via UTF8_STRING",
                    error=str(e)
                )

            return clipboard_text

        except Exception as e:
            logger.debug(
                "Could not read clipboard",
                error=str(e)
            )
            return None

    def __del__(self):
        """Clean up X display connection"""
        if self.display_obj:
            try:
                self.display_obj.close()
            except:
                pass
