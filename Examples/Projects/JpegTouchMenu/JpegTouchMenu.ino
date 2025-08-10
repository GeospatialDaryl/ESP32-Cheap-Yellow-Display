/*
  JpegTouchMenu example for the ESP32 Cheap Yellow Display.
  Loads a JPEG background and uses touch hotspots.
*/

#include <TFT_eSPI.h>
#include <TJpg_Decoder.h>
#include <XPT2046_Bitbang.h>
#include <SPI.h>
#include <SD.h>

#define XPT2046_IRQ 36
#define XPT2046_MOSI 32
#define XPT2046_MISO 39
#define XPT2046_CLK 25
#define XPT2046_CS 33
#define SD_CS 5
#define LED_PIN 2

// Touch calibration values
#define TOUCH_MINX 200
#define TOUCH_MAXX 3900
#define TOUCH_MINY 200
#define TOUCH_MAXY 3800

TFT_eSPI tft = TFT_eSPI();
SPIClass sdSpi = SPIClass(VSPI);
XPT2046_Bitbang ts = XPT2046_Bitbang(XPT2046_MOSI, XPT2046_MISO, XPT2046_CLK, XPT2046_CS);

bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t *bitmap) {
  if (y >= tft.height()) return 0;
  tft.pushImage(x, y, w, h, bitmap);
  return 1;
}

void drawJpeg(const char *filename, int16_t x, int16_t y) {
  TJpgDec.drawSdJpg(filename, x, y);
}

struct Hotspot {
  int16_t x;
  int16_t y;
  int16_t w;
  int16_t h;
};

Hotspot btn1 = {20, 180, 100, 60};
Hotspot btn2 = {200, 180, 100, 60};

void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);

  tft.init();
  tft.setRotation(1);
  tft.setSwapBytes(true);

  ts.begin();

  sdSpi.begin(18, 19, 23, SD_CS);
  if (!SD.begin(SD_CS, sdSpi)) {
    Serial.println("SD init failed!");
    while (true) delay(1);
  }

  TJpgDec.setSwapBytes(true);
  TJpgDec.setCallback(tft_output);

  drawJpeg("/menu.jpg", 0, 0);
}

void loop() {
  TouchPoint p = ts.getTouch();
  if (p.zRaw > 0) {
    int16_t x = map(p.xRaw, TOUCH_MINX, TOUCH_MAXX, 0, tft.width());
    int16_t y = map(p.yRaw, TOUCH_MINY, TOUCH_MAXY, 0, tft.height());

    if (x > btn1.x && x < btn1.x + btn1.w && y > btn1.y && y < btn1.y + btn1.h) {
      Serial.println("Button 1");
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      delay(300);
    } else if (x > btn2.x && x < btn2.x + btn2.w && y > btn2.y && y < btn2.y + btn2.h) {
      Serial.println("Button 2");
      delay(300);
    }
  }
  delay(20);
}

