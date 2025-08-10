#include "serialDisplay.h"
#include <WiFi.h>
#include <WiFiManager.h>

SerialDisplay::SerialDisplay() : ProjectDisplay() {}

void SerialDisplay::displaySetup() {
  Serial.println("Serial Display Setup");
}

void SerialDisplay::drawText(const String &text, int x, int y,
                             uint16_t fg, uint16_t bg, int font, bool center) {
  (void)x;
  (void)y;
  (void)fg;
  (void)bg;
  (void)font;
  (void)center;
  Serial.printf("%s\n", text.c_str());
}

void SerialDisplay::drawWifiManagerMessage(WiFiManager *myWiFiManager) {
  drawText("Entered Conf Mode:", 0, 0);
  drawText("Connect to the following WIFI AP:", 0, 0);
  drawText(myWiFiManager->getConfigPortalSSID(), 0, 0);
  drawText("Password:", 0, 0);
  drawText("brianlough", 0, 0);
  drawText("If it doesn't AutoConnect, use this IP:", 0, 0);
  drawText(WiFi.softAPIP().toString(), 0, 0);
}

