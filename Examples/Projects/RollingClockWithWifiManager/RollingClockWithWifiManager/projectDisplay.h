
#ifndef PROJECTDISPLAY_H
#define PROJECTDISPLAY_H

#include <Arduino.h>

class ProjectDisplay
{
public:
  static const uint16_t defaultColor = 0xFFFF;
  static const uint16_t defaultBg = 0x0000;
  static const int defaultFont = 2;

  virtual void displaySetup() = 0;

  virtual void drawWifiManagerMessage(WiFiManager *myWiFiManager) = 0;

  virtual void drawText(const String &text, int x, int y, uint16_t fg = defaultColor, uint16_t bg = defaultBg, int font = defaultFont, bool center = false) = 0;

  void setWidth(int w)
  {
    screenWidth = w;
    screenCenterX = screenWidth / 2;
  }

  void setHeight(int h)
  {
    screenHeight = h;
  }

protected:
  int screenWidth;
  int screenHeight;
  int screenCenterX;
};
#endif
