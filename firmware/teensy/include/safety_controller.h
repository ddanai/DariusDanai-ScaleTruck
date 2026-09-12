#pragma once

#include <Arduino.h>

#include "pid_controllers.h"

enum class SafetyState : uint8_t {
  kDisarmed,
  kArmed,
  kActive,
  kEmergencyStop,
  kWatchdogFault,
  kCommandFault,
  kSensorFault,
};

// Supervises throttle and steering. Only the commands returned by this class may be
// sent to actuator drivers; raw PID outputs bypass the safety envelope.
class SafetyController {
 public:
  explicit SafetyController(PidControllers& controllers);

  void begin();
  bool arm(uint32_t now_ms);
  void disarm();

  // The emergency stop is level-sensitive and latched. Once asserted, it must
  // be released and clearFaults() must be called before arming. Main currently
  // supplies a software latch; there is no physical E-stop on this truck.
  void setEmergencyStop(bool asserted);
  bool clearFaults();

  // Records one validated command packet from the supervisory computer.
  // Returns false if the values are invalid or safety is not armed.
  bool acceptCommand(double speed_target_mps,
                     double steering_target_degrees,
                     uint32_t now_ms);

  // Call every loop with the latest feedback and E-stop state already
  // supplied through setEmergencyStop().
  void update(double measured_speed_mps, uint32_t now_ms);

  SafetyState state() const;
  const char* stateName() const;
  bool mayDrive() const;
  double throttleCommand() const;
  double steeringCommand() const;

 private:
  void enterFault(SafetyState fault);
  void forceNeutral();
  bool sensorsValid(double speed_mps) const;
  static double clamp(double value, double minimum, double maximum);

  PidControllers& controllers_;
  SafetyState state_;
  bool emergency_stop_asserted_;
  bool command_received_;
  uint32_t last_command_ms_;
  double safe_throttle_command_;
  double safe_steering_command_;
};
