from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml
from loguru import logger


@dataclass(frozen=True)
class Config:
    spool_path: Path
    state_path: Path
    log_path: Path
    printer_device: Path
    max_retries: int = 3
    retry_delay_s: float = 2.0
    line_spacing: int = 8
    max_line_width: int = 384
    locale: str = "en_US.UTF-8"

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "Config":
        def _path(key: str, default: str | None = None) -> Path:
            value = data.get(key, default)
            if value is None:
                raise KeyError(f"Missing required configuration key: {key}")
            return Path(os.path.expanduser(str(value))).resolve()

        return cls(
            spool_path=_path("spool_path"),
            state_path=_path("state_path"),
            log_path=_path("log_path"),
            printer_device=_path("printer_device"),
            max_retries=int(data.get("max_retries", 3)),
            retry_delay_s=float(data.get("retry_delay_s", 2.0)),
            line_spacing=int(data.get("line_spacing", 8)),
            max_line_width=int(data.get("max_line_width", 384)),
            locale=str(data.get("locale", "en_US.UTF-8")),
        )


def load_config(path: str | os.PathLike[str]) -> Config:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return Config.from_mapping(data)


def ensure_directories(config: Config) -> None:
    for directory in (config.spool_path, config.state_path, config.log_path):
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured directory exists", path=str(directory))


def atomic_write(path: Path, payload: bytes, suffix: str = ".tmp") -> None:
    tmp_path = path.with_suffix(path.suffix + suffix)
    with tmp_path.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    tmp_path.replace(path)


def read_job(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_job(path: Path, job: Dict[str, Any]) -> None:
    payload = json.dumps(job, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    atomic_write(path, payload)


def reserve_processing_lock(spool_path: Path, job_path: Path) -> Path:
    lock_path = spool_path / f".{job_path.name}.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise FileExistsError(f"Job {job_path.name} is already locked") from exc
    os.close(fd)
    return lock_path


def release_processing_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def iter_job_files(spool_path: Path):
    for path in sorted(spool_path.glob("*.job")):
        if path.is_file():
            yield path

