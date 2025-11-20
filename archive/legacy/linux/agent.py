"""
CyberSentinel DLP Agent for Linux
Main agent implementation for Linux platform
"""

import asyncio
import platform
import structlog
from pathlib import Path
import os

# Import base agent
import sys
sys.path.append(str(Path(__file__).parent.parent))

from common.base_agent import BaseAgent
from common.monitors.file_monitor import FileMonitor
from linux.clipboard_monitor_linux import LinuxClipboardMonitor
from linux.usb_monitor_linux import LinuxUSBMonitor

logger = structlog.get_logger()


class LinuxAgent(BaseAgent):
    """
    Linux DLP Agent

    Monitors:
    - File system (home directory, documents, downloads, etc.)
    - Clipboard operations (X11)
    - USB device connections
    - Network traffic (optional)
    """

    def __init__(self, config_path: str = None):
        """
        Initialize Linux agent

        Args:
            config_path: Path to configuration file
        """
        super().__init__(config_path)

        logger.info(
            "Linux agent initialized",
            platform=platform.platform(),
            version=platform.version(),
            distribution=self._get_distribution()
        )

    def _get_distribution(self) -> str:
        """Get Linux distribution name"""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('PRETTY_NAME='):
                        return line.split('=')[1].strip().strip('"')
        except:
            pass
        return platform.system()

    async def initialize_monitors(self):
        """
        Initialize Linux-specific monitors
        """
        logger.info("Initializing monitors")

        # File system monitor
        if self.config.get("monitoring", {}).get("file_system", {}).get("enabled", True):
            paths = self.config.get("monitoring", {}).get("file_system", {}).get("paths", [])

            # Default Linux paths if none specified
            if not paths:
                home = str(Path.home())
                paths = [
                    f"{home}/Desktop",
                    f"{home}/Documents",
                    f"{home}/Downloads"
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
            clipboard_monitor = LinuxClipboardMonitor(
                agent=self,
                poll_interval=2
            )

            self.monitors.append(clipboard_monitor)

            logger.info("Clipboard monitor configured")

        # USB monitor
        if self.config.get("monitoring", {}).get("usb", {}).get("enabled", True):
            usb_monitor = LinuxUSBMonitor(
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
    Main entry point for Linux agent
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
    agent = LinuxAgent()

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
