"""
CyberSentinel DLP - Windows Endpoint Agent
Monitors file operations, clipboard, and USB devices for data loss prevention
"""

import os
import sys
import time
import json
import logging
import hashlib
import socket
import platform
import threading
import uuid
import signal
import atexit
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import requests
import win32clipboard
import win32con
import wmi
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cybersentinel_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CyberSentinelAgent')


class AgentConfig:
    """Agent configuration"""
    def __init__(self, config_path: str = "agent_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        # Check environment variable first, then config file, then default
        default_server_url = os.getenv("CYBERSENTINEL_SERVER_URL", "http://localhost:55000/api/v1")
        default_config = {
            "server_url": default_server_url,
            "agent_id": str(uuid.uuid4()),
            "agent_name": socket.gethostname(),
            "heartbeat_interval": 30,  # Reduced from 60s to 30s for more frequent updates
            "monitoring": {
                "file_system": True,
                "clipboard": True,
                "usb_devices": True,
                "monitored_paths": [
                    str(Path.home() / "Documents"),
                    str(Path.home() / "Desktop"),
                    str(Path.home() / "Downloads")
                ],
                "file_extensions": [".pdf", ".docx", ".xlsx", ".txt", ".csv", ".json", ".xml"]
            },
            "classification": {
                "enabled": True,
                "max_file_size_mb": 10
            }
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}, using defaults")

        # Environment variable takes precedence over config file
        if os.getenv("CYBERSENTINEL_SERVER_URL"):
            default_config["server_url"] = os.getenv("CYBERSENTINEL_SERVER_URL")

        # Save config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)


class FileMonitorHandler(FileSystemEventHandler):
    """Handles file system events"""

    def __init__(self, agent):
        self.agent = agent
        super().__init__()

    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        if not event.is_directory and self._should_monitor(event.src_path):
            self.agent.handle_file_event("file_created", event.src_path)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if not event.is_directory and self._should_monitor(event.src_path):
            self.agent.handle_file_event("file_modified", event.src_path)

    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename"""
        if not event.is_directory and self._should_monitor(event.dest_path):
            self.agent.handle_file_event("file_moved", event.dest_path)

    def _should_monitor(self, file_path: str) -> bool:
        """Check if file should be monitored"""
        ext = Path(file_path).suffix.lower()
        monitored_exts = self.agent.config.get("monitoring", {}).get("file_extensions", [])
        return ext in monitored_exts if monitored_exts else True


class DLPAgent:
    """Main DLP Agent class"""

    def __init__(self, config_path: str = "agent_config.json"):
        self.config = AgentConfig(config_path)
        self.agent_id = self.config.get("agent_id")
        self.server_url = self.config.get("server_url")
        self.running = False
        self.observers = []
        self.last_clipboard = ""

        logger.info(f"Agent initialized: {self.agent_id}")

    def start(self):
        """Start the agent"""
        logger.info("Starting CyberSentinel DLP Agent...")
        self.running = True

        # Register agent with server
        self.register_agent()

        # Start file system monitoring
        if self.config.get("monitoring", {}).get("file_system", True):
            self.start_file_monitoring()

        # Start clipboard monitoring
        if self.config.get("monitoring", {}).get("clipboard", True):
            threading.Thread(target=self.monitor_clipboard, daemon=True).start()

        # Start USB monitoring
        if self.config.get("monitoring", {}).get("usb_devices", True):
            threading.Thread(target=self.monitor_usb, daemon=True).start()

        # Start heartbeat
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

        logger.info("Agent started successfully")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down agent...")
            self.stop()

    def unregister_agent(self):
        """Unregister agent from server"""
        try:
            response = requests.delete(
                f"{self.server_url}/agents/{self.agent_id}/unregister",
                timeout=5
            )
            if response.status_code in [200, 204]:
                logger.info("Agent unregistered from server")
            else:
                logger.debug(f"Unregister response: {response.status_code}")
        except Exception as e:
            logger.debug(f"Failed to unregister agent: {e}")

    def stop(self):
        """Stop the agent"""
        if not self.running:
            return  # Already stopped
        
        self.running = False
        
        # Unregister from server
        self.unregister_agent()
        
        # Stop file observers
        for observer in self.observers:
            observer.stop()
            observer.join()
        logger.info("Agent stopped")

    def register_agent(self):
        """Register agent with server"""
        try:
            data = {
                "agent_id": self.agent_id,
                "name": self.config.get("agent_name"),
                "hostname": socket.gethostname(),
                "os": "windows",
                "os_version": platform.platform(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "version": "1.0.0",
                "capabilities": {
                    "file_monitoring": True,
                    "clipboard_monitoring": True,
                    "usb_monitoring": True
                }
            }

            response = requests.post(
                f"{self.server_url}/agents",
                json=data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info("Agent registered with server")
            else:
                logger.warning(f"Failed to register agent: {response.status_code}")

        except Exception as e:
            logger.error(f"Error registering agent: {e}")

    def start_file_monitoring(self):
        """Start monitoring file system"""
        monitored_paths = self.config.get("monitoring", {}).get("monitored_paths", [])

        for path in monitored_paths:
            # Expand environment variables (e.g., %USERNAME%)
            expanded_path = os.path.expandvars(path)
            
            if os.path.exists(expanded_path):
                event_handler = FileMonitorHandler(self)
                observer = Observer()
                observer.schedule(event_handler, expanded_path, recursive=True)
                observer.start()
                self.observers.append(observer)
                logger.info(f"Monitoring path: {expanded_path}")
            else:
                logger.warning(f"Path does not exist: {expanded_path}")

    def monitor_clipboard(self):
        """Monitor clipboard for sensitive data"""
        logger.info("Clipboard monitoring started")

        while self.running:
            try:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                        data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                        if data and data != self.last_clipboard:
                            self.last_clipboard = data
                            self.handle_clipboard_event(data.decode('utf-8', errors='ignore'))
                finally:
                    win32clipboard.CloseClipboard()
            except Exception as e:
                logger.debug(f"Clipboard access error: {e}")

            time.sleep(2)

    def monitor_usb(self):
        """Monitor USB device connections"""
        def usb_monitor_thread():
            try:
                # Initialize COM for this thread (required for WMI)
                # Use CoInitializeEx with COINIT_MULTITHREADED for better thread safety
                import pythoncom
                try:
                    # Try CoInitializeEx first (better for multithreaded scenarios)
                    pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
                except AttributeError:
                    # Fallback to CoInitialize if CoInitializeEx not available
                    pythoncom.CoInitialize()
                
                try:
                    logger.info("USB monitoring started")
                    c = wmi.WMI()

                    # Track known devices
                    known_devices = set()

                    while self.running:
                        try:
                            for usb in c.Win32_USBHub():
                                device_id = usb.DeviceID
                                if device_id not in known_devices:
                                    known_devices.add(device_id)
                                    self.handle_usb_event(usb.Name, device_id)
                        except Exception as e:
                            logger.error(f"USB monitoring error: {e}", exc_info=True)

                        time.sleep(5)
                finally:
                    # Cleanup COM
                    try:
                        pythoncom.CoUninitialize()
                    except Exception as e:
                        logger.debug(f"COM cleanup error (non-critical): {e}")
            except Exception as e:
                logger.error(f"USB monitoring failed: {e}", exc_info=True)
        
        # Start USB monitoring in a separate thread
        usb_thread = threading.Thread(target=usb_monitor_thread, daemon=True)
        usb_thread.start()

    def handle_file_event(self, event_type: str, file_path: str):
        """Handle file system event"""
        try:
            logger.info(f"File event detected: {event_type} - {file_path}")
            # Get file info
            file_size = os.path.getsize(file_path)
            max_size = self.config.get("classification", {}).get("max_file_size_mb", 10) * 1024 * 1024

            if file_size > max_size:
                logger.debug(f"File too large, skipping: {file_path}")
                return

            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)

            # Read content for classification
            content = self._read_file_content(file_path, max_bytes=100000)

            # Classify content (simplified - in production, call server API)
            classification = self._classify_content(content)

            # Send event to server
            event_data = {
                "event_id": str(uuid.uuid4()),
                "event_type": "file",
                "event_subtype": event_type,
                "agent_id": self.agent_id,
                "source_type": "agent",
                "user_email": f"{os.getlogin()}@{socket.gethostname()}",
                "description": f"{event_type}: {Path(file_path).name}",
                "severity": classification.get("severity", "low"),
                "action": "logged",
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "file_size": file_size,
                "file_hash": file_hash,
                "classification": classification,
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Sending file event: {event_type} - {Path(file_path).name} - Severity: {classification.get('severity', 'low')}")
            self.send_event(event_data)

        except Exception as e:
            logger.error(f"Error handling file event: {e}", exc_info=True)

    def handle_clipboard_event(self, content: str):
        """Handle clipboard event"""
        try:
            # Classify clipboard content
            classification = self._classify_content(content)

            if classification.get("labels"):
                event_data = {
                    "event_id": str(uuid.uuid4()),
                    "event_type": "clipboard",
                    "event_subtype": "clipboard_copy",
                    "agent_id": self.agent_id,
                    "source_type": "agent",
                    "user_email": f"{os.getlogin()}@{socket.gethostname()}",
                    "description": "Sensitive data copied to clipboard",
                    "severity": classification.get("severity", "medium"),
                    "action": "alerted",
                    "classification": classification,
                    "details": {
                        "content_preview": content[:200] if len(content) > 200 else content
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

                self.send_event(event_data)
                logger.info(f"Clipboard event: {classification.get('labels')}")

        except Exception as e:
            logger.error(f"Error handling clipboard event: {e}")

    def handle_usb_event(self, device_name: str, device_id: str):
        """Handle USB device event"""
        try:
            event_data = {
                "event_id": str(uuid.uuid4()),
                "event_type": "usb",
                "event_subtype": "usb_connected",
                "agent_id": self.agent_id,
                "source_type": "agent",
                "user_email": f"{os.getlogin()}@{socket.gethostname()}",
                "description": f"USB device connected: {device_name}",
                "severity": "medium",
                "action": "logged",
                "details": {
                    "device_name": device_name,
                    "device_id": device_id
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            self.send_event(event_data)
            logger.info(f"USB device connected: {device_name}")

        except Exception as e:
            logger.error(f"Error handling USB event: {e}")

    def _classify_content(self, content: str) -> Dict[str, Any]:
        """Classify content for sensitive data"""
        import re

        labels = []
        severity = "low"

        # Credit card detection
        if re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', content):
            labels.append("PAN")
            severity = "critical"

        # SSN detection
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', content):
            labels.append("SSN")
            severity = "critical"

        # Email detection
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content):
            labels.append("EMAIL")
            if severity == "low":
                severity = "medium"

        # API key patterns
        if re.search(r'api[_-]?key|secret[_-]?key|access[_-]?token', content, re.IGNORECASE):
            labels.append("API_KEY")
            severity = "high"

        return {
            "labels": labels,
            "severity": severity,
            "score": 0.9 if labels else 0.1,
            "method": "regex"
        }

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return ""

    def _read_file_content(self, file_path: str, max_bytes: int = 100000) -> str:
        """Read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_bytes)
        except:
            return ""

    def send_event(self, event_data: Dict[str, Any]):
        """Send event to server"""
        try:
            response = requests.post(
                f"{self.server_url}/events",
                json=event_data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.debug("Event sent successfully")
            else:
                logger.warning(f"Failed to send event: {response.status_code}")

        except Exception as e:
            logger.error(f"Error sending event: {e}")

    def heartbeat_loop(self):
        """Send periodic heartbeat to server"""
        # Reduced interval from 60s to 30s for more frequent updates
        interval = self.config.get("heartbeat_interval", 30)

        while self.running:
            try:
                self.send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

            time.sleep(interval)

    def send_heartbeat(self):
        """Send heartbeat to server with timestamp"""
        try:
            # Send timestamp in ISO format for server validation
            data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "ip_address": socket.gethostbyname(socket.gethostname())
            }

            response = requests.put(
                f"{self.server_url}/agents/{self.agent_id}/heartbeat",
                json=data,
                timeout=30  # Increased timeout to handle slow server responses
            )

            if response.status_code == 200:
                logger.info("Heartbeat sent successfully")
            else:
                logger.warning(f"Heartbeat response: {response.status_code}")

        except Exception as e:
            logger.error(f"Heartbeat failed: {e}", exc_info=True)


def main():
    """Main entry point"""
    print("=" * 60)
    print("CyberSentinel DLP - Windows Agent")
    print("=" * 60)
    print()

    agent = DLPAgent()
    
    # Register signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        agent.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register atexit handler as backup
    atexit.register(agent.stop)
    
    agent.start()


if __name__ == "__main__":
    main()
