#include <Arduino.h>

namespace {

constexpr uint8_t kEncoderAPin = 2;
constexpr uint8_t kEncoderBPin = 3;
constexpr uint32_t kReportPeriodMs = 250;

volatile int32_t encoder_count = 0;
volatile uint8_t encoder_state = 0;
uint32_t last_report_ms = 0;
int32_t last_report_count = 0;

void updateEncoder() {
  const uint8_t current_state =
      static_cast<uint8_t>((digitalReadFast(kEncoderAPin) << 1) |
                           digitalReadFast(kEncoderBPin));
  const uint8_t transition = static_cast<uint8_t>((encoder_state << 2) | current_state);

  switch (transition) {
    case 0b0001:
    case 0b0111:
    case 0b1110:
    case 0b1000:
      ++encoder_count;
      break;
    case 0b0010:
    case 0b1011:
    case 0b1101:
    case 0b0100:
      --encoder_count;
      break;
    default:
      break;
  }

  encoder_state = current_state;
}

void reportStatus() {
  noInterrupts();
  const int32_t current_count = encoder_count;
  interrupts();

  const int32_t change = current_count - last_report_count;
  const char* direction = change > 0 ? "FORWARD" : change < 0 ? "REVERSE" : "STOP";

  Serial.print("ENCODER count=");
  Serial.print(current_count);
  Serial.print(" delta=");
  Serial.print(change);
  Serial.print(" direction=");
  Serial.println(direction);

  last_report_count = current_count;
}

}  // namespace

void setup() {
  pinMode(kEncoderAPin, INPUT_PULLUP);
  pinMode(kEncoderBPin, INPUT_PULLUP);

  encoder_state = static_cast<uint8_t>((digitalReadFast(kEncoderAPin) << 1) |
                                       digitalReadFast(kEncoderBPin));
  attachInterrupt(digitalPinToInterrupt(kEncoderAPin), updateEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(kEncoderBPin), updateEncoder, CHANGE);

  Serial.begin(115200);
  const uint32_t serial_wait_start = millis();
  while (!Serial && millis() - serial_wait_start < 3000) {
  }

  Serial.println("MOTOR ENCODER TEST READY");
  Serial.print("A pin=");
  Serial.println(kEncoderAPin);
  Serial.print("B pin=");
  Serial.println(kEncoderBPin);
  Serial.println("Turn the motor shaft by hand; positive and negative counts indicate direction.");
}

void loop() {
  const uint32_t now_ms = millis();
  if (now_ms - last_report_ms >= kReportPeriodMs) {
    last_report_ms = now_ms;
    reportStatus();
  }
}
