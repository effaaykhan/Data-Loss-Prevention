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
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

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
            "policy_sync_interval": 60,  # More responsive bundle refresh (was 300s)
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
            "quarantine": {
                # Global quarantine toggle for this agent
                "enabled": True,
                # Default quarantine folder on Linux endpoints
                "folder": "/home/vansh/quarantine"
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

        # Enforce faster policy sync cadence
        default_config["policy_sync_interval"] = 60
        
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

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion"""
        if not event.is_directory and self._should_monitor(event.src_path):
            self.agent.handle_file_event("file_deleted", event.src_path)

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
        self.policy_bundle = None
        self.policy_file_paths: List[str] = []
        self.has_file_policies: bool = False
        self.allow_events: bool = False
        self.active_policy_version: Optional[str] = None
        self.policy_sync_interval = self.config.get("policy_sync_interval", 60)
        self.policy_capabilities = {"file_monitoring": self.config.get("monitoring", {}).get("file_system", True)}
        self.last_policy_sync_at: Optional[str] = None
        self.last_policy_sync_status: str = "never"
        self.last_policy_sync_error: Optional[str] = None
        self.file_policies: List[Dict[str, Any]] = []

        quarantine_cfg = self.config.get("quarantine", {})
        self.quarantine_enabled: bool = quarantine_cfg.get("enabled", False)
        self.quarantine_folder: Optional[str] = quarantine_cfg.get("folder")
        if self.quarantine_enabled and self.quarantine_folder:
            try:
                os.makedirs(self.quarantine_folder, exist_ok=True)
            except Exception as exc:
                # Do not disable quarantine; policies may supply an alternate folder.
                logger.warning(f"Could not create quarantine folder {self.quarantine_folder}: {exc}")
        # Ensure quarantine folder is excluded from monitoring to prevent loops
        if self.quarantine_folder:
            monitoring_cfg = self.config.get("monitoring", {}) or {}
            exclude_paths = monitoring_cfg.get("exclude_paths", []) or []
            if self.quarantine_folder not in exclude_paths:
                exclude_paths.append(self.quarantine_folder)
                monitoring_cfg["exclude_paths"] = exclude_paths
                # Persist back onto config dictionary safely
                if isinstance(self.config, AgentConfig) and isinstance(self.config.config, dict):
                    self.config.config["monitoring"] = monitoring_cfg
        
        # Deduplication: Track recent events to prevent duplicates
        self.recent_events = {}  # {(file_path, event_type): timestamp}
        self.dedup_window_seconds = 2  # Ignore duplicate events within 2 seconds

        logger.info(f"Agent initialized: {self.agent_id}")

    def start(self):
        """Start the agent"""
        logger.info("Starting CyberSentinel DLP Agent...")
        self.running = True

        # Register agent with server
        self.register_agent()
        self.sync_policies(initial=True)
        if self.policy_sync_interval:
            threading.Thread(target=self.policy_sync_loop, daemon=True).start()

        # Start file system monitoring
        if self.config.get("monitoring", {}).get("file_system", True) and self.has_file_policies:
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
                # Use a real interface IP instead of hostname resolution to avoid 127.0.x/WSL artifacts
                "ip_address": self._get_real_ip_address(),
                "version": "1.0.0",
                "capabilities": self.policy_capabilities
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

    def policy_sync_loop(self):
        while self.running and self.policy_sync_interval:
            time.sleep(self.policy_sync_interval)
            try:
                self.sync_policies()
            except Exception as exc:
                logger.debug(f"Policy sync loop error: {exc}")

    def sync_policies(self, initial: bool = False):
        try:
            logger.info("Syncing policy bundle", extra={"installed_version": self.active_policy_version})
            payload = {
                "platform": "linux",
                "capabilities": self.policy_capabilities,
            }
            if self.active_policy_version:
                payload["installed_version"] = self.active_policy_version

            response = requests.post(
                f"{self.server_url}/agents/{self.agent_id}/policies/sync",
                json=payload,
                timeout=15,
            )
            if response.status_code != 200:
                logger.warning(f"Policy sync failed ({response.status_code}): {response.text}")
                self.last_policy_sync_status = f"error_{response.status_code}"
                self.last_policy_sync_error = response.text
                self.last_policy_sync_at = datetime.utcnow().isoformat() + "Z"
                return

            data = response.json()
            if data.get("status") == "up_to_date":
                logger.info(
                    "Agent policy bundle up to date",
                    extra={"version": self.active_policy_version or data.get("version")}
                )
                self.last_policy_sync_status = "up_to_date"
                self.last_policy_sync_error = None
                self.last_policy_sync_at = datetime.utcnow().isoformat() + "Z"
                return

            self.policy_bundle = data
            self.active_policy_version = data.get("version")
            self.last_policy_sync_status = "success"
            self.last_policy_sync_error = None
            self.last_policy_sync_at = datetime.utcnow().isoformat() + "Z"
            logger.info(
                "Policy bundle updated",
                extra={"version": self.active_policy_version, "count": data.get("policy_count")}
            )
            self._apply_policy_bundle()
        except Exception as e:
            log_method = logger.error if initial else logger.debug
            log_method(f"Failed to sync policies: {e}")
            self.last_policy_sync_status = "exception"
            self.last_policy_sync_error = str(e)
            self.last_policy_sync_at = datetime.utcnow().isoformat() + "Z"

    def _apply_policy_bundle(self):
        if not self.policy_bundle:
            return

        policies = self.policy_bundle.get("policies", {})
        file_policies = policies.get("file_system_monitoring", [])
        usb_transfer_policies = policies.get("usb_file_transfer_monitoring", [])

        # Persist file policies for action handling
        self.file_policies = file_policies

        new_paths: List[str] = []
        for policy in file_policies + usb_transfer_policies:
            config = policy.get("config", {})
            new_paths.extend(config.get("monitoredPaths", []))
        self.policy_file_paths = list(dict.fromkeys(new_paths))

        # Policy presence flags
        self.has_file_policies = bool(file_policies or usb_transfer_policies)
        self.allow_events = self.has_file_policies

        # Reconcile monitoring based on current policies
        self._reconcile_monitors()

    def _restart_file_monitoring(self):
        logger.info("Restarting file monitors with updated policies")
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers = []
        self.start_file_monitoring()

    def _resolve_monitored_paths(self) -> List[str]:
        if self.policy_file_paths:
            return self.policy_file_paths
        monitoring_cfg = self.config.get("monitoring", {})
        return monitoring_cfg.get("monitored_paths", [])

    def _expand_path(self, path: str) -> str:
        expanded = os.path.expandvars(path or "")
        expanded = os.path.expanduser(expanded)
        return expanded

    def start_file_monitoring(self):
        """Start monitoring file system"""
        monitored_paths = self._resolve_monitored_paths()

        for path in monitored_paths:
            expanded_path = self._expand_path(path)
            if os.path.exists(expanded_path):
                event_handler = FileMonitorHandler(self)
                observer = Observer()
                observer.schedule(event_handler, expanded_path, recursive=True)
                observer.start()
                self.observers.append(observer)
                logger.info(f"Monitoring path: {expanded_path}")
            else:
                logger.warning(f"Path does not exist: {expanded_path}")

    def stop_file_monitoring(self):
        """Stop all file observers."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers = []
        logger.info("File monitoring stopped")

    def _reconcile_monitors(self):
        """Start or stop monitors based on active policies."""
        if self.has_file_policies:
            if not self.observers:
                self.start_file_monitoring()
        else:
            if self.observers:
                self.stop_file_monitoring()

    def _is_in_quarantine(self, file_path: str) -> bool:
        """Check if the file resides in the quarantine folder to avoid loops."""
        if not self.quarantine_enabled or not self.quarantine_folder:
            return False
        try:
            return os.path.commonpath([os.path.abspath(file_path), os.path.abspath(self.quarantine_folder)]) == os.path.abspath(self.quarantine_folder)
        except Exception:
            return False

    def _get_quarantine_destination(self, source_path: str) -> str:
        """Compute destination path for a quarantined file."""
        basename = Path(source_path).name
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        unique_name = f"{timestamp}_{uuid.uuid4().hex[:8]}_{basename}"
        return str(Path(self.quarantine_folder) / unique_name)

    def quarantine_file(self, source_path: str, override_folder: Optional[str] = None) -> Optional[str]:
        """Move a file into the quarantine folder. Honors a policy-specified folder when provided."""
        target_folder = override_folder or self.quarantine_folder
        if not target_folder:
            logger.warning(f"No quarantine folder configured; cannot quarantine {source_path}")
            return None
        if not os.path.exists(source_path):
            logger.debug(f"File to quarantine does not exist: {source_path}")
            return None

        try:
            os.makedirs(target_folder, exist_ok=True)
            dest_path = str(Path(target_folder) / Path(self._get_quarantine_destination(source_path)).name)
            shutil.move(source_path, dest_path)
            logger.warning(f"File quarantined: {source_path} -> {dest_path}")
            return dest_path
        except Exception as exc:
            logger.error(f"Failed to quarantine file {source_path}: {exc}", exc_info=True)
            return None

    def block_file_transfer(self, file_path: str) -> bool:
        """Delete a file as a blocking action."""
        try:
            os.remove(file_path)
            logger.warning(f"Blocked and deleted file: {file_path}")
            return True
        except Exception as exc:
            logger.error(f"Failed to delete file during block: {exc}", exc_info=True)
            return False

    def _match_file_policy(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Find the first file system policy whose monitoredPaths include the file."""
        for policy in self.file_policies:
            config = policy.get("config", {})
            monitored_paths = config.get("monitoredPaths", [])
            for path in monitored_paths:
                expanded = self._expand_path(path)
                if file_path.startswith(expanded):
                    return policy
        return None

    def handle_file_event(self, event_type: str, file_path: str):
        """Handle file system event"""
        try:
            if not self.allow_events or not self.has_file_policies:
                return
            if self._is_in_quarantine(file_path):
                logger.debug(f"Skipping event inside quarantine folder: {file_path}")
                return
            # Deduplication: Check if we recently sent an event for this file/type
            dedup_key = (file_path, event_type)
            now = time.time()
            if dedup_key in self.recent_events:
                last_sent = self.recent_events[dedup_key]
                if now - last_sent < self.dedup_window_seconds:
                    logger.debug(f"Skipping duplicate event: {event_type} - {file_path} (last sent {now - last_sent:.2f}s ago)")
                    return
            
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
            content_snippet = content[:5000] if content else None

            # Classify content
            classification = self._classify_content(content)

            # Determine matching policy and action
            matched_policy = self._match_file_policy(file_path)
            policy_config = matched_policy.get("config", {}) if matched_policy else {}
            policy_action = policy_config.get("action", "log").lower()
            event_action = "logged"
            quarantine_path: Optional[str] = None
            quarantine_timestamp: Optional[str] = None

            if policy_action == "block":
                if self.block_file_transfer(file_path):
                    event_action = "blocked"
            elif policy_action == "quarantine":
                target_folder = policy_config.get("quarantinePath") or self.quarantine_folder
                quarantine_path = self.quarantine_file(file_path, target_folder)
                if quarantine_path:
                    event_action = "quarantined"
                    quarantine_timestamp = datetime.utcnow().isoformat() + "Z"
            elif policy_action == "alert":
                event_action = "alert"

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
                "action": event_action,
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "file_size": file_size,
                "file_hash": file_hash,
                "classification": classification,
                "source_path": file_path,
                "content": content_snippet,
                "timestamp": datetime.utcnow().isoformat()
            }

            if matched_policy and matched_policy.get("id"):
                event_data["policy_id"] = matched_policy.get("id")
            if quarantine_path:
                event_data["quarantined"] = True
                event_data["quarantine_path"] = quarantine_path
                event_data["quarantine_timestamp"] = quarantine_timestamp

            if self.active_policy_version:
                event_data["policy_version"] = self.active_policy_version

            self.send_event(event_data)
            
            # Record this event to prevent duplicates
            self.recent_events[dedup_key] = now
            # Clean up old entries (keep only recent 100 entries)
            if len(self.recent_events) > 100:
                cutoff = now - self.dedup_window_seconds
                self.recent_events = {k: v for k, v in self.recent_events.items() if v > cutoff}

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
            if not self.allow_events:
                logger.debug("Dropping event because no active policies")
                return
            if self.active_policy_version and "policy_version" not in event_data:
                event_data["policy_version"] = self.active_policy_version

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
                # Keep heartbeat IP aligned with registration IP
                "ip_address": self._get_real_ip_address(),
            }

            response = requests.put(
                f"{self.server_url}/agents/{self.agent_id}/heartbeat",
                json=self._augment_heartbeat_data(data),
                timeout=30  # Increased timeout to handle slow server responses
            )

            if response.status_code == 200:
                logger.info("Heartbeat sent successfully")
            else:
                logger.warning(f"Heartbeat response: {response.status_code}")

        except Exception as e:
            logger.error(f"Heartbeat failed: {e}", exc_info=True)

    def _augment_heartbeat_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.active_policy_version:
            data["policy_version"] = self.active_policy_version
        if self.last_policy_sync_status:
            data["policy_sync_status"] = self.last_policy_sync_status
        if self.last_policy_sync_at:
            data["policy_last_synced_at"] = self.last_policy_sync_at
        if self.last_policy_sync_error:
            data["policy_sync_error"] = self.last_policy_sync_error
        return data

    def _get_real_ip_address(self) -> str:
        """Get the primary IPv4 address of the Linux machine.

        Prefer a real interface address (not 127.0.0.1 or a container/WSL bridge) by
        opening a UDP socket toward a well-known external IP. No packets are actually
        sent, but the OS chooses the outbound interface and we read its IP.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Use a public resolver IP to determine the primary interface.
                # The remote host does not need to be reachable for getsockname() to work.
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            # Fallback to hostname resolution, and finally loopback as last resort.
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"


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
