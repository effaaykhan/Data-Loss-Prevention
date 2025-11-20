"""
USB Device Monitor
Monitors USB device connections/disconnections
"""

import asyncio
import structlog
from typing import Dict, Any

logger = structlog.get_logger()


class USBMonitor:
    """
    USB device monitor
    Platform-specific implementation in subclasses
    """

    def __init__(self, agent, poll_interval: int = 5):
        """
        Initialize USB monitor

        Args:
            agent: Parent agent instance
            poll_interval: Polling interval in seconds
        """
        self.agent = agent
        self.poll_interval = poll_interval
        self.running = False
        self.known_devices = set()

        logger.info("USB monitor initialized")

    def get_usb_devices(self) -> Dict[str, Any]:
        """
        Get currently connected USB devices
        Must be implemented by platform-specific subclass

        Returns:
            Dictionary of device_id -> device_info
        """
        raise NotImplementedError("Subclass must implement get_usb_devices()")

    async def on_device_connected(self, device_info: Dict[str, Any]):
        """
        Handle USB device connection

        Args:
            device_info: Device information dictionary
        """
        # Create event
        event = self.agent.create_event(
            event_type="usb",
            severity="medium",
            usb=device_info,
            action={"type": "connected"}
        )

        # Queue event
        await self.agent.queue_event(event)

        logger.info(
            "USB device connected",
            device_id=device_info.get("device_id"),
            vendor=device_info.get("vendor"),
            product=device_info.get("product")
        )

    async def on_device_disconnected(self, device_info: Dict[str, Any]):
        """
        Handle USB device disconnection

        Args:
            device_info: Device information dictionary
        """
        # Create event
        event = self.agent.create_event(
            event_type="usb",
            severity="low",
            usb=device_info,
            action={"type": "disconnected"}
        )

        # Queue event
        await self.agent.queue_event(event)

        logger.info(
            "USB device disconnected",
            device_id=device_info.get("device_id")
        )

    async def start(self):
        """
        Start monitoring USB devices
        """
        self.running = True

        logger.info("Starting USB monitor")

        # Get initial device list
        try:
            devices = self.get_usb_devices()
            self.known_devices = set(devices.keys())
            logger.info(
                "Initial USB devices",
                count=len(self.known_devices)
            )
        except Exception as e:
            logger.error(
                "Error getting initial USB devices",
                error=str(e)
            )

        # Poll for changes
        while self.running:
            try:
                current_devices = self.get_usb_devices()
                current_ids = set(current_devices.keys())

                # Find new devices
                new_devices = current_ids - self.known_devices
                for device_id in new_devices:
                    await self.on_device_connected(current_devices[device_id])

                # Find removed devices
                removed_devices = self.known_devices - current_ids
                for device_id in removed_devices:
                    # Create minimal device info
                    device_info = {"device_id": device_id}
                    await self.on_device_disconnected(device_info)

                # Update known devices
                self.known_devices = current_ids

            except Exception as e:
                logger.error(
                    "Error monitoring USB devices",
                    error=str(e)
                )

            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """
        Stop monitoring
        """
        self.running = False
        logger.info("USB monitor stopped")
