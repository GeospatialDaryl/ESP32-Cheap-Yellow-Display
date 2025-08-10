#include "wifiManagerHandler.h"
#include <WiFi.h>

WiFiManagerHandler *WiFiManagerHandler::instance = nullptr;

WiFiManagerHandler::WiFiManagerHandler()
    : drd(kDrdTimeout, kDrdAddress), wmDisplay(nullptr), shouldSaveConfig(false) {
  instance = this;
}

bool WiFiManagerHandler::detectDoubleReset() {
  if (drd.detectDoubleReset()) {
    Serial.println(F("Forcing config mode as there was a Double reset detected"));
    return true;
  }
  return false;
}

void WiFiManagerHandler::saveConfigCallback() {
  if (instance) {
    instance->shouldSaveConfig = true;
  }
}

void WiFiManagerHandler::configModeCallback(WiFiManager *myWiFiManager) {
  if (instance && instance->wmDisplay) {
    instance->wmDisplay->drawWifiManagerMessage(myWiFiManager);
  }
}

void WiFiManagerHandler::setupWiFiManager(bool forceConfig, ProjectConfig &config, ProjectDisplay &display) {
  wmDisplay = &display;
  WiFiManager wm;
  wm.setSaveConfigCallback(saveConfigCallback);
  wm.setAPCallback(configModeCallback);

  WiFiManagerParameter timeZoneParam(PROJECT_TIME_ZONE_LABEL, "Time Zone", config.timeZone.c_str(), 60);

  char checkBox[] = "type=\"checkbox\"";
  char checkBoxChecked[] = "type=\"checkbox\" checked";
  char *customHtml;

  if (config.twentyFourHour) {
    customHtml = checkBoxChecked;
  } else {
    customHtml = checkBox;
  }
  WiFiManagerParameter isTwentyFourHour(PROJECT_TIME_TWENTY_FOUR_HOUR, "24H Clock", "T", 2, customHtml);

  char *customHtmlTwo;
  if (config.usDateFormat) {
    customHtmlTwo = checkBoxChecked;
  } else {
    customHtmlTwo = checkBox;
  }
  WiFiManagerParameter isUsDateFormat(PROJECT_TIME_US_DATE, "US Date Format", "T", 2, customHtmlTwo);

  wm.addParameter(&timeZoneParam);
  wm.addParameter(&isTwentyFourHour);
  wm.addParameter(&isUsDateFormat);

  if (forceConfig) {
    drd.stop();
    if (!wm.startConfigPortal("esp32Project", "brianlough")) {
      Serial.println("failed to connect and hit timeout");
      delay(3000);
      ESP.restart();
      delay(5000);
    }
  } else {
    if (!wm.autoConnect("esp32Project", "brianlough")) {
      Serial.println("failed to connect and hit timeout");
      delay(3000);
      ESP.restart();
      delay(5000);
    }
  }

  if (shouldSaveConfig) {
    config.timeZone = String(timeZoneParam.getValue());
    config.twentyFourHour = (strncmp(isTwentyFourHour.getValue(), "T", 1) == 0);
    config.usDateFormat = (strncmp(isUsDateFormat.getValue(), "T", 1) == 0);

    config.saveConfigFile();
    drd.stop();
    ESP.restart();
    delay(5000);
  }
}

void WiFiManagerHandler::loop() {
  drd.loop();
}

