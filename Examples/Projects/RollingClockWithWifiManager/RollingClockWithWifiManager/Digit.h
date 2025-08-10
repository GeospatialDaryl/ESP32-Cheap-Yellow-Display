
class Digit {
private:
    int m_value;
    int m_newValue;
    int m_frame;
    int m_height;
    struct Position {
        int x;
        int y;
    } m_position;

public:
    explicit Digit(int value);
    ~Digit();
    int getValue() const;
    void setValue(int value);
    int getNewValue() const;
    void setNewValue(int newValue);
    int getFrame() const;
    void setFrame(int frame);
    int getHeight() const;
    void setHeight(int height);
    void setPosition(int x, int y);
    int getX() const;
    int getY() const;
};

