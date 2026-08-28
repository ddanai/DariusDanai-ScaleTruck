#include <Arduino.h>

#include <cstdio>
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
double simulated_speed_mps = 0.0;
double simulated_steering_degrees = 0.0;

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
  } else if (std::strcmp(command, "ARM") == 0) {
    if (safety.arm(millis())) {
      Serial.println("OK ARMED");
    } else {
      Serial.print("ERR ARM_REJECTED state=");
      Serial.println(safety.stateName());
    }
  } else if (std::strcmp(command, "CLEAR") == 0) {
    // Software-only bring-up: simulate releasing the physical E-stop before
    // clearing a latched fault. Replace this with the real input later.
    safety.setEmergencyStop(false);
    if (safety.clearFaults()) {
      Serial.println("OK FAULTS_CLEARED");
    } else {
      Serial.print("ERR CLEAR_REJECTED state=");
      Serial.println(safety.stateName());
    }
  } else if (std::strcmp(command, "DISARM") == 0) {
    safety.disarm();
    Serial.println("OK DISARMED");
  } else if (std::strcmp(command, "ESTOP") == 0) {
    safety.setEmergencyStop(true);
    Serial.println("OK ESTOP_LATCHED");
  } else {
    double first_value = 0.0;
    double second_value = 0.0;
    char trailing_character = '\0';

    if (std::sscanf(command, "FEEDBACK %lf %lf %c", &first_value,
                    &second_value, &trailing_character) == 2) {
      simulated_speed_mps = first_value;
      simulated_steering_degrees = second_value;
      Serial.print("OK FEEDBACK speed=");
      Serial.print(simulated_speed_mps, 4);
      Serial.print(" steering=");
      Serial.println(simulated_steering_degrees, 4);
    } else if (std::sscanf(command, "CMD %lf %lf %c", &first_value,
                           &second_value, &trailing_character) == 2) {
      if (safety.acceptCommand(first_value, second_value, millis())) {
        Serial.println("OK COMMAND_ACCEPTED");
      } else {
        Serial.print("ERR COMMAND_REJECTED state=");
        Serial.println(safety.stateName());
      }
    } else if (command[0] != '\0') {
      Serial.println("ERR UNKNOWN_COMMAND");
    }
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
  pollSerial();

  const uint32_t now_ms = millis();
  safety.update(simulated_speed_mps, simulated_steering_degrees, now_ms);

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
