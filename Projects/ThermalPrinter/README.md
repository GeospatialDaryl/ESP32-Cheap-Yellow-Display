# MPU-L465 Thermal Printer System Design

This project provides a complete, modular printing stack tailored for the MPU-L465 58/80 mm thermal printer connected to an Ubuntu 24.04 "Noble" system via `/dev/usb/lp1`.  The solution is designed for unattended deployments such as kiosks or embedded controllers where deterministic, low-maintenance operation is required.

## Overview

The system is composed of the following layers:

| Layer | Component | Purpose |
|-------|-----------|---------|
| Job submission | `tp-submit` CLI | Accepts UTF-8 text, markdown, raw ESC/POS, or images and produces normalized job files inside the spool directory. |
| Spool | `tp-spoold` daemon | Watches the spool directory, performs validation, and dispatches jobs to the renderer. |
| Rendering | `renderer` module | Converts normalized job definitions to ESC/POS byte streams suitable for the MPU-L465. |
| Device access | `device` module | Streams ESC/POS bytes to `/dev/usb/lp1` with retry, pacing, and error logging. |
| Monitoring | systemd + journald | Provides service supervision and structured logs for post-mortem analysis. |

The design avoids heavyweight print subsystems (CUPS) while retaining isolation between job submission and the physical device.

## Directory Structure

```
Projects/ThermalPrinter/
├── README.md                 # This document
├── config.example.yaml       # Editable runtime configuration
├── src/
│   ├── __init__.py
│   ├── cli.py                # Entrypoint for both tp-submit and tp-spoold
│   ├── device.py             # Safe access to /dev/usb/lp1
│   ├── renderer.py           # High-level to ESC/POS conversion
│   ├── spooler.py            # Job queue logic
│   └── utils.py              # Shared helpers
├── systemd/
│   └── tp-spoold.service     # Sample systemd unit
└── spool/                    # Default spool directory (jobs in JSON)
```

Only the `spool/` directory must be writable by the service account.  The device file `/dev/usb/lp1` requires membership in the `lp` group or an explicit `udev` rule.

## Configuration

Copy `config.example.yaml` to `config.yaml` and adjust as needed.

```yaml
spool_path: /var/spool/tprinter
state_path: /var/lib/tprinter
log_path: /var/log/tprinter
printer_device: /dev/usb/lp1
max_retries: 3
retry_delay_s: 2.0
line_spacing: 8          # dots
max_line_width: 384      # dots (48 columns @ 8 dots)
locale: en_US.UTF-8
```

* `spool_path` — Directory containing job files.  Jobs are JSON files with a `.job` suffix.
* `state_path` — Persistent storage for the monotonic job ID counter and crash recovery metadata.
* `log_path` — Directory for rotated debug logs when not running under systemd/journald.
* `line_spacing` & `max_line_width` — Rendering defaults tuned for standard 58 mm paper.  Set `max_line_width` to 576 for 80 mm paper.

A helper CLI `tp-setup` (future work) could create directories, set permissions, and install the systemd unit.  For now follow the manual steps in [Deployment](#deployment).

## Job Model

A job is a UTF-8 JSON document, written atomically to the spool directory.  Example:

```json
{
  "version": 1,
  "content": [
    {"type": "text", "text": "Thermal Printer Test", "style": {"align": "center", "bold": true, "double_height": true}},
    {"type": "barcode", "symbology": "CODE128", "data": "ABC-123"},
    {"type": "qrcode", "data": "https://example.com"},
    {"type": "image", "path": "/home/user/logo.png", "align": "center"},
    {"type": "feed", "lines": 4}
  ]
}
```

The spooler validates each entry and resolves relative paths against the job file's directory.  The renderer handles text shaping, barcode encoding, dithering (Floyd–Steinberg) for images, and automatic pagination.

## Deployment

1. **Create runtime directories** (example uses service user `tprinter`):
   ```bash
   sudo useradd --system --home /var/lib/tprinter --shell /usr/sbin/nologin tprinter
   sudo install -d -o tprinter -g tprinter /var/spool/tprinter /var/lib/tprinter /var/log/tprinter
   sudo usermod -aG lp tprinter
   ```

2. **Copy configuration**:
   ```bash
   sudo install -o tprinter -g tprinter Projects/ThermalPrinter/config.example.yaml /etc/tprinter/config.yaml
   ```

3. **Install Python environment** (Python 3.12 recommended):
   ```bash
   python3 -m venv /opt/tprinter
   /opt/tprinter/bin/pip install --requirement Projects/ThermalPrinter/requirements.txt
   ```

4. **Install CLI wrappers and library**:
   ```bash
   sudo install -m 755 Projects/ThermalPrinter/bin/tp-submit /opt/tprinter/bin/tp-submit
   sudo install -m 755 Projects/ThermalPrinter/bin/tp-spoold /opt/tprinter/bin/tp-spoold
   sudo rsync -a Projects /opt/tprinter/lib
   ```

5. **Install systemd service**:
   ```bash
   sudo install -m 644 Projects/ThermalPrinter/systemd/tp-spoold.service /etc/systemd/system/tp-spoold.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now tp-spoold.service
   ```

6. **Submit a test job**:
   ```bash
   /opt/tprinter/bin/tp-submit text "Hello thermal world!"
   ```

## Operational Considerations

* **Crash safety** — Jobs are processed using atomic rename to avoid partial reads.  The spooler maintains a lock file during processing and requeues jobs upon recoverable errors.
* **Logging & metrics** — JSON structured logs with monotonic job IDs allow ingestion by Loki/Elastic.  Hooks for Prometheus textfile exporter can be added in `spooler.py`.
* **Printer health** — The `device` module exposes temperature and paper status queries via ESC/POS real-time status commands.  The spooler surfaces them in the logs, enabling proactive maintenance.
* **Extensibility** — Additional job types (tables, receipts, localized formats) can be added by extending the renderer without modifying job submission or device access layers.

## Future Enhancements

* HTTP REST API wrapping `tp-submit` for remote job ingestion.
* Integration with MQTT for IoT workflows.
* Web dashboard for job history and printer telemetry.

