#pragma once

#include <TFT_eSPI.h>
#include <JPEGDEC.h>
#include <FS.h>
#ifdef ESP32
#include <SPIFFS.h>
#include <SD.h>
#endif

#if defined(SdFat_h)
extern SdFat sd;
static SdBaseFile sdfatFile;
#endif

static JPEGDEC jpeg;
static File fsFile;

enum JpegSource { SRC_NONE, SRC_FS, SRC_SDFAT };
static JpegSource jpegSource = SRC_NONE;
static TFT_eSPI *jpegTft = nullptr;

static int jpegDraw(JPEGDRAW *pDraw) {
  if (jpegTft == nullptr) return 0;
  jpegTft->pushImage(pDraw->x, pDraw->y, pDraw->iWidth, pDraw->iHeight, pDraw->pPixels);
  return 1;
}

static void *myOpen(const char *filename, int32_t *size) {
#ifdef ESP32
  if (SPIFFS.exists(filename)) {
    fsFile = SPIFFS.open(filename, FILE_READ);
    if (fsFile) {
      *size = fsFile.size();
      jpegSource = SRC_FS;
      return &fsFile;
    }
  }
  if (SD.exists(filename)) {
    fsFile = SD.open(filename, FILE_READ);
    if (fsFile) {
      *size = fsFile.size();
      jpegSource = SRC_FS;
      return &fsFile;
    }
  }
#endif
#if defined(SdFat_h)
  sdfatFile = sd.open(filename);
  if (sdfatFile) {
    *size = sdfatFile.fileSize();
    jpegSource = SRC_SDFAT;
    return &sdfatFile;
  }
#endif
  return nullptr;
}

static void myClose(void *handle) {
  if (jpegSource == SRC_SDFAT) {
#if defined(SdFat_h)
    if (sdfatFile) sdfatFile.close();
#endif
  } else {
    if (fsFile) fsFile.close();
  }
  jpegSource = SRC_NONE;
}

static int32_t myRead(JPEGFILE *handle, uint8_t *buffer, int32_t length) {
  if (jpegSource == SRC_SDFAT) {
#if defined(SdFat_h)
    return sdfatFile.read(buffer, length);
#endif
  } else if (fsFile) {
    return fsFile.read(buffer, length);
  }
  return 0;
}

static int32_t mySeek(JPEGFILE *handle, int32_t position) {
  if (jpegSource == SRC_SDFAT) {
#if defined(SdFat_h)
    return sdfatFile.seekSet(position);
#endif
  } else if (fsFile) {
    return fsFile.seek(position);
  }
  return 0;
}

static void decodeJpeg(const char *name, TFT_eSPI &tft) {
  jpegTft = &tft;
  if (!jpeg.open(name, myOpen, myClose, myRead, mySeek, jpegDraw)) {
    return;
  }
  uint16_t w = jpeg.getWidth();
  uint16_t h = jpeg.getHeight();
  uint8_t scale = 0;
  while ((w >> scale) > tft.width() || (h >> scale) > tft.height()) {
    if (scale == 3) break;
    scale++;
  }
  uint16_t dw = w >> scale;
  uint16_t dh = h >> scale;
  if (dw < tft.width() || dh < tft.height()) {
    tft.fillScreen(TFT_BLACK);
  }
  int16_t x = (tft.width() - dw) / 2;
  int16_t y = (tft.height() - dh) / 2;
  jpeg.decode(x, y, scale);
  jpeg.close();
}

inline void drawJpeg(const char *path, TFT_eSPI &tft) {
  decodeJpeg(path, tft);
}

