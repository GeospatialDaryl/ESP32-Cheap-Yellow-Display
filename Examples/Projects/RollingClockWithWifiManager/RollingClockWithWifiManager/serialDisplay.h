#ifndef SERIALDISPLAY_H
#define SERIALDISPLAY_H

#include "projectDisplay.h"

class SerialDisplay : public ProjectDisplay {
public:
  SerialDisplay();

  void displaySetup() override;
  void drawText(const String &text, int x, int y,
                uint16_t fg = ProjectDisplay::kDefaultColor,
                uint16_t bg = ProjectDisplay::kDefaultBg,
                int font = ProjectDisplay::kDefaultFont,
                bool center = false) override;
  void drawWifiManagerMessage(WiFiManager *myWiFiManager) override;
};

#endif
