/*******************************************************************
    TFT_eSPI button example for the ESP32 Cheap Yellow Display.

    https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display

    Written by Claus Näveke
    Github: https://github.com/TheNitek
 *******************************************************************/

// Make sure to copy the UserSetup.h file into the library as
// per the Github Instructions. The pins are defined in there.

// ----------------------------
// Standard Libraries
// ----------------------------

#include <SPI.h>

// ----------------------------
// Additional Libraries - each one of these will need to be installed.
// ----------------------------

#include <XPT2046_Bitbang.h>
// A library for interfacing with the touch screen
//
// Can be installed from the library manager (Search for "XPT2046 Slim")
// https://github.com/TheNitek/XPT2046_Bitbang_Arduino_Library

#include <TFT_eSPI.h>
// A library for interfacing with LCD displays
//
// Can be installed from the library manager (Search for "TFT_eSPI")
// https://github.com/Bodmer/TFT_eSPI

struct Hotspot {
  uint16_t x, y, w, h;
  void (*onPress)();
};

static const uint8_t MAX_HOTSPOTS = 16;
Hotspot hotspots[MAX_HOTSPOTS];
bool hotspotPressed[MAX_HOTSPOTS];
uint8_t hotspotCount = 0;

void registerHotspot(uint16_t x, uint16_t y, uint16_t w, uint16_t h, void (*onPress)()) {
  if (hotspotCount < MAX_HOTSPOTS) {
    hotspots[hotspotCount] = {x, y, w, h, onPress};
    hotspotPressed[hotspotCount] = false;
    hotspotCount++;
  }
}

void registerJpegHotspot(uint16_t jpegX, uint16_t jpegY, uint16_t x, uint16_t y, uint16_t w, uint16_t h, void (*onPress)()) {
  registerHotspot(jpegX + x, jpegY + y, w, h, onPress);
}

void checkTouchHotspots(const TouchPoint &p) {
  for (uint8_t i = 0; i < hotspotCount; ++i) {
    bool inside = (p.zRaw > 0) &&
                  (p.x >= hotspots[i].x) && (p.x < hotspots[i].x + hotspots[i].w) &&
                  (p.y >= hotspots[i].y) && (p.y < hotspots[i].y + hotspots[i].h);
    if (inside && !hotspotPressed[i]) {
      hotspotPressed[i] = true;
      if (hotspots[i].onPress) {
        hotspots[i].onPress();
      }
    } else if (!inside) {
      hotspotPressed[i] = false;
    }
  }
}


// ----------------------------
// Touch Screen pins
// ----------------------------

// The CYD touch uses some non default
// SPI pins

#define XPT2046_IRQ 36
#define XPT2046_MOSI 32
#define XPT2046_MISO 39
#define XPT2046_CLK 25
#define XPT2046_CS 33
// ----------------------------

XPT2046_Bitbang ts(XPT2046_MOSI, XPT2046_MISO, XPT2046_CLK, XPT2046_CS);

TFT_eSPI tft = TFT_eSPI();

TFT_eSPI_Button key[6];

void button1Pressed() { Serial.println("Hotspot 1 pressed"); }
void button2Pressed() { Serial.println("Hotspot 2 pressed"); }
void button3Pressed() { Serial.println("Hotspot 3 pressed"); }
void button4Pressed() { Serial.println("Hotspot 4 pressed"); }
void button5Pressed() { Serial.println("Hotspot 5 pressed"); }
void button6Pressed() { Serial.println("Hotspot 6 pressed"); }

void (*buttonCallbacks[6])() = {
  button1Pressed,
  button2Pressed,
  button3Pressed,
  button4Pressed,
  button5Pressed,
  button6Pressed,
};

void setup() {
  Serial.begin(115200);

  // Start the SPI for the touch screen and init the TS library
  ts.begin();
  //ts.setRotation(1);

  // Start the tft display and set it to black
  tft.init();
  tft.setRotation(1); //This is the display in landscape

  // Clear the screen before writing to it
  tft.fillScreen(TFT_BLACK);
  tft.setFreeFont(&FreeMono18pt7b);

  drawButtons();
}


void drawButtons() {
  uint16_t bWidth = TFT_HEIGHT/3;
  uint16_t bHeight = TFT_WIDTH/2;
  // Generate buttons with different size X deltas
  for (int i = 0; i < 6; i++) {
    key[i].initButton(&tft,
                      bWidth * (i%3) + bWidth/2,
                      bHeight * (i/3) + bHeight/2,
                      bWidth,
                      bHeight,
                      TFT_BLACK, // Outline
                      TFT_BLUE, // Fill
                      TFT_BLACK, // Text
                      "",
                      1);

    key[i].drawButton(false, String(i+1));
    registerHotspot(bWidth * (i%3), bHeight * (i/3), bWidth, bHeight, buttonCallbacks[i]);
  }
}

void loop() {
  TouchPoint p = ts.getTouch();
  // Adjust press state of each key appropriately
  for (uint8_t b = 0; b < 6; b++) {
    if ((p.zRaw > 0) && key[b].contains(p.x, p.y)) {
      key[b].press(true);  // tell the button it is pressed
    } else {
      key[b].press(false);  // tell the button it is NOT pressed
    }
  }

  // Check if any key has changed state
  for (uint8_t b = 0; b < 6; b++) {
    // If button was just pressed, redraw inverted button
    if (key[b].justPressed()) {
      key[b].drawButton(true, String(b+1));
    }

    // If button was just released, redraw normal color button
    if (key[b].justReleased()) {
      key[b].drawButton(false, String(b+1));
    }
  }

  checkTouchHotspots(p);
  delay(50);
}
