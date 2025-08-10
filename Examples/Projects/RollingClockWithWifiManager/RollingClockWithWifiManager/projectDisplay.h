
#ifndef PROJECTDISPLAY_H
#define PROJECTDISPLAY_H

#include <Arduino.h>

class WiFiManager;

class ProjectDisplay {
public:
  static constexpr uint16_t kDefaultColor = 0xFFFF;
  static constexpr uint16_t kDefaultBg = 0x0000;
  static constexpr int kDefaultFont = 2;

  explicit ProjectDisplay(int width = 0, int height = 0);
  virtual ~ProjectDisplay() = default;

  virtual void displaySetup() = 0;

  virtual void drawWifiManagerMessage(WiFiManager *myWiFiManager) = 0;

  virtual void drawText(const String &text, int x, int y,
                        uint16_t fg = kDefaultColor,
                        uint16_t bg = kDefaultBg,
                        int font = kDefaultFont,
                        bool center = false) = 0;

protected:
  int screenWidth;
  int screenHeight;
  int screenCenterX;
};
#endif
