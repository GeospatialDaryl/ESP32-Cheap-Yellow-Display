/*-------- CYD (Cheap Yellow Display) ----------*/

// TFT_eSPI tft = TFT_eSPI();              // Invoke custom library
//  Will be defined outside of here
TFT_eSprite sprite = TFT_eSprite(&tft); // Sprite class

int clockFont = 1;
int clockSize = 6;
int clockDatum = TL_DATUM;
uint16_t clockBackgroundColor = TFT_BLACK;
uint16_t clockFontColor = TFT_YELLOW;
int prevDay = 0;

bool SHOW_24HOUR = false;
bool SHOW_AMPM = true;

bool NOT_US_DATE = true;

void SetupCYD()
{
    Serial.println("SetupCYD");
    // tft.init();
    tft.fillScreen(clockBackgroundColor);
    tft.setTextColor(clockFontColor, clockBackgroundColor);

    tft.setRotation(1);
    tft.setTextFont(clockFont);
    tft.setTextSize(clockSize);
    tft.setTextDatum(clockDatum);

    sprite.createSprite(tft.textWidth("8"), tft.fontHeight());
    sprite.setTextColor(clockFontColor, clockBackgroundColor);
    sprite.setRotation(1);
    sprite.setTextFont(clockFont);
    sprite.setTextSize(clockSize);
    sprite.setTextDatum(clockDatum);
}

/*-------- Digits ----------*/
#include "Digit.h"
Digit *digs[6];
int colons[2];
int timeY = 50;
int ampm[2]; // X, Y of the AM or PM indicator
bool ispm;

void CalculateDigitOffsets()
{
    int y = timeY;
    int width = tft.width();
    int DigitWidth = tft.textWidth("8");
    int colonWidth = tft.textWidth(":");
    int left = SHOW_AMPM ? 10 : (width - DigitWidth * 6 - colonWidth * 2) / 2;
      digs[0]->setPosition(left, y);                      // HH
      digs[1]->setPosition(digs[0]->getX() + DigitWidth, y); // HH

      colons[0] = digs[1]->getX() + DigitWidth; // :

      digs[2]->setPosition(colons[0] + colonWidth, y); // MM
      digs[3]->setPosition(digs[2]->getX() + DigitWidth, y);

      colons[1] = digs[3]->getX() + DigitWidth; // :

      digs[4]->setPosition(colons[1] + colonWidth, y); // SS
      digs[5]->setPosition(digs[4]->getX() + DigitWidth, y);

      ampm[0] = digs[5]->getX() + DigitWidth + 4;
    ampm[1] = y - 2;
}

void SetupDigits()
{
    tft.fillScreen(clockBackgroundColor);
    tft.setTextFont(clockFont);
    tft.setTextSize(clockSize);
    tft.setTextDatum(clockDatum);

    for (size_t i = 0; i < 6; i++)
    {
        digs[i] = new Digit(0);
        digs[i]->setHeight(tft.fontHeight());
    }

    //-- Measure font widths --
    // Debug("1", tft.textWidth("1"));
    // Debug(":", tft.textWidth(":"));
    // Debug("8", tft.textWidth("8"));

    CalculateDigitOffsets();
}

/*-------- DRAWING ----------*/
void DrawColons()
{
    tft.setTextFont(clockFont);
    tft.setTextSize(clockSize);
    tft.setTextDatum(clockDatum);
    tft.drawChar(':', colons[0], timeY);
    tft.drawChar(':', colons[1], timeY);
}

void DrawAmPm()
{
    if (SHOW_AMPM)
    {
        tft.setTextSize(3);
        tft.drawChar(ispm ? 'P' : 'A', ampm[0], ampm[1]);
        tft.drawChar('M', ampm[0], ampm[1] + tft.fontHeight());
    }
}

void DrawADigit(Digit *digg); // Without this line, compiler says: error: variable or field 'DrawADigit' declared void.

void DrawADigit(Digit *digg)
{
    if (digg->getValue() == digg->getNewValue())
    {
        sprite.drawNumber(digg->getValue(), 0, 0);
        sprite.pushSprite(digg->getX(), digg->getY());
    }
    else
    {
        for (size_t f = 0; f <= digg->getHeight(); f++)
        {
            digg->setFrame(f);
            sprite.drawNumber(digg->getValue(), 0, -digg->getFrame());
            sprite.drawNumber(digg->getNewValue(), 0, digg->getHeight() - digg->getFrame());
            sprite.pushSprite(digg->getX(), digg->getY());
            delay(5);
        }
        digg->setValue(digg->getNewValue());
    }
}

