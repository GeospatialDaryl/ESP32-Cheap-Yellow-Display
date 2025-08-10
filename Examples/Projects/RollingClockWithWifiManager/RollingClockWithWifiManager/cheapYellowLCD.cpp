#include "cheapYellowLCD.h"
#include <WiFi.h>
#include <WiFiManager.h>

CheapYellowDisplay::CheapYellowDisplay() : ProjectDisplay(320, 240), tft() {}

void CheapYellowDisplay::displaySetup() {
  Serial.println("cyd display setup");
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
}

void CheapYellowDisplay::drawText(const String &text, int x, int y,
                                  uint16_t fg, uint16_t bg, int font,
                                  bool center) {
  tft.setTextColor(fg, bg);
  if (center) {
    tft.drawCentreString(text, x, y, font);
  } else {
    tft.drawString(text, x, y, font);
  }
}

void CheapYellowDisplay::drawWifiManagerMessage(WiFiManager *myWiFiManager) {
  Serial.println("Entered Conf Mode");
  tft.fillScreen(TFT_BLACK);
  drawText("Entered Conf Mode:", screenCenterX, 5, TFT_WHITE, TFT_BLACK, 2, true);
  drawText("Connect to the following WIFI AP:", 5, 28, TFT_WHITE, TFT_BLACK, 2);
  drawText(myWiFiManager->getConfigPortalSSID(), 20, 48, TFT_BLUE, TFT_BLACK, 2);
  drawText("Password:", 5, 64, TFT_WHITE, TFT_BLACK, 2);
  drawText("brianlough", 20, 82, TFT_BLUE, TFT_BLACK, 2);
  drawText("If it doesn't AutoConnect, use this IP:", 5, 110, TFT_WHITE, TFT_BLACK, 2);
  drawText(WiFi.softAPIP().toString(), 20, 128, TFT_BLUE, TFT_BLACK, 2);
}

