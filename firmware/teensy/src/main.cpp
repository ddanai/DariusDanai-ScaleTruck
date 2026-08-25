#include <Arduino.h>

#include <cstring>

#include "firmware_config.h"
#include "pid_controllers.h"
#include "safety_controller.h"

namespace {

char command_buffer[firmware_config::kCommandBufferSize] = {};
size_t command_length = 0;
uint32_t last_heartbeat_ms = 0;
uint32_t last_led_toggle_ms = 0;
bool heartbeat_enabled = true;
PidControllers controllers;
SafetyController safety(controllers);

void printInfo() {
  Serial.print("INFO name=");
  Serial.print(firmware_config::kFirmwareName);
  Serial.print(" version=");
  Serial.print(firmware_config::kFirmwareVersion);
  Serial.print(" built=");
  Serial.print(__DATE__);
  Serial.print('T');
  Serial.println(__TIME__);
}

void handleCommand(const char* command) {
  if (std::strcmp(command, "PING") == 0) {
    Serial.println("PONG");
  } else if (std::strcmp(command, "INFO") == 0) {
    printInfo();
  } else if (std::strcmp(command, "STATUS") == 0) {
    Serial.print("STATUS uptime_ms=");
    Serial.print(millis());
    Serial.print(" safety_state=");
    Serial.print(safety.stateName());
    Serial.print(" throttle_cmd=");
    Serial.print(safety.throttleCommand(), 4);
    Serial.print(" steering_cmd=");
    Serial.print(safety.steeringCommand(), 4);
    Serial.print(" heartbeat=");
    Serial.println(heartbeat_enabled ? "ON" : "OFF");
  } else if (std::strcmp(command, "HEARTBEAT ON") == 0) {
    heartbeat_enabled = true;
    last_heartbeat_ms = millis();
    Serial.println("OK HEARTBEAT ON");
  } else if (std::strcmp(command, "HEARTBEAT OFF") == 0) {
    heartbeat_enabled = false;
    Serial.println("OK HEARTBEAT OFF");
  } else if (std::strcmp(command, "DISARM") == 0) {
    safety.disarm();
    Serial.println("OK DISARMED");
  } else if (std::strcmp(command, "ESTOP") == 0) {
    safety.setEmergencyStop(true);
    Serial.println("OK ESTOP_LATCHED");
  } else if (command[0] != '\0') {
    Serial.println("ERR UNKNOWN_COMMAND");
  }
}

void pollSerial() {
  while (Serial.available() > 0) {
    const char incoming = static_cast<char>(Serial.read());

    if (incoming == '\r') {
      continue;
    }

    if (incoming == '\n') {
      command_buffer[command_length] = '\0';
      handleCommand(command_buffer);
      command_length = 0;
      continue;
    }

    if (command_length < sizeof(command_buffer) - 1) {
      command_buffer[command_length++] = incoming;
    } else {
      command_length = 0;
      Serial.println("ERR COMMAND_TOO_LONG");
    }
  }
}

}  // namespace

void setup() {
  controllers.begin();
  safety.begin();
  pinMode(firmware_config::kStatusLedPin, OUTPUT);
  digitalWrite(firmware_config::kStatusLedPin, LOW);

  Serial.begin(firmware_config::kSerialBaud);
  const uint32_t serial_wait_start = millis();
  while (!Serial && millis() - serial_wait_start < 5000) {
  // Wait up to five seconds for the Xavier to open USB serial.
  }

  Serial.print("BOOT ");
  Serial.print(firmware_config::kFirmwareName);
  Serial.print(' ');
  Serial.println(firmware_config::kFirmwareVersion);
  Serial.println("READY");
}

void loop() {
  const uint32_t now_ms = millis();

  pollSerial();

  if (now_ms - last_led_toggle_ms >= firmware_config::kLedTogglePeriodMs) {
    last_led_toggle_ms = now_ms;
    digitalWrite(firmware_config::kStatusLedPin,
                 !digitalRead(firmware_config::kStatusLedPin));
  }

  if (heartbeat_enabled &&
      now_ms - last_heartbeat_ms >= firmware_config::kHeartbeatPeriodMs) {
    last_heartbeat_ms = now_ms;
    Serial.print("HEARTBEAT ");
    Serial.println(now_ms);
  }
}
