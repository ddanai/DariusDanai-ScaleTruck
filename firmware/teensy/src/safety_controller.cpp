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
  if (emergency_stop_asserted_) state_ = SafetyState::kEmergencyStop;
  else if (state_ == SafetyState::kActive || state_ == SafetyState::kArmed)
    state_ = SafetyState::kDisarmed;
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
      speed_target_mps < 0.0 || speed_target_mps > firmware_config::kBenchSpeedLimitMps ||
      std::fabs(steering_target_degrees) >
          firmware_config::kBenchSteeringLimitDegrees) {
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
                              uint32_t now_ms) {
  if (emergency_stop_asserted_) {
    enterFault(SafetyState::kEmergencyStop);
    return;
  }
  if (state_ != SafetyState::kArmed && state_ != SafetyState::kActive) {
    forceNeutral();
    return;
  }
  if (firmware_config::kEncoderMetresPerCount > 0.0 && !sensorsValid(measured_speed_mps)) {
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

  if (controllers_.speedTarget() == 0.0) {
    // A stop must command neutral, never reverse or retain PID integral output.
    controllers_.disable();
    safe_throttle_command_ = 0.0;
  } else if (firmware_config::kEncoderMetresPerCount > 0.0) {
    controllers_.enable();
    controllers_.update(measured_speed_mps, 0.0);
    safe_throttle_command_ = clamp(controllers_.throttleCommand(),
        firmware_config::kSafeThrottleMin, firmware_config::kSafeThrottleMax);
  } else {
    // Uncalibrated commissioning: the speed field is only a throttle request.
    controllers_.disable();
    safe_throttle_command_ = firmware_config::kSafeThrottleMax *
        controllers_.speedTarget() / firmware_config::kBenchSpeedLimitMps;
  }
  // RC servo handles its own internal position loop. No external angle sensor
  // is installed, so do not run a steering PID against fabricated feedback.
  safe_steering_command_ = clamp(controllers_.steeringTarget() /
      firmware_config::kBenchSteeringLimitDegrees * firmware_config::kSafeSteeringMax,
      firmware_config::kSafeSteeringMin, firmware_config::kSafeSteeringMax);
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

bool SafetyController::sensorsValid(double speed_mps) const {
  return std::isfinite(speed_mps) &&
         std::fabs(speed_mps) <= firmware_config::kMaximumPlausibleSpeedMps;
}

double SafetyController::clamp(double value, double minimum, double maximum) {
  if (value < minimum) return minimum;
  if (value > maximum) return maximum;
  return value;
}
