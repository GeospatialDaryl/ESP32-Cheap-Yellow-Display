from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Optional

import typer
from loguru import logger

from .device import PrinterDevice
from .spooler import (
    Spooler,
    build_job_from_file,
    build_job_from_markdown,
    build_job_from_text,
    write_job_to_spool,
)
from .utils import Config, ensure_directories, load_config

DEFAULT_CONFIG = Path("/etc/tprinter/config.yaml")

app = typer.Typer(help="MPU-L465 thermal printer toolkit")
submit_app = typer.Typer(help="Submit print jobs")
app.add_typer(submit_app, name="submit")


def _load_config(config_path: Optional[Path]) -> Config:
    path = config_path or DEFAULT_CONFIG
    config = load_config(path)
    ensure_directories(config)
    logger.info("Loaded configuration", path=str(path))
    return config


@app.command()
def spoold(
    config_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False, readable=True, help="Path to configuration YAML"),
) -> None:
    """Run the spooler daemon."""

    config = _load_config(config_path)
    device = PrinterDevice(config.printer_device, config.max_retries, config.retry_delay_s)
    Spooler(config, device).run()


@submit_app.command("text")
def submit_text(
    text: str = typer.Argument(..., help="Text to print"),
    align: str = typer.Option("left", help="Alignment: left/center/right"),
    bold: bool = typer.Option(False, help="Enable bold"),
    double_width: bool = typer.Option(False, help="Double width"),
    double_height: bool = typer.Option(False, help="Double height"),
    config_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False, readable=True),
) -> None:
    config = _load_config(config_path)
    job = build_job_from_text(text, align=align, bold=bold, double_width=double_width, double_height=double_height)
    write_job_to_spool(job, config.spool_path)


@submit_app.command("markdown")
def submit_markdown(
    source: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
    config_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False, readable=True),
) -> None:
    config = _load_config(config_path)
    text = source.read_text(encoding="utf-8")
    job = build_job_from_markdown(text)
    write_job_to_spool(job, config.spool_path)


@submit_app.command("job")
def submit_job_file(
    job_file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
    config_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False, readable=True),
) -> None:
    config = _load_config(config_path)
    job = build_job_from_file(job_file)
    write_job_to_spool(job, config.spool_path)


@submit_app.command("raw")
def submit_raw(
    binary_file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
    config_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False, readable=True),
) -> None:
    config = _load_config(config_path)
    data = binary_file.read_bytes()
    job = {
        "version": 1,
        "content": [
            {"type": "raw", "data": base64.b64encode(data).decode("ascii"), "encoding": "base64"},
        ],
    }
    write_job_to_spool(job, config.spool_path)


@submit_app.command("image")
def submit_image(
    image_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
    align: str = typer.Option("center"),
    dither: bool = typer.Option(True),
    config_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False, readable=True),
) -> None:
    config = _load_config(config_path)
    job = {
        "version": 1,
        "content": [
            {"type": "image", "path": str(image_path), "align": align, "dither": dither},
            {"type": "feed", "lines": 4},
        ],
    }
    write_job_to_spool(job, config.spool_path)


@submit_app.command("qrcode")
def submit_qrcode(
    data: str = typer.Argument(..., help="QR code data"),
    size: int = typer.Option(8, help="Box size"),
    border: int = typer.Option(4, help="Border modules"),
    config_path: Optional[Path] = typer.Option(None, exists=True, file_okay=True, dir_okay=False, readable=True),
) -> None:
    config = _load_config(config_path)
    job = {
        "version": 1,
        "content": [
            {"type": "qrcode", "data": data, "size": size, "border": border, "align": "center"},
            {"type": "feed", "lines": 4},
        ],
    }
    write_job_to_spool(job, config.spool_path)


@app.command()
def sample_job(
    output: Path = typer.Argument(..., file_okay=True, dir_okay=False),
) -> None:
    """Generate a sample job JSON."""

    job = {
        "version": 1,
        "content": [
            {"type": "text", "text": "Thermal Printer Test", "style": {"align": "center", "bold": True, "double_height": True}},
            {"type": "text", "text": "MPU-L465 Ubuntu Noble"},
            {"type": "feed", "lines": 2},
            {"type": "qrcode", "data": "https://example.com", "align": "center"},
            {"type": "feed", "lines": 4},
        ],
    }
    output.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"Sample job written to {output}")


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()

