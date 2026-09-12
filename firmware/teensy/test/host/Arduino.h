#pragma once
#include <cstdint>
#include <cstddef>
#include <string>
#include <deque>

#define LED_BUILTIN 13
#define INPUT_PULLUP 2
#define OUTPUT 1
#define CHANGE 3
inline uint32_t fake_ms = 0;
inline int pins[64] = {};
inline void (*handlers[64])() = {};
inline uint32_t millis() { return fake_ms; }
inline void noInterrupts() {}
inline void interrupts() {}
inline void pinMode(int pin, int mode) { if (mode == INPUT_PULLUP) pins[pin] = 1; }
inline int digitalReadFast(int pin) { return pins[pin]; }
inline int digitalRead(int pin) { return pins[pin]; }
inline void digitalWrite(int pin, int value) { pins[pin] = value; }
inline int digitalPinToInterrupt(int pin) { return pin; }
inline void attachInterrupt(int pin, void (*fn)(), int) { handlers[pin] = fn; }
struct FakeSerial {
  bool connected = true;
  int capacity = 4096;
  std::deque<char> input;
  std::string output;
  explicit operator bool() const { return connected; }
  void begin(int) {}
  int available() const { return static_cast<int>(input.size()); }
  int availableForWrite() const { return capacity; }
  int read() { char c = input.front(); input.pop_front(); return c; }
  void write(const uint8_t* bytes, size_t n) { output.append(reinterpret_cast<const char*>(bytes), n); }
  void write(char c) { output += c; }
};
inline FakeSerial Serial;
