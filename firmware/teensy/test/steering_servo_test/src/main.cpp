#include <Arduino.h>
#include <Servo.h>

// Temporary, unloaded steering-servo bench test.
// Servo signal: Teensy pin 6
// Initial test range: 1430--1530 us around the historical 1480 us center.

namespace {

constexpr uint8_t kServoPin = 6;
constexpr int kCenterPulseUs = 1480;
constexpr int kLeftPulseUs = 1380;
constexpr int kRightPulseUs = 1580;
constexpr uint32_t kCommandTimeoutMs = 2000;

Servo steering_servo;
uint32_t last_command_ms = 0;
bool command_active = false;
String command_buffer;

void commandPulse(const int pulse_us, const char* name) {
  steering_servo.writeMicroseconds(pulse_us);
  last_command_ms = millis();
  command_active = pulse_us != kCenterPulseUs;

  Serial.print("OK ");
  Serial.print(name);
  Serial.print(" pulse_us=");
  Serial.println(pulse_us);
}

void printHelp() {
  Serial.println("Commands: CENTER, LEFT, RIGHT, STATUS, HELP");
  Serial.println("LEFT/RIGHT return to CENTER after 2 seconds.");
}

void handleCommand(String command) {
  command.trim();
  command.toUpperCase();

  if (command == "CENTER") {
    commandPulse(kCenterPulseUs, "CENTER");
  } else if (command == "LEFT") {
    commandPulse(kLeftPulseUs, "LEFT");
  } else if (command == "RIGHT") {
    commandPulse(kRightPulseUs, "RIGHT");
  } else if (command == "STATUS") {
    Serial.print("STATUS pin=");
    Serial.print(kServoPin);
    Serial.print(" pulse_us=");
    Serial.println(steering_servo.readMicroseconds());
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

  // Establish the center command before attaching the output pin, avoiding a
  // startup pulse at an arbitrary position.
  steering_servo.writeMicroseconds(kCenterPulseUs);
  steering_servo.attach(kServoPin);

  const uint32_t serial_wait_start = millis();
  while (!Serial && millis() - serial_wait_start < 3000) {
  }

  Serial.println("STEERING SERVO TEST READY");
  Serial.print("pin=6 center_us=");
  Serial.print(kCenterPulseUs);
  Serial.print(" left_us=");
  Serial.print(kLeftPulseUs);
  Serial.print(" right_us=");
  Serial.println(kRightPulseUs);
  printHelp();
}

void loop() {
  pollSerial();

  if (command_active && millis() - last_command_ms >= kCommandTimeoutMs) {
    commandPulse(kCenterPulseUs, "AUTO_CENTER");
  }
}
