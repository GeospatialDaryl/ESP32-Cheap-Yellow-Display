from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import barcode
import qrcode
from PIL import Image, ImageOps
from barcode.writer import ImageWriter
from loguru import logger

ESC = b"\x1b"
GS = b"\x1d"
LF = b"\n"


@dataclass
class TextStyle:
    align: str = "left"
    bold: bool = False
    underline: bool = False
    double_height: bool = False
    double_width: bool = False


def _align_command(align: str) -> bytes:
    align = align.lower()
    mapping = {"left": 0, "center": 1, "right": 2}
    value = mapping.get(align, 0)
    return ESC + b"a" + bytes([value])


def _bold_command(enabled: bool) -> bytes:
    return ESC + b"E" + (b"\x01" if enabled else b"\x00")


def _underline_command(enabled: bool) -> bytes:
    return ESC + b"-" + (b"\x02" if enabled else b"\x00")


def _double_size_command(width: bool, height: bool) -> bytes:
    value = (int(width) << 4) | int(height)
    return GS + b"!" + bytes([value])


def _line_spacing_command(dots: int) -> bytes:
    return ESC + b"3" + bytes([dots])


def render_job(job: Dict[str, Any], *, line_spacing: int, max_line_width: int) -> bytes:
    logger.debug("Rendering job", version=job.get("version"))
    chunks: List[bytes] = [ESC + b"@", _line_spacing_command(line_spacing)]

    for entry in job.get("content", []):
        entry_type = entry.get("type")
        if entry_type == "text":
            chunks.append(render_text(entry, max_line_width))
        elif entry_type == "feed":
            chunks.append(render_feed(entry))
        elif entry_type == "raw":
            data = entry.get("data", "")
            payload = base64.b64decode(data) if entry.get("encoding") == "base64" else data.encode("latin-1")
            chunks.append(payload)
        elif entry_type == "barcode":
            chunks.append(render_barcode(entry, max_line_width))
        elif entry_type == "qrcode":
            chunks.append(render_qrcode(entry, max_line_width))
        elif entry_type == "image":
            chunks.append(render_image(entry, max_line_width))
        else:
            logger.warning("Unknown job entry", entry=entry)
    chunks.append(ESC + b"@")
    return b"".join(chunks)


def render_text(entry: Dict[str, Any], max_line_width: int) -> bytes:
    style = entry.get("style", {})
    text = entry.get("text", "")
    ts = TextStyle(
        align=style.get("align", "left"),
        bold=bool(style.get("bold", False)),
        underline=bool(style.get("underline", False)),
        double_height=bool(style.get("double_height", False)),
        double_width=bool(style.get("double_width", False)),
    )

    commands = [
        _align_command(ts.align),
        _bold_command(ts.bold),
        _underline_command(ts.underline),
        _double_size_command(ts.double_width, ts.double_height),
    ]

    wrapped_text = _wrap_text(text, ts, max_line_width)
    commands.append(wrapped_text.encode("utf-8") + LF)

    commands.append(_double_size_command(False, False))
    commands.append(_bold_command(False))
    commands.append(_underline_command(False))
    commands.append(_align_command("left"))
    return b"".join(commands)


def _wrap_text(text: str, style: TextStyle, max_line_width: int) -> str:
    columns = max_line_width // (16 if style.double_width else 8)
    if columns <= 0:
        columns = 32
    lines: List[str] = []
    for paragraph in text.splitlines() or [""]:
        current = ""
        for word in paragraph.split(" "):
            if not current:
                current = word
                continue
            if len(current) + 1 + len(word) > columns:
                lines.append(current)
                current = word
            else:
                current += " " + word
        lines.append(current)
    return "\n".join(lines)


def render_feed(entry: Dict[str, Any]) -> bytes:
    lines = int(entry.get("lines", 1))
    return LF * max(lines, 0)


def render_image(entry: Dict[str, Any], max_width: int) -> bytes:
    if "path" in entry:
        image_path = Path(entry["path"]).expanduser()
        if image_path.as_posix().startswith("data:"):
            image = Image.open(io.BytesIO(_data_uri_to_bytes(entry["path"])))
        else:
            image = Image.open(image_path)
    elif "data" in entry:
        image = Image.open(io.BytesIO(base64.b64decode(entry["data"])))
    else:
        raise ValueError("Image entry must include 'path' or 'data'")

    align = entry.get("align", "left")
    dither = bool(entry.get("dither", True))
    raster = _image_to_raster(image, max_width, dither)
    header = GS + b"v0" + b"\x00"
    width_bytes = len(raster[0]) if raster else 0
    width_lsb = width_bytes & 0xFF
    width_msb = (width_bytes >> 8) & 0xFF
    height = len(raster)
    height_lsb = height & 0xFF
    height_msb = (height >> 8) & 0xFF

    align_cmd = _align_command(align)
    payload = bytearray()
    payload.extend(align_cmd)
    payload.extend(header)
    payload.extend(bytes([width_lsb, width_msb, height_lsb, height_msb]))
    for row in raster:
        payload.extend(row)
    payload.extend(LF)
    payload.extend(_align_command("left"))
    return bytes(payload)


def _data_uri_to_bytes(uri: str) -> bytes:
    header, data = uri.split(",", 1)
    if ";base64" in header:
        return base64.b64decode(data)
    return data.encode("latin-1")


def _image_to_raster(image: Image.Image, max_width: int, dither: bool) -> List[bytes]:
    image = image.convert("L")
    width = min(max_width, image.width)
    if image.width != width:
        ratio = width / image.width
        new_height = max(1, int(image.height * ratio))
        image = image.resize((width, new_height), Image.LANCZOS)
    if dither:
        image = image.convert("1")
    else:
        image = ImageOps.autocontrast(image)
        image = image.point(lambda x: 0 if x < 128 else 255, mode="1")

    padded_width = ((image.width + 7) // 8) * 8
    if padded_width != image.width:
        padded = Image.new("1", (padded_width, image.height), color=255)
        padded.paste(image, (0, 0))
        image = padded

    pixels = image.load()
    rows: List[bytes] = []
    for y in range(image.height):
        row = bytearray()
        for x in range(0, image.width, 8):
            byte = 0
            for bit in range(8):
                pixel = pixels[x + bit, y]
                if pixel == 0:
                    byte |= 1 << (7 - bit)
            row.append(byte)
        rows.append(bytes(row))
    return rows


def render_barcode(entry: Dict[str, Any], max_width: int) -> bytes:
    symbology = entry.get("symbology", "CODE128").upper()
    data = entry.get("data", "")
    module_height = int(entry.get("height", 60))
    align = entry.get("align", "center")

    barcode_cls = barcode.get_barcode_class(symbology)
    barcode_image = barcode_cls(data, writer=ImageWriter()).render(writer_options={
        "module_height": module_height,
        "quiet_zone": 2,
    })
    encoded = base64.b64encode(_image_to_png(barcode_image)).decode("ascii")
    return render_image({"align": align, "data": encoded}, max_width)


def render_qrcode(entry: Dict[str, Any], max_width: int) -> bytes:
    data = entry.get("data", "")
    size = int(entry.get("size", 8))
    border = int(entry.get("border", 4))
    align = entry.get("align", "center")

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=size, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    encoded = base64.b64encode(_image_to_png(image)).decode("ascii")
    return render_image({"align": align, "data": encoded}, max_width)


def _image_to_png(image: Image.Image) -> bytes:
    pil_image = image.get_image() if hasattr(image, "get_image") else image
    if not isinstance(pil_image, Image.Image):
        raise TypeError("Object is not a PIL image")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()

