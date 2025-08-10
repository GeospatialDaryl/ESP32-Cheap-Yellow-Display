# JpegTouchMenu

Loads a JPEG menu background from the SD card and uses touch hotspots to trigger actions.

## SD card setup

* Format an SD card as FAT32.
* Copy `menu.jpg` to the root of the card.
* Insert the card into the display before powering on.

## Touch calibration

Raw touch values need to be mapped to the screen coordinates. Run the calibration example from the [`XPT2046_Bitbang`](https://github.com/TheNitek/XPT2046_Bitbang_Arduino_Library) library to obtain the minimum and maximum `x`/`y` values for your panel. Update the `TOUCH_MIN*` and `TOUCH_MAX*` defines in the sketch with your results.

The default sketch defines two hotspots matching buttons drawn in `menu.jpg`. Touching a hotspot toggles the built-in LED or prints a message to the serial monitor.
