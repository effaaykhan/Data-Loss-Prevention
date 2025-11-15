"""
Windows USB Monitor
Uses WMI to detect USB device connections
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from typing import Dict, Any

logger = structlog.get_logger()

# Try to import WMI
try:
    import wmi
    HAS_WMI = True
except ImportError:
    HAS_WMI = False
    logger.warning("WMI not available, USB monitoring disabled")


from common.monitors.usb_monitor import USBMonitor


class WindowsUSBMonitor(USBMonitor):
    """
    Windows-specific USB monitor using WMI
    """

    def __init__(self, agent, poll_interval: int = 5):
        """
        Initialize Windows USB monitor

        Args:
            agent: Parent agent instance
            poll_interval: Polling interval in seconds
        """
        super().__init__(agent, poll_interval)

        if not HAS_WMI:
            logger.error("WMI not available, cannot monitor USB devices")

        self.wmi_client = None
        if HAS_WMI:
            try:
                self.wmi_client = wmi.WMI()
            except Exception as e:
                logger.error(
                    "Failed to initialize WMI",
                    error=str(e)
                )

    def get_usb_devices(self) -> Dict[str, Any]:
        """
        Get currently connected USB devices using WMI

        Returns:
            Dictionary of device_id -> device_info
        """
        devices = {}

        if not HAS_WMI or not self.wmi_client:
            return devices

        try:
            # Query USB devices
            for usb in self.wmi_client.Win32_USBHub():
                device_id = usb.DeviceID

                device_info = {
                    "device_id": device_id,
                    "name": usb.Name or "Unknown",
                    "description": usb.Description or "Unknown",
                    "manufacturer": getattr(usb, 'Manufacturer', 'Unknown'),
                    "status": usb.Status or "Unknown",
                    "pnp_device_id": usb.PNPDeviceID or ""
                }

                devices[device_id] = device_info

            # Also check removable drives
            for disk in self.wmi_client.Win32_DiskDrive(InterfaceType="USB"):
                device_id = disk.DeviceID

                if device_id not in devices:
                    device_info = {
                        "device_id": device_id,
                        "name": disk.Caption or "Unknown",
                        "model": disk.Model or "Unknown",
                        "vendor": getattr(disk, 'Manufacturer', 'Unknown'),
                        "product": disk.Model or "Unknown",
                        "size": disk.Size or 0,
                        "serial": disk.SerialNumber or "Unknown",
                        "media_type": disk.MediaType or "Unknown",
                        "interface": "USB"
                    }

                    devices[device_id] = device_info

        except Exception as e:
            logger.error(
                "Error querying USB devices",
                error=str(e)
            )

        return devices