void DrawDigitsAtOnce()
{
    tft.setTextDatum(TL_DATUM);
    for (size_t f = 0; f <= digs[0]->getHeight(); f++) // For all animation frames...
    {
        for (size_t di = 0; di < 6; di++) // for all Digits...
        {
            Digit *dig = digs[di];
            if (dig->getValue() == dig->getNewValue()) // If Digit is not changing...
            {
                if (f == 0) //... and this is first frame, just draw it to screeen without animation.
                {
                    sprite.drawNumber(dig->getValue(), 0, 0);
                    sprite.pushSprite(dig->getX(), dig->getY());
                }
            }
            else // However, if a Digit is changing value, we need to draw animation frame "f"
            {
                dig->setFrame(f);                                                       // Set the animation offset
                sprite.drawNumber(dig->getValue(), 0, -dig->getFrame());                   // Scroll up the current value
                sprite.drawNumber(dig->getNewValue(), 0, dig->getHeight() - dig->getFrame()); // while make new value appear from below
                sprite.pushSprite(dig->getX(), dig->getY());                               // Draw the current animation frame to actual screen.
            }
        }
        delay(5);
    }

    // Once all animations are done, then we can update all Digits to current new values.
    for (size_t di = 0; di < 6; di++)
    {
        Digit *dig = digs[di];
        dig->setValue(dig->getNewValue());
    }
}

void DrawDigitsWithoutAnimation()
{
    for (size_t di = 0; di < 6; di++)
    {
        Digit *dig = digs[di];
        dig->setValue(dig->getNewValue());
        dig->setFrame(0);
        sprite.drawNumber(dig->getNewValue(), 0, 0);
        sprite.pushSprite(dig->getX(), dig->getY());
    }
}

void DrawDigitsOneByOne()
{
    tft.setTextDatum(TL_DATUM);
    for (size_t i = 0; i < 6; i++)
    {
        DrawADigit(digs[5 - i]);
    }
}

void ParseDigits()
{
    time_t local = myTZ.now();
    digs[0]->setNewValue((SHOW_24HOUR ? hour(local) : hourFormat12(local)) / 10);
    digs[1]->setNewValue((SHOW_24HOUR ? hour(local) : hourFormat12(local)) % 10);
    digs[2]->setNewValue(minute(local) / 10);
    digs[3]->setNewValue(minute(local) % 10);
    digs[4]->setNewValue(second(local) / 10);
    digs[5]->setNewValue(second(local) % 10);
    ispm = isPM(local);
}

void DrawDate()
{
    // time_t local = myTZ.toLocal(utc, &tcr);
    time_t local = myTZ.now();
    int dd = day(local);
    int mth = month(local);
    int yr = year(local);

    if (dd != prevDay)
    {
        prevDay = dd;
        tft.setTextDatum(BC_DATUM);
        char buffer[50];
        if (NOT_US_DATE)
        {
            sprintf(buffer, "%02d/%02d/%d", dd, mth, yr);
        }
        else
        {
            // MURICA!!
            sprintf(buffer, "%02d/%02d/%d", mth, dd, yr);
        }

        tft.setTextSize(4);
        int h = tft.fontHeight();
        tft.fillRect(0, 210 - h, 320, h, TFT_BLACK);

        projectDisplay.drawText(buffer, 320 / 2, 210, clockFontColor, clockBackgroundColor, clockFont, true);

        int dow = weekday(local);
        String dayNames[] = {"", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};
        tft.setTextSize(4);
        tft.fillRect(0, 170 - h, 320, h, TFT_BLACK);
        projectDisplay.drawText(dayNames[dow], 320 / 2, 170, clockFontColor, clockBackgroundColor, clockFont, true);
    }
}

void rollingClockSetup(bool is24Hour, bool notUsDate)
{
    Serial.println("rollingClockSetup");
    SHOW_24HOUR = is24Hour;
    SHOW_AMPM = !is24Hour;
    NOT_US_DATE = notUsDate;
    SetupCYD();
    SetupDigits();
}

void drawRollingClock()
{
    ParseDigits();
    DrawDigitsAtOnce(); // Choose one: DrawDigitsWithoutAnimation(), DrawDigitsAtOnce(), DrawDigitsOneByOne()
    DrawDate();         // Draw Date and day of the week.
    DrawColons();
    DrawAmPm();
}