#pragma once

#include <Arduino.h>
#include <Servo.h>

class TruckHardware {
 public:
  void begin();
  void sample(uint32_t now_ms);
  void writeOutputs(double throttle, double steering);
  int32_t count() const;
  double speed() const { return speed_mps_; }
  int escPulse() const { return esc_pulse_; }
  int servoPulse() const { return servo_pulse_; }

 private:
  Servo esc_;
  Servo servo_;
  uint32_t sample_ms_ = 0;
  uint32_t sample_count_ = 0;
  double speed_mps_ = 0.0;
  int esc_pulse_ = 1500;
  int servo_pulse_ = 1480;
};
