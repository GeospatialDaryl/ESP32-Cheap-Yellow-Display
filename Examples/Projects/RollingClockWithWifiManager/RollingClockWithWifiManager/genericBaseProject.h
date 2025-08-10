// ----------------------------
// Library Defines - Need to be defined before library import
// ----------------------------

#define ESP_DRD_USE_SPIFFS true

// ----------------------------
// Standard Libraries
// ----------------------------
#include <WiFi.h>

#include <FS.h>
#include "SPIFFS.h"

// ----------------------------
// Additional Libraries - each one of these will need to be installed.
// ----------------------------


#include <ezTime.h>
// Library used for getting the time and converting session time
// to users timezone

// Search for "ezTime" in the Arduino Library manager
// https://github.com/ropg/ezTime

#include <ArduinoJson.h>
// Library used for parsing Json from the API responses

// Search for "Arduino Json" in the Arduino Library manager
// https://github.com/bblanchon/ArduinoJson

// ----------------------------
// Internal includes
// ----------------------------

#include "projectConfig.h"
#include "projectDisplay.h"
#include "wifiManagerHandler.h"
#include "cheapYellowLCD.h"

ProjectConfig projectConfig;

CheapYellowDisplay projectDisplay;
WiFiManagerHandler wifiManager;

Timezone myTZ;

void baseProjectSetup()
{
    projectDisplay.displaySetup();

    bool forceConfig = wifiManager.detectDoubleReset();

    // Initialise SPIFFS, if this fails try .begin(true)
    // NOTE: I believe this formats it though it will erase everything on
    // spiffs already! In this example that is not a problem.
    // I have found once I used the true flag once, I could use it
    // without the true flag after that.
    bool spiffsInitSuccess = SPIFFS.begin(false) || SPIFFS.begin(true);
    if (!spiffsInitSuccess)
    {
        Serial.println("SPIFFS initialisation failed!");
        while (1)
            yield(); // Stay here twiddling thumbs waiting
    }
    Serial.println("\r\nInitialisation done.");

    if (!projectConfig.fetchConfigFile())
    {
        // Failed to fetch config file, need to launch Wifi Manager
        forceConfig = true;
    }

    // While Wifi is not connected it will not progress past here
    wifiManager.setupWiFiManager(forceConfig, projectConfig, projectDisplay);

    // Set WiFi to station mode and disconnect from an AP if it was Previously
    // connected
    // WiFi.mode(WIFI_STA);
    // WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED)
    {
        Serial.print(".");
        delay(500);
    }

    Serial.println("");
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());

    Serial.println("Waiting for time sync");

    waitForSync();

    Serial.println();
    Serial.println("UTC:             " + UTC.dateTime());

    myTZ.setLocation(projectConfig.timeZone);
    Serial.print(projectConfig.timeZone);
    Serial.print(F(":     "));
    Serial.println(myTZ.dateTime());
    Serial.println("-------------------------");
}

void baseProjectLoop()
{
    wifiManager.loop();
}
