#include <Arduino.h>
#include <Servo.h>

// Temporary TBLE-02S bench test. Raise the driven wheels before use.
// Connect only the ESC signal and ground to the Teensy. Leave the ESC's red
// 6 V BEC wire disconnected and insulated while Teensy is powered by USB.

namespace {

constexpr uint8_t kEscSignalPin = 9;
constexpr int kNeutralPulseUs = 1500;
constexpr int kRunPulseUs = 1600;
constexpr uint32_t kRunTimeoutMs = 1000;

Servo motor_esc;
String command_buffer;
bool armed = false;
bool run_active = false;
uint32_t run_started_ms = 0;

void setNeutral(const char* reason) {
  motor_esc.writeMicroseconds(kNeutralPulseUs);
  run_active = false;

  Serial.print("OK ");
  Serial.print(reason);
  Serial.print(" pulse_us=");
  Serial.println(kNeutralPulseUs);
}

void printStatus() {
  Serial.print("STATUS pin=");
  Serial.print(kEscSignalPin);
  Serial.print(" state=");
  Serial.print(armed ? "ARMED" : "DISARMED");
  Serial.print(" run_active=");
  Serial.print(run_active ? "YES" : "NO");
  Serial.print(" pulse_us=");
  Serial.println(motor_esc.readMicroseconds());
}

void printHelp() {
  Serial.println("Commands: STATUS, ARM, RUN, STOP, DISARM, HELP");
  Serial.println("RUN applies 1550 us for 1 second, then returns to neutral.");
  Serial.println("Reverse is disabled in this test firmware.");
}

void handleCommand(String command) {
  command.trim();
  command.toUpperCase();

  if (command == "STATUS") {
    printStatus();
  } else if (command == "ARM") {
    setNeutral("NEUTRAL");
    armed = true;
    Serial.println("OK ARMED");
  } else if (command == "RUN") {
    if (!armed) {
      Serial.println("ERR DISARMED; enter ARM first");
      return;
    }

    motor_esc.writeMicroseconds(kRunPulseUs);
    run_started_ms = millis();
    run_active = true;
    Serial.print("OK RUN pulse_us=");
    Serial.println(kRunPulseUs);
  } else if (command == "STOP") {
    setNeutral("STOPPED");
  } else if (command == "DISARM") {
    setNeutral("NEUTRAL");
    armed = false;
    Serial.println("OK DISARMED");
  } else if (command == "HELP" || command.length() == 0) {
    printHelp();
  } else {
    Serial.println("ERR unknown command");
    printHelp();
  }
}

void pollSerial() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());

    if (incoming == '\n') {
      handleCommand(command_buffer);
      command_buffer = "";
    } else if (incoming != '\r') {
      command_buffer += incoming;
    }
  }
}

}  // namespace

void setup() {
  Serial.begin(115200);

  motor_esc.attach(kEscSignalPin);
  motor_esc.writeMicroseconds(kNeutralPulseUs);

  const uint32_t serial_wait_start = millis();
  while (!Serial && millis() - serial_wait_start < 3000) {
  }

  Serial.println("TBLE-02S MOTOR TEST READY");
  Serial.print("pin=9 neutral_us=");
  Serial.print(kNeutralPulseUs);
  Serial.print(" run_us=");
  Serial.print(kRunPulseUs);
  Serial.print(" timeout_ms=");
  Serial.println(kRunTimeoutMs);
  printHelp();
}

void loop() {
  pollSerial();

  if (run_active && millis() - run_started_ms >= kRunTimeoutMs) {
    setNeutral("AUTO_NEUTRAL");
  }
}
