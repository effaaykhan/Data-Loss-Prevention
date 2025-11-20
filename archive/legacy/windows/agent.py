"""
CyberSentinel DLP Agent for Windows
Main agent implementation for Windows platform
"""

import asyncio
import platform
import structlog
from pathlib import Path

# Import base agent
import sys
sys.path.append(str(Path(__file__).parent.parent))

from common.base_agent import BaseAgent
from common.monitors.file_monitor import FileMonitor
from windows.clipboard_monitor_windows import WindowsClipboardMonitor
from windows.usb_monitor_windows import WindowsUSBMonitor

logger = structlog.get_logger()


class WindowsAgent(BaseAgent):
    """
    Windows DLP Agent

    Monitors:
    - File system (Documents, Desktop, Downloads, etc.)
    - Clipboard operations
    - USB device connections
    - Network traffic (optional)
    """

    def __init__(self, config_path: str = None):
        """
        Initialize Windows agent

        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)

        logger.info(
            "Windows agent initialized",
            platform=platform.platform(),
            version=platform.version()
        )

    async def initialize_monitors(self):
        """
        Initialize Windows-specific monitors
        """
        logger.info("Initializing monitors")

        # File system monitor
        if self.config.get("monitoring", {}).get("file_system", {}).get("enabled", True):
            paths = self.config.get("monitoring", {}).get("file_system", {}).get("paths", [])

            # Default Windows paths if none specified
            if not paths:
                username = Path.home().name
                paths = [
                    f"C:/Users/{username}/Desktop",
                    f"C:/Users/{username}/Documents",
                    f"C:/Users/{username}/Downloads"
                ]

            extensions = self.config.get("monitoring", {}).get("file_system", {}).get("extensions", [
                ".pdf", ".docx", ".xlsx", ".txt", ".csv"
            ])

            file_monitor = FileMonitor(
                agent=self,
                paths=paths,
                extensions=extensions,
                max_file_size=self.config.get("performance", {}).get("max_event_size", 1048576)
            )

            self.monitors.append(file_monitor)

            logger.info(
                "File monitor configured",
                paths=len(paths),
                extensions=len(extensions)
            )

        # Clipboard monitor
        if self.config.get("monitoring", {}).get("clipboard", {}).get("enabled", True):
            clipboard_monitor = WindowsClipboardMonitor(
                agent=self,
                poll_interval=2
            )

            self.monitors.append(clipboard_monitor)

            logger.info("Clipboard monitor configured")

        # USB monitor
        if self.config.get("monitoring", {}).get("usb", {}).get("enabled", True):
            usb_monitor = WindowsUSBMonitor(
                agent=self,
                poll_interval=5
            )

            self.monitors.append(usb_monitor)

            logger.info("USB monitor configured")

        logger.info(
            "Monitors initialized",
            total=len(self.monitors)
        )

    async def cleanup_monitors(self):
        """
        Clean up monitors
        """
        logger.info("Cleaning up monitors")

        for monitor in self.monitors:
            try:
                await monitor.stop()
            except Exception as e:
                logger.error(
                    "Error stopping monitor",
                    error=str(e)
                )

        self.monitors = []

        logger.info("Monitors cleaned up")


async def main():
    """
    Main entry point for Windows agent
    """
    # Configure logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )

    # Create and start agent
    agent = WindowsAgent()

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, shutting down")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
    finally:
        await agent.stop()


if __name__ == "__main__":
    import logging

    # Run agent
    asyncio.run(main())
