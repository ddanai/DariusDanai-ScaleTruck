#include <cassert>
#include <iostream>
#include "../../src/main.cpp"

int main() {
  static_assert(firmware_config::kEncoderMetresPerCount == 0.001, "Test calibration required");
  setup();
  fake_ms = 3001;
  loop();
  fake_ms += 20;
  loop();
  assert(hardware.speed() == 0.0);
  handleCommand("ARM");
  handleCommand("CMD 0.2 0");
  assert(hardware.escPulse() == 1550);
  // Four counts in 20 ms at 0.001 m/count measures 0.2 m/s.
  pins[3] = 0; handlers[3]();
  pins[2] = 0; handlers[2]();
  pins[3] = 1; handlers[3]();
  pins[2] = 1; handlers[2]();
  fake_ms += 20; loop();
  assert(std::abs(hardware.speed() - 0.2) < 1e-9);
  assert(hardware.escPulse() == 1500);
  // A long sampling gap invalidates feedback and latches a sensor fault.
  fake_ms += 101; loop();
  assert(safety.state() == SafetyState::kSensorFault);
  assert(hardware.escPulse() == 1500);
  std::cout << "PASS calibrated speed feedback and sensor-fault neutral\n";
}
