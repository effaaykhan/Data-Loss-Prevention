"""
Linux USB Monitor
Uses pyudev to detect USB device connections
"""

import structlog
from typing import Dict, Any

logger = structlog.get_logger()

# Try to import pyudev
try:
    import pyudev
    HAS_PYUDEV = True
except ImportError:
    HAS_PYUDEV = False
    logger.warning("pyudev not available, USB monitoring disabled")


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.monitors.usb_monitor import USBMonitor


class LinuxUSBMonitor(USBMonitor):
    """
    Linux-specific USB monitor using pyudev
    """

    def __init__(self, agent, poll_interval: int = 5):
        """
        Initialize Linux USB monitor

        Args:
            agent: Parent agent instance
            poll_interval: Polling interval in seconds
        """
        super().__init__(agent, poll_interval)

        if not HAS_PYUDEV:
            logger.error("pyudev not available, cannot monitor USB devices")

        self.context = None
        if HAS_PYUDEV:
            try:
                self.context = pyudev.Context()
            except Exception as e:
                logger.error(
                    "Failed to initialize pyudev context",
                    error=str(e)
                )

    def get_usb_devices(self) -> Dict[str, Any]:
        """
        Get currently connected USB devices using pyudev

        Returns:
            Dictionary of device_id -> device_info
        """
        devices = {}

        if not HAS_PYUDEV or not self.context:
            return devices

        try:
            # Query USB devices
            for device in self.context.list_devices(subsystem='usb', DEVTYPE='usb_device'):
                device_path = device.device_path

                # Get device attributes
                id_vendor = device.get('ID_VENDOR_ID', 'Unknown')
                id_product = device.get('ID_MODEL_ID', 'Unknown')
                vendor_name = device.get('ID_VENDOR', 'Unknown')
                product_name = device.get('ID_MODEL', 'Unknown')
                serial = device.get('ID_SERIAL_SHORT', 'Unknown')

                device_id = f"{id_vendor}:{id_product}:{serial}"

                device_info = {
                    "device_id": device_id,
                    "vendor_id": id_vendor,
                    "product_id": id_product,
                    "vendor": vendor_name,
                    "product": product_name,
                    "serial": serial,
                    "device_path": device_path,
                    "subsystem": "usb"
                }

                devices[device_id] = device_info

            # Also check block devices (USB drives)
            for device in self.context.list_devices(subsystem='block', DEVTYPE='disk'):
                # Check if it's a USB device
                if device.get('ID_BUS') == 'usb':
                    device_node = device.device_node
                    id_vendor = device.get('ID_VENDOR_ID', 'Unknown')
                    id_product = device.get('ID_MODEL_ID', 'Unknown')
                    serial = device.get('ID_SERIAL_SHORT', 'Unknown')

                    device_id = f"{id_vendor}:{id_product}:{serial}:block"

                    if device_id not in devices:
                        device_info = {
                            "device_id": device_id,
                            "vendor_id": id_vendor,
                            "product_id": id_product,
                            "vendor": device.get('ID_VENDOR', 'Unknown'),
                            "product": device.get('ID_MODEL', 'Unknown'),
                            "serial": serial,
                            "device_node": device_node,
                            "subsystem": "block",
                            "fs_type": device.get('ID_FS_TYPE', 'Unknown'),
                            "size": device.get('ID_FS_SIZE', 0)
                        }

                        devices[device_id] = device_info

        except Exception as e:
            logger.error(
                "Error querying USB devices",
                error=str(e)
            )

        return devices
