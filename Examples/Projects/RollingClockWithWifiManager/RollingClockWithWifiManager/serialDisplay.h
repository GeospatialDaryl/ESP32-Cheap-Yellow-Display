#include "projectDisplay.h"

class SerialDisplay : public ProjectDisplay
{
public:
  void displaySetup()
  {
    Serial.println("Serial Display Setup");
  }

  void drawText(const String &text, int x, int y, uint16_t fg = defaultColor, uint16_t bg = defaultBg, int font = defaultFont, bool center = false)
  {
    Serial.printf("%s\n", text.c_str());
  }

  void drawWifiManagerMessage(WiFiManager *myWiFiManager)
  {
    drawText("Entered Conf Mode:", 0, 0);
    drawText("Connect to the following WIFI AP:", 0, 0);
    drawText(myWiFiManager->getConfigPortalSSID(), 0, 0);
    drawText("Password:", 0, 0);
    drawText("brianlough", 0, 0);
    drawText("If it doesn't AutoConnect, use this IP:", 0, 0);
    drawText(WiFi.softAPIP().toString(), 0, 0);
  }
};
