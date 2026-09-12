#include "truck_hardware.h"
#include "firmware_config.h"
#include "hardware_math.h"
#include <limits>

namespace {
volatile uint32_t encoder_count = 0;
volatile uint8_t encoder_state = 0;

void encoderInterrupt() {
  const uint8_t current = (digitalReadFast(firmware_config::kEncoderAPin) << 1) |
    digitalReadFast(firmware_config::kEncoderBPin);
  const uint8_t transition = (encoder_state << 2) | current;
  switch (transition) {
    case 0b0001: case 0b0111: case 0b1110: case 0b1000:
      encoder_count += firmware_config::kEncoderSign;
      break;
    case 0b0010: case 0b1011: case 0b1101: case 0b0100:
      encoder_count -= firmware_config::kEncoderSign;
      break;
    default: break;
  }
  encoder_state = current;
}
uint32_t snapshot() {
  noInterrupts();
  const uint32_t value = encoder_count;
  interrupts();
  return value;
}
}  // namespace

void TruckHardware::begin() {
  using namespace firmware_config;
  static_assert(kEncoderSign == 1 || kEncoderSign == -1, "Encoder sign must be +/-1");
  static_assert(kServoDirection == 1 || kServoDirection == -1, "Servo sign must be +/-1");
  static_assert(kEncoderMetresPerCount >= 0.0, "Invalid encoder calibration");
  esc_.attach(kEscPin);
  servo_.attach(kServoPin);
  writeOutputs(0.0, 0.0);
  pinMode(kEncoderAPin, INPUT_PULLUP);
  pinMode(kEncoderBPin, INPUT_PULLUP);
  encoder_state = (digitalReadFast(kEncoderAPin) << 1) | digitalReadFast(kEncoderBPin);
  attachInterrupt(digitalPinToInterrupt(kEncoderAPin), encoderInterrupt, CHANGE);
  attachInterrupt(digitalPinToInterrupt(kEncoderBPin), encoderInterrupt, CHANGE);
  sample_ms_ = millis();
  speed_mps_ = std::numeric_limits<double>::quiet_NaN();
}

int32_t TruckHardware::count() const { return signedCount(snapshot()); }

void TruckHardware::sample(uint32_t now_ms) {
  const uint32_t elapsed = now_ms - sample_ms_;
  if (elapsed < firmware_config::kEncoderSampleMs) return;
  const uint32_t current = snapshot();
  const int32_t delta = signedCount(current - sample_count_);
  speed_mps_ = firmware_config::kEncoderMetresPerCount > 0.0 && elapsed <= 100 ?
    delta * firmware_config::kEncoderMetresPerCount * 1000.0 / elapsed :
    std::numeric_limits<double>::quiet_NaN();
  sample_count_ = current;
  sample_ms_ = now_ms;
}

void TruckHardware::writeOutputs(double throttle, double steering) {
  using namespace firmware_config;
  esc_pulse_ = boundedPulse(throttle, kSafeThrottleMin, kSafeThrottleMax,
    kEscNeutralUs, kEscForwardSpanUs);
  servo_pulse_ = boundedPulse(steering, kSafeSteeringMin, kSafeSteeringMax,
    kServoCenterUs, kServoDirection * kBenchSteeringLimitDegrees *
    kServoUsPerDegree / kSafeSteeringMax);
  esc_.writeMicroseconds(esc_pulse_);
  servo_.writeMicroseconds(servo_pulse_);
}
