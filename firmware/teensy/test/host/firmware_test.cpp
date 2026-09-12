#include <cassert>
#include <iostream>
#include "../../src/main.cpp"

void send(const std::string& line) {
  Serial.output.clear();
  for (char c : line + "\n") Serial.input.push_back(c);
  while (Serial.available()) loop();
}
void active() { send("CLEAR"); send("ARM"); assert(safety.state() == SafetyState::kArmed); }
void neutral() { assert(pulses[9] == 1500); assert(pulses[6] == 1480); }

int main() {
  setup();
  neutral();
  send("ARM");
  assert(Serial.output.find("STARTUP_NEUTRAL") != std::string::npos);
  send("CMD 0.1 5");
  neutral();
  fake_ms = 3001;
  active();
  send("CMD 0.1 5");
  assert(pulses[9] == 1550 && pulses[6] == 1540);
  send("CMD 0.2 -10");
  assert(pulses[9] == 1600 && pulses[6] == 1360);
  send("CMD 0 0"); neutral();
  send("CMD 0 10");
  assert(pulses[9] == 1500 && pulses[6] == 1600);
  fake_ms += 251; loop(); neutral();
  assert(safety.state() == SafetyState::kWatchdogFault);
  send("DISARM"); send("ARM");
  assert(safety.state() == SafetyState::kWatchdogFault);
  active(); send("CMD -0.1 0"); neutral();
  assert(safety.state() == SafetyState::kCommandFault);
  active(); send("CMD 0.21 0"); neutral();
  active(); send("CMD 0.1 11"); neutral();
  active(); send("CMD nan 0"); neutral();
  active(); send("CMD 0.1 0 trailing"); neutral();
  active(); send("CMD 0.1"); neutral();
  active(); send("CMD 0.1 5");
  send("ESTOP"); neutral();
  send("DISARM"); send("ARM");
  assert(safety.state() == SafetyState::kEmergencyStop);
  active(); send("CMD 0.1 5");
  send(std::string(80, 'x') + "ARM"); neutral();
  assert(safety.state() == SafetyState::kDisarmed);
  active(); send(std::string("CMD 0.1\0 5", 10)); neutral();
  active(); send("CMD 0.1 5");
  Serial.connected = false; loop(); neutral();
  Serial.connected = true;
  active(); send("CMD 0.1 5");
  Serial.capacity = 0; fake_ms += 251; loop(); neutral();
  Serial.capacity = 4096;
  send("FEEDBACK 1 1");
  assert(Serial.output.find("SIMULATED_FEEDBACK_DISABLED") != std::string::npos);
  // Four real interrupt transitions produce four signed quadrature counts.
  pins[3] = 0; handlers[3]();
  pins[2] = 0; handlers[2]();
  pins[3] = 1; handlers[3]();
  pins[2] = 1; handlers[2]();
  assert(hardware.count() == 4);
  pins[2] = 0; handlers[2]();
  pins[3] = 0; handlers[3]();
  pins[2] = 1; handlers[2]();
  pins[3] = 1; handlers[3]();
  assert(hardware.count() == 0);
  assert(std::isnan(hardware.speed()));
  send("STATUS");
  assert(Serial.output.find("actuators=ENABLED mode=OPEN_LOOP") != std::string::npos);
  assert(countDelta(-2147483647 - 1, 2147483647) == 1);
  assert(countDelta(2147483647, -2147483647 - 1) == -1);
  assert(boundedPulse(999, 0, .2, 1500, 500) == 1600);
  assert(boundedPulse(-999, 0, .2, 1500, 500) == 1500);
  assert(boundedPulse(std::numeric_limits<double>::quiet_NaN(), 0, .2, 1500, 500) == 1500);
  std::cout << "PASS firmware commands, outputs, safety, parser, encoder and rollover checks\n";
}
