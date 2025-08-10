#ifndef WIFIMANAGERHANDLER_H
#define WIFIMANAGERHANDLER_H

#include <WiFiManager.h>
#include <ESP_DoubleResetDetector.h>
#include "projectConfig.h"
#include "projectDisplay.h"

class WiFiManagerHandler {
public:
  WiFiManagerHandler();

  bool detectDoubleReset();
  void setupWiFiManager(bool forceConfig, ProjectConfig &config, ProjectDisplay &display);
  void loop();

private:
  static constexpr unsigned long kDrdTimeout = 10;
  static constexpr unsigned long kDrdAddress = 0;

  static WiFiManagerHandler *instance;
  DoubleResetDetector drd;
  ProjectDisplay *wmDisplay;
  bool shouldSaveConfig;

  static void saveConfigCallback();
  static void configModeCallback(WiFiManager *myWiFiManager);
};

#endif
