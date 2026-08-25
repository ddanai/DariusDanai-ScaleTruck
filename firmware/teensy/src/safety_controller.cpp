#include "safety_controller.h"

#include <cmath>

#include "firmware_config.h"

SafetyController::SafetyController(PidControllers& controllers)
    : controllers_(controllers),
      state_(SafetyState::kDisarmed),
      emergency_stop_asserted_(false),
      command_received_(false),
      last_command_ms_(0),
      safe_throttle_command_(0.0),
      safe_steering_command_(0.0) {}

void SafetyController::begin() {
  controllers_.disable();
  state_ = SafetyState::kDisarmed;
  emergency_stop_asserted_ = false;
  command_received_ = false;
  forceNeutral();
}

bool SafetyController::arm(uint32_t now_ms) {
  if (emergency_stop_asserted_ || state_ == SafetyState::kEmergencyStop ||
      state_ == SafetyState::kWatchdogFault ||
      state_ == SafetyState::kCommandFault ||
      state_ == SafetyState::kSensorFault) {
    return false;
  }

  controllers_.disable();
  command_received_ = false;
  last_command_ms_ = now_ms;
  state_ = SafetyState::kArmed;
  forceNeutral();
  return true;
}

void SafetyController::disarm() {
  controllers_.disable();
  command_received_ = false;
  state_ = emergency_stop_asserted_ ? SafetyState::kEmergencyStop
                                    : SafetyState::kDisarmed;
  forceNeutral();
}

void SafetyController::setEmergencyStop(bool asserted) {
  emergency_stop_asserted_ = asserted;
  if (asserted) {
    enterFault(SafetyState::kEmergencyStop);
  }
}

bool SafetyController::clearFaults() {
  if (emergency_stop_asserted_) {
    return false;
  }
  controllers_.disable();
  command_received_ = false;
  state_ = SafetyState::kDisarmed;
  forceNeutral();
  return true;
}

bool SafetyController::acceptCommand(double speed_target_mps,
                                     double steering_target_degrees,
                                     uint32_t now_ms) {
  if (state_ != SafetyState::kArmed && state_ != SafetyState::kActive) {
    return false;
  }
  if (!std::isfinite(speed_target_mps) ||
      !std::isfinite(steering_target_degrees) ||
      std::fabs(speed_target_mps) >
          firmware_config::kMaximumPlausibleSpeedMps ||
      std::fabs(steering_target_degrees) >
          firmware_config::kMaximumPlausibleSteeringDegrees) {
    enterFault(SafetyState::kCommandFault);
    return false;
  }

  controllers_.setSpeedTarget(speed_target_mps);
  controllers_.setSteeringTarget(steering_target_degrees);
  last_command_ms_ = now_ms;
  command_received_ = true;
  if (state_ == SafetyState::kArmed) {
    controllers_.enable();
    state_ = SafetyState::kActive;
  }
  return true;
}

void SafetyController::update(double measured_speed_mps,
                              double measured_steering_degrees,
                              uint32_t now_ms) {
  if (emergency_stop_asserted_) {
    enterFault(SafetyState::kEmergencyStop);
    return;
  }
  if (state_ != SafetyState::kArmed && state_ != SafetyState::kActive) {
    forceNeutral();
    return;
  }
  if (!sensorsValid(measured_speed_mps, measured_steering_degrees)) {
    enterFault(SafetyState::kSensorFault);
    return;
  }
  if (command_received_ &&
      now_ms - last_command_ms_ > firmware_config::kCommandWatchdogMs) {
    enterFault(SafetyState::kWatchdogFault);
    return;
  }
  if (state_ != SafetyState::kActive) {
    forceNeutral();
    return;
  }

  controllers_.update(measured_speed_mps, measured_steering_degrees);
  safe_throttle_command_ =
      clamp(controllers_.throttleCommand(), firmware_config::kSafeThrottleMin,
            firmware_config::kSafeThrottleMax);
  safe_steering_command_ =
      clamp(controllers_.steeringCommand(), firmware_config::kSafeSteeringMin,
            firmware_config::kSafeSteeringMax);
}

SafetyState SafetyController::state() const { return state_; }

const char* SafetyController::stateName() const {
  switch (state_) {
    case SafetyState::kDisarmed: return "DISARMED";
    case SafetyState::kArmed: return "ARMED";
    case SafetyState::kActive: return "ACTIVE";
    case SafetyState::kEmergencyStop: return "ESTOP";
    case SafetyState::kWatchdogFault: return "WATCHDOG_FAULT";
    case SafetyState::kCommandFault: return "COMMAND_FAULT";
    case SafetyState::kSensorFault: return "SENSOR_FAULT";
  }
  return "UNKNOWN";
}

bool SafetyController::mayDrive() const {
  return state_ == SafetyState::kActive;
}

double SafetyController::throttleCommand() const {
  return safe_throttle_command_;
}

double SafetyController::steeringCommand() const {
  return safe_steering_command_;
}

void SafetyController::enterFault(SafetyState fault) {
  controllers_.disable();
  command_received_ = false;
  state_ = fault;
  forceNeutral();
}

void SafetyController::forceNeutral() {
  safe_throttle_command_ = 0.0;
  safe_steering_command_ = 0.0;
}

bool SafetyController::sensorsValid(double speed_mps,
                                    double steering_degrees) const {
  return std::isfinite(speed_mps) && std::isfinite(steering_degrees) &&
         std::fabs(speed_mps) <= firmware_config::kMaximumPlausibleSpeedMps &&
         std::fabs(steering_degrees) <=
             firmware_config::kMaximumPlausibleSteeringDegrees;
}

double SafetyController::clamp(double value, double minimum, double maximum) {
  if (value < minimum) return minimum;
  if (value > maximum) return maximum;
  return value;
}
