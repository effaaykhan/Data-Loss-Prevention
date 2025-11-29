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
from typing import Dict, Any, Optional, List

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
            "policy_sync_interval": 60,  # More responsive bundle refresh (was 300s)
            "monitoring": {
                "file_system": True,
                "clipboard": True,
                "usb_devices": True,
                "monitored_paths": [
                    str(Path.home() / "Documents"),
                    str(Path.home() / "Desktop"),
                    str(Path.home() / "Downloads")
                ],
                "file_extensions": [".pdf", ".docx", ".xlsx", ".txt", ".csv", ".json", ".xml"],
                "transfer_blocking": {
                    "enabled": False,
                    "block_removable_drives": True,
                    "poll_interval_seconds": 5
                }
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

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion"""
        if not event.is_directory and self._should_monitor(event.src_path):
            self.agent.handle_file_event("file_deleted", event.src_path)

    def _should_monitor(self, file_path: str) -> bool:
        """Check if file should be monitored"""
        ext = Path(file_path).suffix.lower()
        monitored_exts = self.agent.config.get("monitoring", {}).get("file_extensions", [])
        return ext in monitored_exts if monitored_exts else True


class RemovableDriveHandler(FileSystemEventHandler):
    """Handles file system events on removable drives"""
    
    def __init__(self, agent, drive_letter: str):
        self.agent = agent
        self.drive_letter = drive_letter
        super().__init__()
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation on removable drive"""
        if not event.is_directory:
            self.agent.handle_removable_drive_file(event.src_path)


class DLPAgent:
    """Main DLP Agent class"""

    def __init__(self, config_path: str = "agent_config.json"):
        self.config = AgentConfig(config_path)
        self.agent_id = self.config.get("agent_id")
        self.server_url = self.config.get("server_url")
        self.running = False
        self.observers = []
        self.last_clipboard = ""
        self.policy_bundle = None
        self.policy_file_paths: List[str] = []
        self.policy_clipboard_rules: List[Dict[str, Any]] = []
        self.usb_transfer_policies: List[Dict[str, Any]] = []
        self.usb_transfer_policy_present: bool = False
        self.has_any_policies: bool = False
        self.has_file_policies: bool = False
        self.has_clipboard_policies: bool = False
        self.has_usb_device_policies: bool = False
        self.has_usb_transfer_policies: bool = False
        self.has_gdrive_local_policies: bool = False
        self.allow_events: bool = False
        self.active_policy_version: Optional[str] = None
        self.policy_sync_interval = self.config.get("policy_sync_interval", 60)
        self.policy_capabilities = self._get_policy_capabilities()
        self.last_policy_sync_at: Optional[str] = None
        self.last_policy_sync_status: str = "never"
        self.last_policy_sync_error: Optional[str] = None
        
        # Transfer blocking: Track removable drives and monitored directories
        self.removable_drives = set()  # Track current removable drive letters: {'E:', 'F:'}
        self.removable_observers = {}  # Track observers: {'E:': Observer instance}
        self.monitored_directories = []  # List of monitored directory paths (expanded)
        self.transfer_blocking_config = self.config.get("monitoring", {}).get("transfer_blocking", {})
        self.transfer_blocking_enabled = bool(self.transfer_blocking_config.get("enabled", False))
        self.transfer_blocking_thread_started = False
        
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

        # Start clipboard monitoring
        if self.config.get("monitoring", {}).get("clipboard", True):
            threading.Thread(target=self.monitor_clipboard, daemon=True).start()

        # Start USB monitoring
        if self.config.get("monitoring", {}).get("usb_devices", True):
            threading.Thread(target=self.monitor_usb, daemon=True).start()

        # Start removable drive monitoring for transfer blocking
        self._ensure_transfer_blocking_thread()

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
        
        # Stop removable drive observers
        for drive, observer in self.removable_observers.items():
            observer.stop()
            observer.join()
        self.removable_observers.clear()
        
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

    def _get_policy_capabilities(self) -> Dict[str, bool]:
        monitoring_cfg = self.config.get("monitoring", {})
        return {
            "file_monitoring": bool(monitoring_cfg.get("file_system", True)),
            "clipboard_monitoring": bool(monitoring_cfg.get("clipboard", True)),
            "usb_monitoring": bool(monitoring_cfg.get("usb_devices", True)),
        }

    def policy_sync_loop(self):
        """Background loop to periodically sync policies."""
        while self.running and self.policy_sync_interval:
            time.sleep(self.policy_sync_interval)
            try:
                self.sync_policies()
            except Exception as exc:
                logger.debug(f"Policy sync loop error: {exc}")

    def sync_policies(self, initial: bool = False):
        """Fetch policies from server and apply them."""
        try:
            logger.info("Syncing policy bundle", extra={"installed_version": self.active_policy_version})
            payload = {
                "platform": "windows",
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
        """Apply bundle to runtime configuration."""
        if not self.policy_bundle:
            return

        policies = self.policy_bundle.get("policies", {})
        file_policies = policies.get("file_system_monitoring", [])
        clipboard_policies = policies.get("clipboard_monitoring", [])
        usb_transfer_policies = policies.get("usb_file_transfer_monitoring", [])
        google_drive_local_policies = policies.get("google_drive_local_monitoring", [])
        usb_device_policies = policies.get("usb_device_monitoring", [])

        new_file_paths: List[str] = []
        for policy in file_policies + usb_transfer_policies:
            config = policy.get("config", {})
            paths = self._normalize_path_list(config.get("monitoredPaths", []))
            new_file_paths.extend(paths)
        
        # Process Google Drive local monitoring policies
        for policy in google_drive_local_policies:
            config = policy.get("config", {})
            # Align default with backend transformer ("G:\\My Drive\\")
            base_path = config.get("basePath", "G:\\My Drive\\")
            # Ensure base_path ends with backslash
            if not base_path.endswith("\\"):
                base_path = base_path + "\\"
            
            monitored_folders = config.get("monitoredFolders", [])
            if monitored_folders:
                for folder in monitored_folders:
                    # Normalize folder path
                    folder = folder.strip().replace("/", "\\").strip("\\")
                    if folder:
                        full_path = base_path + folder
                        if not full_path.endswith("\\"):
                            full_path = full_path + "\\"
                        new_file_paths.append(self._normalize_filesystem_path(full_path))
            else:
                # If no folders specified, monitor entire base path
                new_file_paths.append(self._normalize_filesystem_path(base_path))
        
        self.policy_file_paths = list(dict.fromkeys(new_file_paths))
        self.policy_clipboard_rules = clipboard_policies
        # Normalize paths inside USB transfer policies for reliable matching
        self.usb_transfer_policies = self._normalize_usb_transfer_policies(usb_transfer_policies)
        self.usb_transfer_policy_present = bool(self.usb_transfer_policies)

        # Derive capability flags from bundle
        self.has_file_policies = bool(file_policies or google_drive_local_policies or usb_transfer_policies)
        self.has_clipboard_policies = bool(clipboard_policies)
        self.has_usb_device_policies = bool(usb_device_policies)
        self.has_usb_transfer_policies = bool(usb_transfer_policies)
        self.has_gdrive_local_policies = bool(google_drive_local_policies)
        self.has_any_policies = any([
            self.has_file_policies,
            self.has_clipboard_policies,
            self.has_usb_device_policies,
            self.has_usb_transfer_policies,
            self.has_gdrive_local_policies,
        ])
        self.allow_events = self.has_any_policies

        # If policies require transfer blocking, enable the watcher even if config file has it disabled
        if self.usb_transfer_policy_present and not self.transfer_blocking_enabled:
            self.transfer_blocking_enabled = True
            logger.info("Enabling removable drive monitoring due to usb_file_transfer_monitoring policies")

        # Reconcile monitor state with current policies
        self._reconcile_monitors()

    def _resolve_monitored_paths(self) -> List[str]:
        """Determine effective monitored paths based on policy bundle."""
        if self.policy_file_paths:
            return self.policy_file_paths
        monitoring_cfg = self.config.get("monitoring", {})
        return monitoring_cfg.get("monitored_paths", [])

    def _restart_file_monitoring(self):
        """Restart file observers with new configuration."""
        logger.info("Restarting file monitoring with updated policies")
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers = []
        self.start_file_monitoring()

    def _expand_path(self, path: str) -> str:
        """Expand env variables and user tokens in path."""
        expanded = os.path.expandvars(path or "")
        expanded = os.path.expanduser(expanded)
        return expanded

    def _match_usb_transfer_policy(self, source_path: str) -> Optional[Dict[str, Any]]:
        """Find matching USB transfer policy for a given source path."""
        if not self.usb_transfer_policies or not source_path:
            return None

        normalized_src = self._normalize_compare_path(source_path)
        for policy in self.usb_transfer_policies:
            config = policy.get("config", {})
            for path in config.get("monitoredPaths", []):
                expanded = self._normalize_compare_path(path)
                if expanded and self._is_path_prefix(normalized_src, expanded):
                    return policy
        return None

    def start_file_monitoring(self):
        """Start monitoring file system"""
        if not self.has_file_policies:
            logger.info("Skipping file monitoring start; no active file/drive/usb-transfer policies")
            return

        monitored_paths = self._resolve_monitored_paths()
        self.monitored_directories = []  # Track monitored directories for transfer blocking

        if not monitored_paths:
            logger.warning("No monitored paths configured for file monitoring")
            return

        for path in monitored_paths:
            # Expand and normalize environment variables (e.g., %USERNAME%)
            expanded_path = self._normalize_filesystem_path(path)
            
            if os.path.exists(expanded_path):
                self.monitored_directories.append(expanded_path)  # Track for transfer blocking
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
        self.monitored_directories = []
        logger.info("File monitoring stopped")

    def monitor_clipboard(self):
        """Monitor clipboard for sensitive data"""
        logger.info("Clipboard monitoring started")

        while self.running:
            if not self.has_clipboard_policies or not self.allow_events:
                time.sleep(2)
                continue
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
                        if not self.has_usb_device_policies or not self.allow_events:
                            time.sleep(5)
                            continue
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

    def get_removable_drives(self) -> List[str]:
        """
        Get list of removable drive letters using WMI
        
        Returns:
            List of drive letters (e.g., ['E:', 'F:'])
        """
        try:
            import pythoncom
            pythoncom.CoInitialize()
            c = wmi.WMI()
            drives = []
            for disk in c.Win32_LogicalDisk(DriveType=2):  # DriveType 2 = Removable
                drive_letter = disk.DeviceID  # e.g., "E:"
                if os.path.exists(drive_letter):
                    drives.append(drive_letter)
            pythoncom.CoUninitialize()
            return drives
        except Exception as e:
            logger.error(f"Error detecting removable drives: {e}")
            return []

    def monitor_removable_drives(self):
        """
        Monitor removable drives for file operations
        Runs in background thread, polls for new drives periodically
        """
        poll_interval = self.config.get("monitoring", {}).get("transfer_blocking", {}).get("poll_interval_seconds", 5)
        
        while self.running:
            try:
                if not self.transfer_blocking_enabled or not self.has_usb_transfer_policies or not self.allow_events:
                    time.sleep(poll_interval)
                    continue

                current_drives = set(self.get_removable_drives())
                
                # Find newly connected drives
                new_drives = current_drives - self.removable_drives
                for drive in new_drives:
                    self._start_monitoring_removable_drive(drive)
                
                # Find disconnected drives
                disconnected_drives = self.removable_drives - current_drives
                for drive in disconnected_drives:
                    self._stop_monitoring_removable_drive(drive)
                
                self.removable_drives = current_drives
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error monitoring removable drives: {e}")
                time.sleep(poll_interval)

    def _start_monitoring_removable_drive(self, drive_letter: str):
        """
        Start monitoring a specific removable drive
        
        Args:
            drive_letter: Drive letter to monitor (e.g., "E:")
        """
        try:
            if drive_letter in self.removable_observers:
                return  # Already monitoring
            
            logger.info(f"Starting monitoring for removable drive: {drive_letter}")
            
            # Create handler specifically for removable drives
            handler = RemovableDriveHandler(self, drive_letter)
            observer = Observer()
            observer.schedule(handler, drive_letter, recursive=True)
            observer.start()
            
            self.removable_observers[drive_letter] = observer
            logger.info(f"Monitoring started for {drive_letter}")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring {drive_letter}: {e}")

    def _stop_monitoring_removable_drive(self, drive_letter: str):
        """Stop monitoring a disconnected removable drive"""
        if drive_letter in self.removable_observers:
            observer = self.removable_observers.pop(drive_letter)
            observer.stop()
            observer.join()
            logger.info(f"Stopped monitoring {drive_letter}")

    def handle_file_event(self, event_type: str, file_path: str):
        """Handle file system event"""
        try:
            if not self.allow_events or not self.has_file_policies:
                return
            # Deduplication: Check if we recently sent an event for this file/type
            dedup_key = (file_path, event_type)
            now = time.time()
            if dedup_key in self.recent_events:
                last_sent = self.recent_events[dedup_key]
                if now - last_sent < self.dedup_window_seconds:
                    logger.debug(f"Skipping duplicate event: {event_type} - {file_path} (last sent {now - last_sent:.2f}s ago)")
                    return
            
            logger.info(f"File event detected: {event_type} - {file_path}")

            max_size = self.config.get("classification", {}).get("max_file_size_mb", 10) * 1024 * 1024
            retry_attempts = self.config.get("file_access_retries", 3)
            retry_delay = self.config.get("file_access_retry_delay", 1.0)

            file_size = None
            for attempt in range(retry_attempts):
                try:
                    file_size = os.path.getsize(file_path)
                    break
                except PermissionError:
                    if attempt < retry_attempts - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(
                            f"File locked when checking size (attempt {attempt + 1}/{retry_attempts}) - {file_path}. "
                            f"Retrying in {wait_time:.1f}s"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Unable to read file size due to permissions: {file_path}")
            if file_size is None:
                logger.error(f"Unable to read file size after retries, continuing with 0 bytes: {file_path}")
                file_size = 0
                access_denied = True
            else:
                access_denied = False

            if file_size > max_size:
                logger.debug(f"File too large, skipping: {file_path}")
                return

            # Attempt to read file metadata/content, retrying if Google Drive still locks the file
            file_hash = ""
            content = ""
            # Preserve existing flag if we already hit access issues determining size
            access_denied_flag = access_denied

            for attempt in range(retry_attempts):
                try:
                    file_hash = self._calculate_file_hash(file_path)
                    content = self._read_file_content(file_path, max_bytes=100000)
                    access_denied_flag = False
                    break
                except PermissionError:
                    access_denied_flag = True
                    if attempt < retry_attempts - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(
                            f"File locked (attempt {attempt + 1}/{retry_attempts}) - {file_path}. "
                            f"Retrying in {wait_time:.1f}s"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Permission denied after {retry_attempts} attempts. "
                            f"Sending event without content/hash: {file_path}"
                        )

            content_snippet = content[:5000] if content else None

            # Classify content (simplified - in production, call server API)
            classification = self._classify_content(content or "")

            # Check if this is a Google Drive local event (G:\ drive)
            is_google_drive_local = file_path.upper().startswith("G:\\")
            source_type_value = "google_drive_local" if is_google_drive_local else "endpoint"

            # Send event to server
            event_data = {
                "event_id": str(uuid.uuid4()),
                "event_type": "file",
                "event_subtype": event_type,
                "agent_id": self.agent_id,
                "source_type": source_type_value,
                "source": "google_drive_local" if is_google_drive_local else "file_system",
                "user_email": f"{os.getlogin()}@{socket.gethostname()}",
                "description": f"{event_type}: {Path(file_path).name}",
                "severity": classification.get("severity", "low"),
                "action": "logged",
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "file_size": file_size,
                "file_hash": file_hash,
                "classification": classification,
                "source_path": file_path,
                "content": content_snippet,
                "timestamp": datetime.utcnow().isoformat()
            }

            if self.active_policy_version:
                event_data["policy_version"] = self.active_policy_version
            if access_denied_flag:
                event_data["content_access_denied"] = True

            logger.info(f"Sending file event: {event_type} - {Path(file_path).name} - Severity: {classification.get('severity', 'low')}")
            self.send_event(event_data)
            
            # Record this event to prevent duplicates
            self.recent_events[dedup_key] = now
            # Clean up old entries (keep only recent 100 entries)
            if len(self.recent_events) > 100:
                cutoff = now - self.dedup_window_seconds
                self.recent_events = {k: v for k, v in self.recent_events.items() if v > cutoff}

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
                    "content": content[:5000],
                    "details": {
                        "content_preview": content[:200] if len(content) > 200 else content
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

                if self.active_policy_version:
                    event_data["policy_version"] = self.active_policy_version

                self.send_event(event_data)
                logger.info(f"Clipboard event: {classification.get('labels')}")

        except Exception as e:
            logger.error(f"Error handling clipboard event: {e}")

    def handle_usb_event(self, device_name: str, device_id: str):
        """Handle USB device event"""
        try:
            if not self.allow_events or not self.has_usb_device_policies:
                return
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

    def handle_removable_drive_file(self, file_path: str):
        """
        Handle file created on removable drive
        Check if it matches a file from monitored directory
        
        Args:
            file_path: Path to file on removable drive (e.g., "E:\\document.pdf")
        """
        try:
            if not self.allow_events or not self.has_usb_transfer_policies:
                return
            logger.info(f"File detected on removable drive: {file_path}")
            
            # Normalize path (handle both E:file.txt and E:\file.txt)
            if not file_path.startswith("\\"):
                # Fix path format if missing backslash after drive letter
                if len(file_path) > 1 and file_path[1] == ":" and file_path[2] != "\\":
                    file_path = file_path[:2] + "\\" + file_path[2:]
            
            # Get file info
            if not os.path.exists(file_path):
                logger.debug(f"File no longer exists: {file_path}")
                return
            
            file_size = os.path.getsize(file_path)
            file_name = Path(file_path).name
            logger.info(f"File info - Name: {file_name}, Size: {file_size} bytes")
            
            # Wait a bit for file copy to complete (Windows Explorer may still have file locked)
            time.sleep(0.3)
            
            # Calculate hash (with retry in case file is locked during copy)
            file_hash = None
            for attempt in range(5):  # Increased to 5 attempts
                try:
                    file_hash = self._calculate_file_hash(file_path)
                    if file_hash:
                        break
                except PermissionError:
                    # File is locked, wait longer and retry
                    wait_time = 0.5 * (attempt + 1)  # Increasing wait time: 0.5s, 1s, 1.5s, 2s
                    if attempt < 4:
                        logger.debug(f"File locked, waiting {wait_time}s before retry (attempt {attempt + 1}/5)")
                        time.sleep(wait_time)
                    continue
                except Exception as e:
                    if attempt < 4:
                        logger.debug(f"Hash calculation error, retrying in 0.5s (attempt {attempt + 1}/5): {e}")
                        time.sleep(0.5)
                    continue
            
            if not file_hash:
                logger.error(f"Failed to calculate hash for: {file_path} after 5 attempts")
                return
            logger.info(f"File hash calculated: {file_hash[:16]}... (length: {len(file_hash)})")
            
            # Check monitored directories
            logger.info(f"Checking {len(self.monitored_directories)} monitored directories: {self.monitored_directories}")
            
            # Check if identical file exists in monitored directories
            source_file = self._find_source_file_in_monitored_dirs(file_hash, file_size, file_name)
            
            if source_file:
                logger.warning(f"Copy detected: {source_file} -> {file_path}")

                policy = self._match_usb_transfer_policy(source_file)
                if not policy:
                    logger.info("No USB transfer policy matched; leaving file in place")
                    return

                policy_action = policy.get("config", {}).get("action", "block").lower()
                blocked = False
                if policy_action == "block":
                    blocked = self.block_file_transfer(file_path)

                # Send blocked transfer event
                self._send_blocked_transfer_event(
                    source_file,
                    file_path,
                    file_hash,
                    file_size,
                    blocked,
                    policy=policy,
                    action=policy_action,
                )
            else:
                logger.info(f"File on removable drive not found in monitored directories: {file_path} (Name: {file_name}, Size: {file_size})")
                
        except Exception as e:
            logger.error(f"Error handling removable drive file: {e}", exc_info=True)

    def _find_source_file_in_monitored_dirs(self, file_hash: str, file_size: int, file_name: str) -> Optional[str]:
        """
        Check if file with matching hash/size/name exists in monitored directories
        
        Args:
            file_hash: SHA256 hash of file
            file_size: Size in bytes
            file_name: Filename
            
        Returns:
            Path to source file if found, None otherwise
        """
        if not file_hash:
            logger.warning("File hash is empty, cannot match")
            return None
        
        if not self.monitored_directories:
            logger.warning("No monitored directories configured")
            return None
        
        logger.info(f"Searching for file: {file_name} (size: {file_size}, hash: {file_hash[:16]}...)")
        
        # Search all monitored directories
        for monitored_dir in self.monitored_directories:
            try:
                logger.info(f"Searching in: {monitored_dir}")
                file_count = 0
                # Walk through directory tree
                for root, dirs, files in os.walk(monitored_dir):
                    # Skip if file name doesn't match (quick filter)
                    if file_name in files:
                        file_count += 1
                        candidate_path = os.path.join(root, file_name)
                        logger.info(f"Found candidate #{file_count}: {candidate_path}")
                        
                        # Check size first (faster than hash)
                        try:
                            candidate_size = os.path.getsize(candidate_path)
                            logger.info(f"Candidate size: {candidate_size}, Target size: {file_size}")
                            if candidate_size != file_size:
                                logger.info(f"Size mismatch: {candidate_size} != {file_size}, skipping")
                                continue
                        except Exception as e:
                            logger.warning(f"Error getting size for {candidate_path}: {e}")
                            continue
                        
                        # Check hash (slower but definitive)
                        logger.info(f"Calculating hash for: {candidate_path}")
                        candidate_hash = self._calculate_file_hash(candidate_path)
                        if not candidate_hash:
                            logger.warning(f"Failed to calculate hash for candidate: {candidate_path}")
                            continue
                        logger.info(f"Candidate hash: {candidate_hash[:16]}..., Target hash: {file_hash[:16]}...")
                        if candidate_hash == file_hash:
                            logger.warning(f"MATCH FOUND! Source: {candidate_path}")
                            return candidate_path
                        else:
                            logger.info(f"Hash mismatch, continuing search...")
                            
                if file_count == 0:
                    logger.info(f"No files named '{file_name}' found in {monitored_dir}")
                            
            except Exception as e:
                logger.error(f"Error searching {monitored_dir}: {e}", exc_info=True)
                continue
        
        logger.warning(f"No matching file found for: {file_name} after searching all monitored directories")
        return None

    def block_file_transfer(self, file_path: str) -> bool:
        """
        Block file transfer by deleting the file
        
        Args:
            file_path: Path to file on removable drive
            
        Returns:
            True if successfully blocked, False otherwise
        """
        try:
            # Try to delete the file
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.warning(f"Blocked file transfer by deleting: {file_path}")
                return True
            else:
                logger.warning(f"File already removed: {file_path}")
                return False
        except PermissionError:
            logger.error(f"Permission denied when blocking transfer: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to block transfer: {e}", exc_info=True)
            return False

    def _send_blocked_transfer_event(
        self,
        source_file: str,
        dest_file: str,
        file_hash: str,
        file_size: int,
        blocked: bool,
        policy: Optional[Dict[str, Any]] = None,
        action: str = "block",
    ):
        """
        Send event for blocked transfer
        
        Args:
            source_file: Path to source file in monitored directory
            dest_file: Path to destination file on removable drive
            file_hash: File hash
            file_size: File size
            blocked: Whether blocking was successful
        """
        try:
            # Read content for classification
            content = self._read_file_content(source_file, max_bytes=100000)
            classification = self._classify_content(content)
            
            # Determine severity (always critical for blocked transfers)
            severity = "critical" if blocked else "high"
            
            description = (
                f"File transfer blocked: {Path(source_file).name} -> {Path(dest_file).name}"
                if blocked else
                f"File transfer detected: {Path(source_file).name} -> {Path(dest_file).name}"
            )

            event_data = {
                "event_id": str(uuid.uuid4()),
                "event_type": "file",
                "event_subtype": "transfer_blocked" if blocked else "transfer_attempt",
                "agent_id": self.agent_id,
                "source_type": "agent",
                "user_email": f"{os.getlogin()}@{socket.gethostname()}",
                "description": description,
                "severity": severity,
                "action": "blocked" if blocked else "logged",
                "file_path": source_file,  # Source file path
                "file_name": Path(source_file).name,
                "file_size": file_size,
                "file_hash": file_hash,
                "classification": classification,
                "destination": dest_file,  # Destination on removable drive
                "source_path": source_file,
                "blocked": blocked,
                "destination_type": "removable_drive",
                "content": content[:5000] if content else None,
                "transfer_type": "usb_copy",
                "timestamp": datetime.utcnow().isoformat(),
                "policy_id": policy.get("id") if policy else None,
                "policy_name": policy.get("name") if policy else None,
                "policy_action": action,
            }

            if self.active_policy_version:
                event_data["policy_version"] = self.active_policy_version
            
            logger.info(
                f"Sending blocked transfer event: {Path(source_file).name} -> {Path(dest_file).name} "
                f"(Blocked: {blocked}, Severity: {severity})"
            )
            self.send_event(event_data)
            
        except Exception as e:
            logger.error(f"Error sending blocked transfer event: {e}", exc_info=True)

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
        except PermissionError:
            # Re-raise PermissionError so caller can handle retry logic
            raise
        except Exception as e:
            logger.debug(f"Error calculating hash for {file_path}: {e}")
            return ""

    def _read_file_content(self, file_path: str, max_bytes: int = 100000) -> str:
        """Read file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_bytes)
        except:
            return ""

    def _normalize_filesystem_path(self, path: str) -> str:
        """
        Normalize a path for filesystem access on Windows:
        - Expand env vars and user tokens
        - Replace forward slashes with backslashes
        """
        expanded = self._expand_path(path or "")
        return expanded.replace("/", "\\")

    def _normalize_compare_path(self, path: str) -> str:
        """
        Normalize a path for comparisons:
        - Expand env vars
        - Replace slashes
        - Collapse redundant segments
        - Lowercase for case-insensitive Windows comparisons
        """
        normalized = os.path.normpath(self._normalize_filesystem_path(path))
        return normalized.lower()

    def _is_path_prefix(self, candidate: str, prefix: str) -> bool:
        """
        Check whether prefix is a directory prefix of candidate.
        Both arguments must already be normalized and lowercased.
        """
        if candidate == prefix:
            return True
        return candidate.startswith(prefix + "\\")

    def _normalize_path_list(self, paths: List[str]) -> List[str]:
        """Normalize a list of paths for consistency in bundles."""
        return [self._normalize_filesystem_path(p) for p in paths if p]

    def _normalize_usb_transfer_policies(self, policies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize monitoredPaths inside USB transfer policies to avoid slash mismatches."""
        normalized = []
        for policy in policies:
            cfg = dict(policy.get("config", {}))
            cfg["monitoredPaths"] = self._normalize_path_list(cfg.get("monitoredPaths", []))
            normalized.append({**policy, "config": cfg})
        return normalized

    def _ensure_transfer_blocking_thread(self):
        """Start removable drive monitoring if enabled by config or policies."""
        if self.transfer_blocking_enabled and not self.transfer_blocking_thread_started:
            threading.Thread(target=self.monitor_removable_drives, daemon=True).start()
            self.transfer_blocking_thread_started = True
            logger.info("Removable drive monitoring thread started")

    def _reconcile_monitors(self):
        """Start or stop monitors based on current policy presence."""
        # File monitoring (covers file system and Google Drive local)
        if self.has_file_policies:
            if not self.observers:
                self.start_file_monitoring()
        else:
            if self.observers:
                self.stop_file_monitoring()

        # Clipboard monitoring and USB device monitoring are long-running threads; gating handled inside loops

        # Removable drive monitoring for USB transfer
        if self.has_usb_transfer_policies:
            self._ensure_transfer_blocking_thread()
        else:
            # Stop any removable-drive observers and clear state
            for drive, observer in list(self.removable_observers.items()):
                observer.stop()
                observer.join()
                self.removable_observers.pop(drive, None)
            self.removable_drives = set()

    def send_event(self, event_data: Dict[str, Any]):
        """Send event to server"""
        try:
            if not self.allow_events:
                logger.debug("Dropping event because no active policies")
                return
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
            if self.active_policy_version:
                data["policy_version"] = self.active_policy_version
            if self.last_policy_sync_status:
                data["policy_sync_status"] = self.last_policy_sync_status
            if self.last_policy_sync_at:
                data["policy_last_synced_at"] = self.last_policy_sync_at
            if self.last_policy_sync_error:
                data["policy_sync_error"] = self.last_policy_sync_error

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
