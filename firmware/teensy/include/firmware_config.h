#pragma once

#include <Arduino.h>

namespace firmware_config {

constexpr char kFirmwareName[] = "scale-truck-teensy";
constexpr char kFirmwareVersion[] = "0.1.0";
constexpr uint32_t kSerialBaud = 115200;
constexpr uint32_t kHeartbeatPeriodMs = 1000;
constexpr uint32_t kLedTogglePeriodMs = 500;
constexpr size_t kCommandBufferSize = 64;
constexpr uint8_t kStatusLedPin = LED_BUILTIN;

}  // namespace firmware_config
