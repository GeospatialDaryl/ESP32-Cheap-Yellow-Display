from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from loguru import logger

STATUS_COMMAND = b"\x10\x04\x01"
PAPER_SENSOR_COMMAND = b"\x10\x04\x04"


class PrinterDevice:
    """Wrapper around the raw /dev/usb/lpX character device."""

    def __init__(self, path: Path, max_retries: int = 3, retry_delay_s: float = 2.0):
        self.path = path
        self.max_retries = max_retries
        self.retry_delay_s = retry_delay_s

    def write(self, payload: bytes) -> None:
        attempt = 0
        while True:
            try:
                with self.path.open("wb", buffering=0) as handle:
                    logger.debug("Opened printer device", path=str(self.path), size=len(payload))
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                    logger.info("Successfully wrote payload", bytes=len(payload))
                break
            except OSError as exc:
                attempt += 1
                logger.error(
                    "Printer write failed",
                    attempt=attempt,
                    max_retries=self.max_retries,
                    error=str(exc),
                )
                if attempt > self.max_retries:
                    raise
                time.sleep(self.retry_delay_s)

    def query_status(self) -> Optional[int]:
        try:
            with self.path.open("wb", buffering=0) as handle:
                handle.write(STATUS_COMMAND)
                handle.flush()
                os.fsync(handle.fileno())
            with self.path.open("rb", buffering=0) as handle:
                response = handle.read(1)
                return response[0] if response else None
        except OSError as exc:
            logger.error("Failed to query printer status", error=str(exc))
            return None

    def query_paper(self) -> Optional[int]:
        try:
            with self.path.open("wb", buffering=0) as handle:
                handle.write(PAPER_SENSOR_COMMAND)
                handle.flush()
                os.fsync(handle.fileno())
            with self.path.open("rb", buffering=0) as handle:
                response = handle.read(1)
                return response[0] if response else None
        except OSError as exc:
            logger.error("Failed to query paper sensor", error=str(exc))
            return None

