"""
Windows Clipboard Monitor
Uses pywin32 to access Windows clipboard
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from typing import Optional

logger = structlog.get_logger()

# Try to import pywin32
try:
    import win32clipboard
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.warning("pywin32 not available, clipboard monitoring disabled")


from common.monitors.clipboard_monitor import ClipboardMonitor


class WindowsClipboardMonitor(ClipboardMonitor):
    """
    Windows-specific clipboard monitor using pywin32
    """

    def __init__(self, agent, poll_interval: int = 2):
        """
        Initialize Windows clipboard monitor

        Args:
            agent: Parent agent instance
            poll_interval: Polling interval in seconds
        """
        super().__init__(agent, poll_interval)

        if not HAS_WIN32:
            logger.error("pywin32 not available, cannot monitor clipboard")

    def get_clipboard_content(self) -> Optional[str]:
        """
        Get current clipboard content using Windows API

        Returns:
            Clipboard content as string, or None if unavailable
        """
        if not HAS_WIN32:
            return None

        try:
            win32clipboard.OpenClipboard()

            # Try to get text
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                win32clipboard.CloseClipboard()

                if isinstance(data, bytes):
                    return data.decode('utf-8', errors='ignore')
                else:
                    return str(data)

            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                return str(data)

            else:
                win32clipboard.CloseClipboard()
                return None

        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

            logger.debug(
                "Could not read clipboard",
                error=str(e)
            )
            return None
