"""
File System Monitor
Monitors file operations (create, modify, delete, copy) in specified directories
"""

import asyncio
import structlog
from typing import Dict, Any, List, Callable
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = structlog.get_logger()


class DLPFileHandler(FileSystemEventHandler):
    """
    File system event handler for DLP monitoring
    """

    def __init__(
        self,
        on_event: Callable,
        extensions: List[str],
        max_file_size: int
    ):
        """
        Initialize handler

        Args:
            on_event: Async callback function
            extensions: List of extensions to monitor (e.g., ['.pdf', '.docx'])
            max_file_size: Maximum file size to read (bytes)
        """
        super().__init__()
        self.on_event = on_event
        self.extensions = [ext.lower() for ext in extensions]
        self.max_file_size = max_file_size

    def on_created(self, event: FileSystemEvent):
        """File created"""
        if not event.is_directory:
            asyncio.create_task(self._handle_event(event, "created"))

    def on_modified(self, event: FileSystemEvent):
        """File modified"""
        if not event.is_directory:
            asyncio.create_task(self._handle_event(event, "modified"))

    def on_deleted(self, event: FileSystemEvent):
        """File deleted"""
        if not event.is_directory:
            asyncio.create_task(self._handle_event(event, "deleted"))

    def on_moved(self, event: FileSystemEvent):
        """File moved/renamed"""
        if not event.is_directory:
            asyncio.create_task(self._handle_event(event, "moved"))

    async def _handle_event(self, event: FileSystemEvent, action: str):
        """
        Handle file system event

        Args:
            event: Watchdog file system event
            action: Action type (created, modified, deleted, moved)
        """
        try:
            file_path = Path(event.src_path)

            # Check extension
            if self.extensions and file_path.suffix.lower() not in self.extensions:
                return

            # Get file info
            file_info = {
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix
            }

            # Get file size if exists
            if file_path.exists():
                try:
                    file_size = file_path.stat().st_size
                    file_info["size"] = file_size
                except:
                    file_info["size"] = 0
            else:
                file_info["size"] = 0

            # Read file content if small enough
            content = None
            if action in ["created", "modified"] and file_path.exists():
                if file_info["size"] <= self.max_file_size:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        logger.debug(
                            "Could not read file content",
                            file=str(file_path),
                            error=str(e)
                        )

            # Call event callback
            await self.on_event(
                action=action,
                file_info=file_info,
                content=content
            )

        except Exception as e:
            logger.error(
                "Error handling file event",
                error=str(e),
                path=event.src_path
            )


class FileMonitor:
    """
    File system monitor using watchdog
    Works on Windows, Linux, and macOS
    """

    def __init__(
        self,
        agent,
        paths: List[str],
        extensions: List[str],
        max_file_size: int = 1048576  # 1MB
    ):
        """
        Initialize file monitor

        Args:
            agent: Parent agent instance
            paths: List of paths to monitor
            extensions: List of file extensions to monitor
            max_file_size: Maximum file size to read
        """
        self.agent = agent
        self.paths = [Path(p) for p in paths]
        self.extensions = extensions
        self.max_file_size = max_file_size

        self.observers = []
        self.running = False

        logger.info(
            "File monitor initialized",
            paths=len(self.paths),
            extensions=len(self.extensions)
        )

    async def on_file_event(
        self,
        action: str,
        file_info: Dict[str, Any],
        content: str = None
    ):
        """
        Handle file event

        Args:
            action: Action type (created, modified, deleted, moved)
            file_info: File information dict
            content: File content (if available)
        """
        # Determine severity
        severity = "low"
        if content and len(content) > 0:
            # Will be classified by server
            severity = "medium"

        # Create event
        event = self.agent.create_event(
            event_type="file",
            severity=severity,
            file=file_info,
            action={"type": action}
        )

        # Add content if available
        if content:
            event["content"] = content

        # Queue event
        await self.agent.queue_event(event)

        logger.debug(
            "File event detected",
            action=action,
            file=file_info.get("name"),
            has_content=content is not None
        )

    async def start(self):
        """
        Start monitoring file system
        """
        self.running = True

        logger.info("Starting file monitor")

        for path in self.paths:
            if not path.exists():
                logger.warning(
                    "Path does not exist, skipping",
                    path=str(path)
                )
                continue

            # Create event handler
            event_handler = DLPFileHandler(
                on_event=self.on_file_event,
                extensions=self.extensions,
                max_file_size=self.max_file_size
            )

            # Create observer
            observer = Observer()
            observer.schedule(
                event_handler,
                str(path),
                recursive=True
            )
            observer.start()

            self.observers.append(observer)

            logger.info(
                "Monitoring path",
                path=str(path)
            )

    async def stop(self):
        """
        Stop monitoring
        """
        self.running = False

        logger.info("Stopping file monitor")

        for observer in self.observers:
            observer.stop()
            observer.join()

        self.observers = []

        logger.info("File monitor stopped")
