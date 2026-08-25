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

// Initial, deliberately conservative controller settings. These values must be
// tuned on the actual truck. Units are m/s for speed and degrees for steering.
constexpr uint32_t kControlPeriodMs = 20;

constexpr double kSpeedKp = 0.5;
constexpr double kSpeedKi = 0.0;
constexpr double kSpeedKd = 0.0;
constexpr double kThrottleMin = -1.0;
constexpr double kThrottleMax = 1.0;

constexpr double kSteeringKp = 0.5;
constexpr double kSteeringKi = 0.0;
constexpr double kSteeringKd = 0.0;
constexpr double kSteeringCommandMin = -1.0;
constexpr double kSteeringCommandMax = 1.0;

}  // namespace firmware_config
