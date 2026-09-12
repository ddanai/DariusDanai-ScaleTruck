#pragma once

#include <Arduino.h>

namespace firmware_config {

constexpr char kFirmwareName[] = "scale-truck-teensy";
constexpr char kFirmwareVersion[] = "0.2.0";
constexpr uint32_t kSerialBaud = 115200;
constexpr uint32_t kHeartbeatPeriodMs = 3000;
constexpr uint32_t kLedTogglePeriodMs = 500;
constexpr size_t kCommandBufferSize = 64;
constexpr uint8_t kStatusLedPin = LED_BUILTIN;

// Wiring from the successful standalone tests.
constexpr uint8_t kEscPin = 9;
constexpr uint8_t kServoPin = 6;
constexpr uint8_t kEncoderAPin = 2;
constexpr uint8_t kEncoderBPin = 3;
constexpr int kEncoderSign = 1;
// Leave zero until measured: travelled metres / quadrature count change.
// Zero selects OPEN_LOOP commissioning; it must never be reported as measured m/s.
#ifndef TRUCK_ENCODER_METRES_PER_COUNT
#define TRUCK_ENCODER_METRES_PER_COUNT 0.0
#endif
constexpr double kEncoderMetresPerCount = TRUCK_ENCODER_METRES_PER_COUNT;
constexpr uint32_t kEncoderSampleMs = 20;
constexpr uint32_t kEncoderReportMs = 250;
constexpr int kEscNeutralUs = 1500;
constexpr int kEscForwardSpanUs = 500;
constexpr int kServoCenterUs = 1480;
constexpr double kServoUsPerDegree = 12.0;
constexpr int kServoDirection = 1;
constexpr uint32_t kEscStartupNeutralMs = 3000;
constexpr double kBenchSpeedLimitMps = 0.2;
constexpr double kBenchSteeringLimitDegrees = 10.0;
// There is no physical E-stop installed. ESTOP is a serial software latch.

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

// Safety envelope. Begin with restricted authority and increase only after
// bench testing. A valid command must arrive faster than the watchdog period.
constexpr uint32_t kCommandWatchdogMs = 250;
constexpr double kSafeThrottleMin = 0.0;  // Forward-only commissioning.
constexpr double kSafeThrottleMax = 0.20;
constexpr double kSafeSteeringMin = -0.25;
constexpr double kSafeSteeringMax = 0.25;
constexpr double kMaximumPlausibleSpeedMps = 15.0;
constexpr double kMaximumPlausibleSteeringDegrees = 45.0;

}  // namespace firmware_config
