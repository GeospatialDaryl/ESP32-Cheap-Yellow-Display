from __future__ import annotations

import json
import signal
import time
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from . import renderer
from .device import PrinterDevice
from .utils import (
    Config,
    iter_job_files,
    read_job,
    release_processing_lock,
    reserve_processing_lock,
    write_job,
)


class Spooler:
    def __init__(self, config: Config, device: Optional[PrinterDevice] = None):
        self.config = config
        self.device = device or PrinterDevice(
            config.printer_device, config.max_retries, config.retry_delay_s
        )
        self._should_run = True

    def run(self) -> None:
        logger.info("Starting spooler", spool=str(self.config.spool_path))
        signal.signal(signal.SIGTERM, self._handle_stop)
        signal.signal(signal.SIGINT, self._handle_stop)
        while self._should_run:
            processed = False
            for job_path in iter_job_files(self.config.spool_path):
                processed = True
                try:
                    self._process_job(job_path)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.exception("Failed to process job", job=job_path.name, error=str(exc))
            if not processed:
                time.sleep(0.5)
        logger.info("Spooler stopped")

    def _handle_stop(self, signum, _frame) -> None:  # type: ignore[override]
        logger.info("Received stop signal", signal=signum)
        self._should_run = False

    def _process_job(self, job_path: Path) -> None:
        lock_path = reserve_processing_lock(self.config.spool_path, job_path)
        logger.info("Processing job", job=job_path.name)
        try:
            job = read_job(job_path)
            payload = renderer.render_job(
                job,
                line_spacing=self.config.line_spacing,
                max_line_width=self.config.max_line_width,
            )
            self.device.write(payload)
            done_path = job_path.with_suffix(".done")
            job_path.rename(done_path)
            logger.info("Completed job", job=job_path.name, bytes=len(payload))
        except Exception:
            failed_path = job_path.with_suffix(".error")
            job_path.rename(failed_path)
            logger.error("Job moved to error state", job=job_path.name)
            raise
        finally:
            release_processing_lock(lock_path)


def build_job_from_text(text: str, **style) -> Dict:
    return {
        "version": 1,
        "content": [
            {"type": "text", "text": text, "style": style},
            {"type": "feed", "lines": 4},
        ],
    }


def build_job_from_markdown(markdown_text: str) -> Dict:
    lines = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if line.startswith("###"):
            lines.append({"type": "text", "text": line[3:].strip(), "style": {"bold": True}})
        elif line.startswith("##"):
            lines.append({"type": "text", "text": line[2:].strip(), "style": {"bold": True, "double_height": True}})
        elif line.startswith("#"):
            lines.append({"type": "text", "text": line[1:].strip(), "style": {"align": "center", "bold": True}})
        elif line == "":
            lines.append({"type": "feed", "lines": 1})
        else:
            lines.append({"type": "text", "text": line})
    lines.append({"type": "feed", "lines": 4})
    return {"version": 1, "content": lines}


def build_job_from_file(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_job_to_spool(job: Dict, spool_path: Path, prefix: str = "job") -> Path:
    spool_path.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time() * 1000)
    job_path = spool_path / f"{prefix}-{timestamp}.job"
    write_job(job_path, job)
    logger.info("Queued job", path=str(job_path))
    return job_path

