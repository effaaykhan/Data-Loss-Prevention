"""
CyberSentinel DLP - Linux Endpoint Agent
Monitors file operations for data loss prevention on Linux systems
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
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# Configure logging
log_file = os.path.expanduser('~/cybersentinel_agent.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CyberSentinelAgent')


class AgentConfig:
    """Agent configuration"""
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Use local config file if /etc is not accessible
            local_config = os.path.expanduser("~/cybersentinel_agent_config.json")
            if os.path.exists("/etc/cybersentinel/agent_config.json"):
                self.config_path = "/etc/cybersentinel/agent_config.json"
            elif os.path.exists("agent_config.json"):
                self.config_path = "agent_config.json"
            else:
                self.config_path = local_config
        else:
            self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        # Check environment variable first, then config file, then default
        default_server_url = os.getenv("CYBERSENTINEL_SERVER_URL", "http://localhost:55000/api/v1")
        default_config = {
            "server_url": default_server_url,
            "agent_id": str(uuid.uuid4()),
            "agent_name": "Linux-Agent",  # Default name for Linux agents
            "heartbeat_interval": 30,  # Reduced from 60s to 30s for more frequent updates
            "monitoring": {
                "file_system": True,
                "monitored_paths": [
                    "/home",
                    "/var/www",
                    "/opt/data"
                ],
                "exclude_paths": [
                    "/home/*/.cache",
                    "/home/*/.local/share",
                    "/home/*/snap"
                ],
                "file_extensions": [".pdf", ".docx", ".xlsx", ".txt", ".csv", ".json", ".xml", ".sql", ".conf"]
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
        
        # Save config (create directory if needed and accessible)
        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                try:
                    os.makedirs(config_dir, exist_ok=True)
                except PermissionError:
                    # Fall back to current directory if can't create parent
                    self.config_path = os.path.basename(self.config_path)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save config: {e}")

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
        # Check exclusions
        exclude_paths = self.agent.config.get("monitoring", {}).get("exclude_paths", [])
        for exclude in exclude_paths:
            if file_path.startswith(exclude.replace("*", "")):
                return False

        # Check extensions
        ext = Path(file_path).suffix.lower()
        monitored_exts = self.agent.config.get("monitoring", {}).get("file_extensions", [])
        return ext in monitored_exts if monitored_exts else True


class DLPAgent:
    """Main DLP Agent class"""

    def __init__(self, config_path: str = "/etc/cybersentinel/agent_config.json"):
        self.config = AgentConfig(config_path)
        self.agent_id = self.config.get("agent_id")
        self.server_url = self.config.get("server_url")
        self.running = False
        self.observers = []

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
            # Get current user
            import pwd
            current_user = pwd.getpwuid(os.getuid()).pw_name

            data = {
                "agent_id": self.agent_id,
                "name": self.config.get("agent_name"),
                "hostname": socket.gethostname(),
                "os": "linux",
                "os_version": platform.platform(),
                "ip_address": socket.gethostbyname(socket.gethostname()),
                "version": "1.0.0",
                "capabilities": {
                    "file_monitoring": True,
                    "clipboard_monitoring": False,
                    "usb_monitoring": False
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
            if os.path.exists(path):
                event_handler = FileMonitorHandler(self)
                observer = Observer()
                observer.schedule(event_handler, path, recursive=True)
                observer.start()
                self.observers.append(observer)
                logger.info(f"Monitoring path: {path}")
            else:
                logger.warning(f"Path does not exist: {path}")

    def handle_file_event(self, event_type: str, file_path: str):
        """Handle file system event"""
        try:
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

            # Classify content
            classification = self._classify_content(content)

            # Get current user
            import pwd
            current_user = pwd.getpwuid(os.getuid()).pw_name

            # Send event to server
            event_data = {
                "event_id": str(uuid.uuid4()),
                "event_type": "file",
                "event_subtype": event_type,
                "agent_id": self.agent_id,
                "source_type": "agent",
                "user_email": f"{current_user}@{socket.gethostname()}",
                "username": current_user,
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

            self.send_event(event_data)

        except Exception as e:
            logger.error(f"Error handling file event: {e}")

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
        if re.search(r'api[_-]?key|secret[_-]?key|access[_-]?token|password\s*=', content, re.IGNORECASE):
            labels.append("API_KEY")
            severity = "high"

        # Private key detection
        if re.search(r'-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----', content):
            labels.append("PRIVATE_KEY")
            severity = "critical"

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
    print("CyberSentinel DLP - Linux Agent")
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
