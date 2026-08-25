#include <Arduino.h>

#include <cstring>

#include "firmware_config.h"

namespace {

char command_buffer[firmware_config::kCommandBufferSize] = {};
size_t command_length = 0;
uint32_t last_heartbeat_ms = 0;
uint32_t last_led_toggle_ms = 0;

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
    Serial.println(" bringup_only=1");
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
  pinMode(firmware_config::kStatusLedPin, OUTPUT);
  digitalWrite(firmware_config::kStatusLedPin, LOW);

  Serial.begin(firmware_config::kSerialBaud);

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

  if (now_ms - last_heartbeat_ms >= firmware_config::kHeartbeatPeriodMs) {
    last_heartbeat_ms = now_ms;
    Serial.print("HEARTBEAT ");
    Serial.println(now_ms);
  }
}
