# Using the UM960 with an Atomic Pi Host

This guide covers how to drive the UM960 / Cheap Yellow Display directly from an Atomic Pi x86 single-board computer (SBC). The Atomic Pi runs a standard Linux distribution, so the display is treated like a USB/peripheral accessory instead of flashing firmware directly to the ESP32 microcontroller on the UM960 board.

## Hardware overview

* **UM960 (Sunton ESP32-2432S028R family)** – ESP32-based module with 2.8" ILI9341 display, resistive touch panel, CH340 USB-to-UART bridge, RGB LED, light sensor, microSD card slot, and available GPIOs.
* **Atomic Pi** – Intel Atom-based SBC with USB host ports, exposed GPIO header, and support for 5 V power outputs. The board typically runs Ubuntu or Debian derivatives.

Because the Atomic Pi is the host system, the ESP32 on the UM960 can be accessed over USB (UART) for firmware upload or as a serial peripheral. The Atomic Pi can also interact with the UM960’s GPIOs through level shifters if required.

## Connection checklist

1. **Power**
   * Supply the UM960 via its USB-C connector using a USB-A-to-C cable from the Atomic Pi’s powered USB host port.
   * Alternatively, feed 5 V directly to the UM960’s `5V` pin and `GND` from the Atomic Pi’s expansion header if you prefer a fixed wiring harness.
2. **Data**
   * The CH340 USB-to-UART bridge enumerates on the Atomic Pi as `/dev/ttyUSB*`. Confirm detection with `dmesg | grep ttyUSB` after plugging the UM960 in.
   * For touchscreen SPI access or additional GPIO, use the UM960 header pins. Add a bi-directional level shifter when connecting to the Atomic Pi’s 3.3 V/5 V tolerant GPIOs to maintain signal integrity.
3. **Optional accessories**
   * Route the UM960’s microSD card slot to the Atomic Pi using an SPI breakout if you need direct file access from Linux.
   * Use the onboard light sensor and RGB LED via ESPHome or custom firmware flashed to the ESP32, exposing data over MQTT or USB serial for the Atomic Pi to consume.

## Software setup on the Atomic Pi

1. **Install the CH340 driver** (if not already present). Most modern Linux kernels bundle the driver, but confirm with `lsmod | grep ch341`.
2. **Install toolchains** based on your integration strategy:
   * **ESPHome CLI** – Build and upload ESPHome firmware directly from the Atomic Pi to the UM960 for Home Assistant integration. See [`Examples/ESPHome`](../ESPHome) for configuration templates.
   * **Arduino CLI / PlatformIO** – Compile Arduino sketches (TFT_eSPI, LVGL, etc.) and flash them over USB. Review the [`Examples/Basics`](../Basics) directory for starter sketches.
   * **ESP-IDF** – When you need low-level control, install Espressif’s IDF (v5.x tested). Sample projects live under [`Examples/ESP-IDF`](../ESP-IDF).
   * **openHASP Web Installer** – From the Atomic Pi’s browser, flash prebuilt UI firmware to the UM960 and configure it over Wi-Fi. Reference [`Examples/openHASP`](../openHASP).
3. **Serial access**
   * Use `screen`, `minicom`, or `picocom` to monitor logs: `screen /dev/ttyUSB0 115200`.
   * Add a `udev` rule if you need persistent device names. Example `/etc/udev/rules.d/99-um960.rules`:
     ```
     SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyUM960"
     ```
   * Reload rules with `sudo udevadm control --reload-rules && sudo udevadm trigger`.

## Application patterns

* **Atomic Pi as automation hub** – Run Home Assistant or Node-RED on the Atomic Pi, with the UM960 acting as a touch HMI via ESPHome firmware.
* **Kiosk or dashboard** – Deploy a serial protocol or WebSocket bridge on the ESP32; the Atomic Pi renders web content and sends UI updates to the UM960 over serial/SPI.
* **Peripheral gateway** – Flash ESP-IDF firmware that proxies UM960 sensors to MQTT/REST, while the Atomic Pi handles heavy processing like AI inference.

## Troubleshooting tips

* If the UM960 does not enumerate, verify that the Atomic Pi’s USB port is providing 5 V and that the cable supports data.
* For noisy touch readings, ensure common ground between the Atomic Pi and UM960 when mixing USB power and header connections.
* When flashing firmware, close any active serial sessions (screen/minicom) to free the port.
* If you experience SPI timing issues, check that the Atomic Pi’s GPIO logic levels match the UM960’s 3.3 V requirements.

## Next steps

Explore the broader documentation for firmware examples, pinouts, and display configuration to tailor the UM960 to your Atomic Pi project:

* [`SETUP.md`](../../SETUP.md) – Environment preparation for Arduino, PlatformIO, and ESP-IDF toolchains.
* [`PINS.md`](../../PINS.md) – Breaks down header pin mappings and available peripherals.
* [`Examples/Projects`](.) – Additional inspiration for end-to-end applications.

