#include "Digit.h"

Digit::Digit(int value)
    : m_value(value), m_newValue(value), m_frame(0), m_height(0), m_position{0, 0} {}

Digit::~Digit() {}

int Digit::getValue() const {
    return m_value;
}

void Digit::setValue(int value) {
    m_value = value;
    m_newValue = value;
}

int Digit::getNewValue() const {
    return m_newValue;
}

void Digit::setNewValue(int newValue) {
    m_newValue = newValue;
}

int Digit::getFrame() const {
    return m_frame;
}

void Digit::setFrame(int frame) {
    m_frame = frame;
}

int Digit::getHeight() const {
    return m_height;
}

void Digit::setHeight(int height) {
    m_height = height;
}

void Digit::setPosition(int x, int y) {
    m_position.x = x;
    m_position.y = y;
}

int Digit::getX() const { return m_position.x; }
int Digit::getY() const { return m_position.y; }