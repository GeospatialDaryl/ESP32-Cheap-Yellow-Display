#ifndef CHEAPYELLOWLCD_H
#define CHEAPYELLOWLCD_H

#include "projectDisplay.h"
#include <TFT_eSPI.h>

class CheapYellowDisplay : public ProjectDisplay {
public:
  CheapYellowDisplay();

  void displaySetup() override;
  void drawText(const String &text, int x, int y,
                uint16_t fg = ProjectDisplay::kDefaultColor,
                uint16_t bg = ProjectDisplay::kDefaultBg,
                int font = ProjectDisplay::kDefaultFont,
                bool center = false) override;
  void drawWifiManagerMessage(WiFiManager *myWiFiManager) override;

private:
  TFT_eSPI tft;
};

#endif
