"""File system watcher for Scholarr."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches file system for changes."""

    def __init__(self):
        self.running = False
        self.watched_paths = []

    async def start(self):
        """Start watching the file system."""
        self.running = True
        logger.info("File watcher started")

    async def stop(self):
        """Stop watching the file system."""
        self.running = False
        logger.info("File watcher stopped")

    async def add_watched_path(self, path: str):
        """Add a path to watch."""
        if path not in self.watched_paths:
            self.watched_paths.append(path)
            logger.info(f"Added watched path: {path}")


# Global file watcher instance
file_watcher = FileWatcher()
