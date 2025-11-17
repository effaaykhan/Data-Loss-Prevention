"""
Base Agent Class
Provides common functionality for all DLP agents (Windows/Linux)
"""

import asyncio
import yaml
import uuid
import structlog
import aiohttp
import socket
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Base class for DLP agents

    Handles:
    - Configuration loading
    - Server communication
    - Auto-enrollment
    - Event queue management
    - Heartbeat
    - Retry logic
    """

    def __init__(self, config_path: str = None):
        """
        Initialize agent

        Args:
            config_path: Path to agent.yml configuration file
        """
        # Default config paths
        if config_path is None:
            if platform.system() == "Windows":
                config_path = "C:/ProgramData/CyberSentinel/agent.yml"
            else:
                config_path = "/etc/cybersentinel/agent.yml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Agent identity
        self.agent_id = self.config.get("agent", {}).get("id", "")
        self.agent_name = self.config.get("agent", {}).get("name", socket.gethostname())
        self.registration_key = self.config.get("agent", {}).get("registration_key", "")
        self.access_token = ""

        # Manager connection
        self.manager_url = self.config.get("agent", {}).get("manager_url", "https://localhost:55000")

        # Cached policies fetched from manager
        self.policies: List[Dict[str, Any]] = []

        # Event queue
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)

        # Running state
        self.running = False

        # Monitors (to be set by subclass)
        self.monitors = []

        logger.info(
            "Agent initialized",
            agent_name=self.agent_name,
            manager_url=self.manager_url,
            platform=platform.system()
        )

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            logger.warning(
                "Config file not found, using defaults",
                config_path=str(self.config_path)
            )
            return self._default_config()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(
                    "Configuration loaded",
                    config_path=str(self.config_path)
                )
                return config
        except Exception as e:
            logger.error(
                "Failed to load config",
                config_path=str(self.config_path),
                error=str(e)
            )
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """
        Return default configuration
        """
        return {
            "agent": {
                "id": "",
                "name": socket.gethostname(),
                "manager_url": "https://localhost:55000",
                "registration_key": "",
                "heartbeat_interval": 60
            },
            "monitoring": {
                "file_system": {
                    "enabled": True,
                    "paths": [],
                    "extensions": [".pdf", ".docx", ".xlsx", ".txt"]
                },
                "clipboard": {
                    "enabled": True
                },
                "usb": {
                    "enabled": True
                },
                "network": {
                    "enabled": False
                }
            },
            "performance": {
                "max_events_per_minute": 100,
                "max_event_size": 1048576,
                "batch_size": 10
            }
        }

    def _save_config(self):
        """
        Save current configuration to file
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)

            logger.info(
                "Configuration saved",
                config_path=str(self.config_path)
            )
        except Exception as e:
            logger.error(
                "Failed to save config",
                config_path=str(self.config_path),
                error=str(e)
            )

    async def register(self) -> bool:
        """
        Register agent with manager (auto-enrollment)

        Returns:
            True if registration successful
        """
        if self.agent_id and self.registration_key:
            logger.info("Agent already registered", agent_id=self.agent_id)
            return True

        try:
            logger.info("Registering agent with manager", manager_url=self.manager_url)

            async with aiohttp.ClientSession() as session:
                payload = {
                    "name": self.agent_name,
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "ip_address": self._get_local_ip(),
                    "hostname": socket.gethostname()
                }

                async with session.post(
                    f"{self.manager_url}/api/v1/agents/register",
                    json=payload,
                    ssl=False  # TODO: Proper SSL verification
                ) as response:
                    if response.status == 201:
                        data = await response.json()

                        self.agent_id = data.get("agent_id")
                        self.registration_key = data.get("registration_key")

                        # Save to config
                        self.config["agent"]["id"] = self.agent_id
                        self.config["agent"]["registration_key"] = self.registration_key
                        self._save_config()

                        logger.info(
                            "Agent registered successfully",
                            agent_id=self.agent_id
                        )
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            "Registration failed",
                            status=response.status,
                            error=error_text
                        )
                        return False

        except Exception as e:
            logger.error("Registration exception", error=str(e))
            return False

    async def authenticate(self) -> bool:
        """
        Authenticate with manager using registration key

        Returns:
            True if authentication successful
        """
        if not self.agent_id or not self.registration_key:
            logger.error("Cannot authenticate: missing agent_id or registration_key")
            return False

        try:
            logger.info("Authenticating with manager", agent_id=self.agent_id)

            async with aiohttp.ClientSession() as session:
                payload = {
                    "agent_id": self.agent_id,
                    "registration_key": self.registration_key
                }

                async with session.post(
                    f"{self.manager_url}/api/v1/agents/auth",
                    json=payload,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get("access_token")

                        logger.info(
                            "Authentication successful",
                            agent_id=self.agent_id
                        )
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(
                            "Authentication failed",
                            status=response.status,
                            error=error_text
                        )
                        return False

        except Exception as e:
            logger.error("Authentication exception", error=str(e))
            return False

    async def send_heartbeat(self):
        """
        Send heartbeat to manager
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "ip_address": self._get_local_ip(),
                    "hostname": socket.gethostname(),
                    "status": "active"
                }

                headers = {}
                if self.access_token:
                    headers["Authorization"] = f"Bearer {self.access_token}"

                async with session.post(
                    f"{self.manager_url}/api/v1/agents/{self.agent_id}/heartbeat",
                    json=payload,
                    headers=headers,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        logger.debug("Heartbeat sent successfully")
                    else:
                        logger.warning(
                            "Heartbeat failed",
                            status=response.status
                        )

        except Exception as e:
            logger.error("Heartbeat exception", error=str(e))

    async def heartbeat_loop(self):
        """
        Periodic heartbeat loop
        """
        interval = self.config.get("agent", {}).get("heartbeat_interval", 60)

        while self.running:
            await self.send_heartbeat()
            await asyncio.sleep(interval)

    async def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send single event to manager

        Args:
            event: Event dictionary

        Returns:
            True if sent successfully
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.access_token:
                    headers["Authorization"] = f"Bearer {self.access_token}"

                async with session.post(
                    f"{self.manager_url}/api/v1/events",
                    json=event,
                    headers=headers,
                    ssl=False
                ) as response:
                    if response.status == 201:
                        logger.debug(
                            "Event sent successfully",
                            event_id=event.get("event_id")
                        )
                        return True
                    else:
                        logger.error(
                            "Failed to send event",
                            status=response.status,
                            event_id=event.get("event_id")
                        )
                        return False

        except Exception as e:
            logger.error(
                "Event send exception",
                error=str(e),
                event_id=event.get("event_id")
            )
            return False

    async def send_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Send multiple events in batch

        Args:
            events: List of event dictionaries

        Returns:
            Number of successfully sent events
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.access_token:
                    headers["Authorization"] = f"Bearer {self.access_token}"

                payload = {"events": events}

                async with session.post(
                    f"{self.manager_url}/api/v1/events/batch",
                    json=payload,
                    headers=headers,
                    ssl=False
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        indexed = data.get("indexed", 0)
                        logger.info(
                            "Batch sent successfully",
                            total=len(events),
                            indexed=indexed
                        )
                        return indexed
                    else:
                        logger.error(
                            "Failed to send batch",
                            status=response.status
                        )
                        return 0

        except Exception as e:
            logger.error("Batch send exception", error=str(e))
            return 0

    async def event_processor_loop(self):
        """
        Process events from queue and send to manager
        """
        batch_size = self.config.get("performance", {}).get("batch_size", 10)
        batch = []

        while self.running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=5.0
                )

                batch.append(event)

                # Send batch when full or queue is empty
                if len(batch) >= batch_size or self.event_queue.empty():
                    if len(batch) == 1:
                        await self.send_event(batch[0])
                    else:
                        await self.send_events_batch(batch)

                    batch = []

            except asyncio.TimeoutError:
                # Send pending batch if any
                if batch:
                    if len(batch) == 1:
                        await self.send_event(batch[0])
                    else:
                        await self.send_events_batch(batch)
                    batch = []

            except Exception as e:
                logger.error("Event processor exception", error=str(e))

    def _get_local_ip(self) -> str:
        """
        Get local IP address
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def create_event(
        self,
        event_type: str,
        severity: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create event dictionary

        Args:
            event_type: Event type (file, clipboard, usb, network)
            severity: Severity (low, medium, high, critical)
            **kwargs: Additional event fields

        Returns:
            Event dictionary
        """
        event = {
            "event_id": f"evt-{uuid.uuid4()}",
            "@timestamp": datetime.utcnow().isoformat(),
            "agent": {
                "id": self.agent_id,
                "name": self.agent_name,
                "ip": self._get_local_ip(),
                "os": platform.system()
            },
            "event": {
                "type": event_type,
                "severity": severity,
                "outcome": "success",
                "action": "logged"
            }
        }

        # Add additional fields
        event.update(kwargs)

        return event

    async def queue_event(self, event: Dict[str, Any]):
        """
        Add event to processing queue

        Args:
            event: Event dictionary
        """
        try:
            await self.event_queue.put(event)
            logger.debug(
                "Event queued",
                event_id=event.get("event_id"),
                queue_size=self.event_queue.qsize()
            )
        except asyncio.QueueFull:
            logger.error("Event queue full, dropping event")

    @abstractmethod
    async def initialize_monitors(self):
        """
        Initialize platform-specific monitors
        Must be implemented by subclass
        """
        pass

    @abstractmethod
    async def cleanup_monitors(self):
        """
        Clean up platform-specific monitors
        Must be implemented by subclass
        """
        pass

    async def start(self):
        """
        Start agent
        """
        logger.info("Starting CyberSentinel DLP Agent", version="2.0.0")

        # Register if not already registered
        if not self.agent_id:
            if not await self.register():
                logger.error("Registration failed, cannot start agent")
                return

        # Authenticate
        if not await self.authenticate():
            logger.error("Authentication failed, cannot start agent")
            return

        # Set running flag
        self.running = True

        # Fetch active policies from manager for local use
        await self.refresh_policies()

        # Initialize monitors
        await self.initialize_monitors()

        # Start background tasks
        tasks = [
            asyncio.create_task(self.heartbeat_loop()),
            asyncio.create_task(self.event_processor_loop()),
            asyncio.create_task(self.policy_refresh_loop()),
        ]

        # Start monitors
        for monitor in self.monitors:
            tasks.append(asyncio.create_task(monitor.start()))

        logger.info(
            "Agent started successfully",
            agent_id=self.agent_id,
            monitors=len(self.monitors)
        )

        # Wait for tasks
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.stop()

    async def stop(self):
        """
        Stop agent
        """
        logger.info("Stopping agent")

        self.running = False

        # Stop monitors
        await self.cleanup_monitors()

        logger.info("Agent stopped")

    async def refresh_policies(self):
        """
        Fetch active policies from the manager and cache them locally.

        Agents use these policies to adjust local monitoring behaviour
        (e.g., which file types to watch, keywords of interest, etc.).
        """
        if not self.access_token:
            logger.warning("Cannot refresh policies without access token")
            return

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with session.get(
                    f"{self.manager_url}/api/v1/policies",
                    params={"enabled_only": "true"},
                    headers=headers,
                    ssl=False,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Policies API returns a list of policy objects
                        self.policies = data
                        logger.info(
                            "Policies refreshed",
                            count=len(self.policies),
                        )
                    else:
                        text = await response.text()
                        logger.warning(
                            "Failed to refresh policies",
                            status=response.status,
                            error=text,
                        )
        except Exception as e:
            logger.error("Policy refresh exception", error=str(e))

    async def policy_refresh_loop(self):
        """
        Periodically refresh policies from the manager.
        """
        # Default to 5 minutes if not specified
        interval = (
            self.config.get("agent", {}).get("policy_refresh_interval", 300)
        )

        while self.running:
            await self.refresh_policies()
            await asyncio.sleep(interval)
