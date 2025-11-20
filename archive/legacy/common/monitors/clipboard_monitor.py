"""
Clipboard Monitor
Monitors clipboard operations for sensitive data
"""

import asyncio
import structlog
from typing import Optional

logger = structlog.get_logger()


class ClipboardMonitor:
    """
    Clipboard monitor
    Platform-specific implementation in subclasses
    """

    def __init__(self, agent, poll_interval: int = 2):
        """
        Initialize clipboard monitor

        Args:
            agent: Parent agent instance
            poll_interval: Polling interval in seconds
        """
        self.agent = agent
        self.poll_interval = poll_interval
        self.running = False
        self.last_content = ""

        logger.info("Clipboard monitor initialized")

    def get_clipboard_content(self) -> Optional[str]:
        """
        Get current clipboard content
        Must be implemented by platform-specific subclass

        Returns:
            Clipboard content as string, or None if unavailable
        """
        raise NotImplementedError("Subclass must implement get_clipboard_content()")

    async def on_clipboard_change(self, content: str):
        """
        Handle clipboard change event

        Args:
            content: New clipboard content
        """
        # Don't process empty content
        if not content or len(content.strip()) == 0:
            return

        # Don't process if same as last
        if content == self.last_content:
            return

        self.last_content = content

        # Determine severity based on content length
        severity = "low"
        if len(content) > 100:
            severity = "medium"

        # Create event
        event = self.agent.create_event(
            event_type="clipboard",
            severity=severity,
            clipboard={
                "content_length": len(content),
                "has_content": True
            },
            content=content[:10000]  # Limit to 10KB
        )

        # Queue event
        await self.agent.queue_event(event)

        logger.debug(
            "Clipboard change detected",
            content_length=len(content)
        )

    async def start(self):
        """
        Start monitoring clipboard
        """
        self.running = True

        logger.info("Starting clipboard monitor")

        while self.running:
            try:
                content = self.get_clipboard_content()

                if content and content != self.last_content:
                    await self.on_clipboard_change(content)

            except Exception as e:
                logger.error(
                    "Error monitoring clipboard",
                    error=str(e)
                )

            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """
        Stop monitoring
        """
        self.running = False
        logger.info("Clipboard monitor stopped")
