#include "pid_controllers.h"

#include "firmware_config.h"

PidControllers::PidControllers()
    : measured_speed_(0.0),
      throttle_command_(0.0),
      speed_target_(0.0),
      measured_steering_(0.0),
      steering_command_(0.0),
      steering_target_(0.0),
      speed_pid_(&measured_speed_, &throttle_command_, &speed_target_,
                 firmware_config::kSpeedKp, firmware_config::kSpeedKi,
                 firmware_config::kSpeedKd, P_ON_E, DIRECT),
      steering_pid_(&measured_steering_, &steering_command_, &steering_target_,
                    firmware_config::kSteeringKp,
                    firmware_config::kSteeringKi,
                    firmware_config::kSteeringKd, P_ON_E, DIRECT),
      enabled_(false) {}

void PidControllers::begin() {
  speed_pid_.SetOutputLimits(firmware_config::kThrottleMin,
                             firmware_config::kThrottleMax);
  steering_pid_.SetOutputLimits(firmware_config::kSteeringCommandMin,
                                firmware_config::kSteeringCommandMax);
  speed_pid_.SetSampleTime(firmware_config::kControlPeriodMs);
  steering_pid_.SetSampleTime(firmware_config::kControlPeriodMs);
  disable();
}

void PidControllers::enable() {
  if (!enabled_) {
    // Starting from zero gives a predictable, bumpless command when control is
    // re-enabled after a watchdog or emergency stop.
    throttle_command_ = 0.0;
    steering_command_ = 0.0;
    speed_pid_.SetMode(AUTOMATIC);
    steering_pid_.SetMode(AUTOMATIC);
    enabled_ = true;
  }
}

void PidControllers::disable() {
  speed_pid_.SetMode(MANUAL);
  steering_pid_.SetMode(MANUAL);
  throttle_command_ = 0.0;
  steering_command_ = 0.0;
  enabled_ = false;
}

bool PidControllers::enabled() const { return enabled_; }

void PidControllers::setSpeedTarget(double metres_per_second) {
  speed_target_ = metres_per_second;
}

void PidControllers::setSteeringTarget(double degrees) {
  steering_target_ = degrees;
}

void PidControllers::setSpeedTunings(double kp, double ki, double kd) {
  speed_pid_.SetTunings(kp, ki, kd, P_ON_E);
}

void PidControllers::setSteeringTunings(double kp, double ki, double kd) {
  steering_pid_.SetTunings(kp, ki, kd, P_ON_E);
}

void PidControllers::update(double measured_speed_metres_per_second,
                            double measured_steering_degrees) {
  measured_speed_ = measured_speed_metres_per_second;
  measured_steering_ = measured_steering_degrees;
  if (enabled_) {
    speed_pid_.Compute();
    steering_pid_.Compute();
  }
}

double PidControllers::throttleCommand() const { return throttle_command_; }
double PidControllers::steeringCommand() const { return steering_command_; }
double PidControllers::speedTarget() const { return speed_target_; }
double PidControllers::steeringTarget() const { return steering_target_; }
