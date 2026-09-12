#pragma once

#include <Arduino.h>
#include <PID_v1.h>

// Owns the speed PID and a reserved steering PID. With no external angle sensor,
// the steering PID stays disabled; SafetyController maps angle to servo command.
// Hardware drivers map supervisor outputs to pulse widths.
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

  // PID_v1 enforces the speed sample period. Steering input is reserved.
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
