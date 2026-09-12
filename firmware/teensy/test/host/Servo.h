#pragma once
inline int pulses[64] = {};
class Servo {
 public:
  void attach(int pin) { pin_ = pin; pulses[pin_] = 1500; }
  void writeMicroseconds(int value) { pulses[pin_] = value; }
 private:
  int pin_ = 0;
};
