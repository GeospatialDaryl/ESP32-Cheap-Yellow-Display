#include "projectDisplay.h"

#include <TFT_eSPI.h>
// A library for interfacing with LCD displays
//
// Can be installed from the library manager (Search for "TFT_eSPI")
// https://github.com/Bodmer/TFT_eSPI

TFT_eSPI tft = TFT_eSPI();

class CheapYellowDisplay : public ProjectDisplay
{
public:
  void displaySetup()
  {

    Serial.println("cyd display setup");
    setWidth(320);
    setHeight(240);

    // Start the tft display and set it to black
    tft.init();
    tft.setRotation(1);
    tft.fillScreen(TFT_BLACK);
  }

  void drawText(const String &text, int x, int y, uint16_t fg = defaultColor, uint16_t bg = defaultBg, int font = defaultFont, bool center = false)
  {
    tft.setTextColor(fg, bg);
    if (center)
    {
      tft.drawCentreString(text, x, y, font);
    }
    else
    {
      tft.drawString(text, x, y, font);
    }
  }

  void drawWifiManagerMessage(WiFiManager *myWiFiManager)
  {
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
};
