#pragma once

#include <Arduino.h>
#include <PID_v1.h>

// Owns two completely independent feedback controllers. The class only
// computes normalized commands; hardware drivers are responsible for mapping
// those commands to PWM/servo signals and enforcing the emergency stop.
class PidControllers {
 public:
  PidControllers();

  void begin();
  void enable();
  void disable();
  bool enabled() const;

  void setSpeedTarget(double metres_per_second);
  void setSteeringTarget(double degrees);
  void setSpeedTunings(double kp, double ki, double kd);
  void setSteeringTunings(double kp, double ki, double kd);

  // Call every loop with fresh feedback. PID_v1 enforces the configured
  // sample period internally. Outputs are normalized to [-1, 1].
  void update(double measured_speed_metres_per_second,
              double measured_steering_degrees);

  double throttleCommand() const;
  double steeringCommand() const;
  double speedTarget() const;
  double steeringTarget() const;

 private:
  double measured_speed_;
  double throttle_command_;
  double speed_target_;

  double measured_steering_;
  double steering_command_;
  double steering_target_;

  PID speed_pid_;
  PID steering_pid_;
  bool enabled_;
};
