#include <Arduino.h>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <limits>

#include "firmware_config.h"
#include "hardware_math.h"
#include "pid_controllers.h"
#include "safety_controller.h"
#include "truck_hardware.h"

namespace {
char command_buffer[firmware_config::kCommandBufferSize] = {};
size_t command_length = 0;
bool discard_line = false;
bool heartbeat_enabled = true;
bool software_estop = false;
uint32_t boot_ms = 0;
uint32_t last_heartbeat_ms = 0;
uint32_t last_led_ms = 0;
uint32_t last_report_ms = 0;
int32_t last_report_count = 0;
PidControllers controllers;
SafetyController safety(controllers);
TruckHardware hardware;

const char* modeName() {
  return firmware_config::kEncoderMetresPerCount > 0.0 ? "SPEED_PID" : "OPEN_LOOP";
}

// Never let serial backpressure delay neutral/watchdog processing. A saturated
// link may drop diagnostics; command acceptance is never inferred from silence.
void reply(const char* text) {
  const size_t length = std::strlen(text);
  if (Serial && Serial.availableForWrite() >= static_cast<int>(length + 1)) {
    Serial.write(reinterpret_cast<const uint8_t*>(text), length);
    Serial.write('\n');
  }
}

void applySafety() {
  const uint32_t now = millis();
  hardware.sample(now);
  safety.setEmergencyStop(software_estop);
  if (!Serial && (safety.mayDrive() || safety.state() == SafetyState::kArmed))
    safety.disarm();
  safety.update(hardware.speed(), now);
  hardware.writeOutputs(safety.throttleCommand(), safety.steeringCommand());
}

void printStatus() {
  char line[320];
  std::snprintf(line, sizeof(line),
    "STATUS uptime_ms=%lu safety_state=%s throttle_cmd=%.4f steering_cmd=%.4f heartbeat=%s "
    "actuators=ENABLED mode=%s encoder_count=%ld speed_mps=%.5f esc_us=%d servo_us=%d",
    static_cast<unsigned long>(millis()), safety.stateName(), safety.throttleCommand(),
    safety.steeringCommand(), heartbeat_enabled ? "ON" : "OFF", modeName(),
    static_cast<long>(hardware.count()), hardware.speed(), hardware.escPulse(), hardware.servoPulse());
  reply(line);
}

void handleCommand(const char* command) {
  if (std::strcmp(command, "PING") == 0) {
    reply("PONG");
  } else if (std::strcmp(command, "INFO") == 0) {
    char line[160];
    std::snprintf(line, sizeof(line), "INFO name=%s version=%s actuators=ENABLED mode=%s",
      firmware_config::kFirmwareName, firmware_config::kFirmwareVersion, modeName());
    reply(line);
  } else if (std::strcmp(command, "STATUS") == 0) {
    printStatus();
  } else if (std::strcmp(command, "HEARTBEAT ON") == 0) {
    heartbeat_enabled = true;
    reply("OK HEARTBEAT ON");
  } else if (std::strcmp(command, "HEARTBEAT OFF") == 0) {
    heartbeat_enabled = false;
    reply("OK HEARTBEAT OFF");
  } else if (std::strcmp(command, "ARM") == 0) {
    if (millis() - boot_ms < firmware_config::kEscStartupNeutralMs) {
      reply("ERR ARM_REJECTED STARTUP_NEUTRAL");
    } else {
      reply(safety.arm(millis()) ? "OK ARMED" : "ERR ARM_REJECTED");
    }
  } else if (std::strcmp(command, "CLEAR") == 0) {
    // Explicit operator release of the software latch; no physical E-stop exists.
    software_estop = false;
    safety.setEmergencyStop(false);
    safety.clearFaults();
    applySafety();
    reply("OK FAULTS_CLEARED");
  } else if (std::strcmp(command, "DISARM") == 0) {
    safety.disarm();
    applySafety();
    reply("OK DISARMED");
  } else if (std::strcmp(command, "ESTOP") == 0) {
    software_estop = true;
    applySafety();
    reply("OK ESTOP_LATCHED");
  } else if (std::strncmp(command, "CMD", 3) == 0) {
    double speed = 0.0, angle = 0.0;
    char trailing = '\0';
    const bool parsed = std::sscanf(command, "CMD %lf %lf %c", &speed, &angle, &trailing) == 2;
    if (!parsed) speed = angle = std::numeric_limits<double>::quiet_NaN();
    const bool accepted = safety.acceptCommand(speed, angle, millis());
    applySafety();
    reply(accepted ? "OK COMMAND_ACCEPTED" : "ERR COMMAND_REJECTED");
  } else if (std::strncmp(command, "FEEDBACK", 8) == 0) {
    reply("ERR SIMULATED_FEEDBACK_DISABLED");
  } else if (command[0]) {
    reply("ERR UNKNOWN_COMMAND");
  }
}

void pollSerial() {
  // Bound work per loop so a continuous sender cannot starve the watchdog.
  for (size_t i = 0; i < firmware_config::kCommandBufferSize && Serial.available(); ++i) {
    const char incoming = static_cast<char>(Serial.read());
    if (incoming == '\r') continue;
    if (incoming == '\n') {
      if (!discard_line) {
        command_buffer[command_length] = '\0';
        handleCommand(command_buffer);
      }
      command_length = 0;
      discard_line = false;
    } else if (!discard_line) {
      if (incoming == '\0' || command_length >= sizeof(command_buffer) - 1) {
        discard_line = true;
        command_length = 0;
        safety.disarm();
        applySafety();
        reply("ERR MALFORMED_OR_TOO_LONG");
      } else {
        command_buffer[command_length++] = incoming;
      }
    }
  }
}
}  // namespace

void setup() {
  hardware.begin();  // Establish neutral outputs before serial initialization.
  controllers.begin();
  safety.begin();
  boot_ms = millis();
  pinMode(firmware_config::kStatusLedPin, OUTPUT);
  Serial.begin(firmware_config::kSerialBaud);
}

void loop() {
  applySafety();
  pollSerial();
  applySafety();
  const uint32_t now = millis();
  if (now - last_led_ms >= firmware_config::kLedTogglePeriodMs) {
    last_led_ms = now;
    digitalWrite(firmware_config::kStatusLedPin, !digitalRead(firmware_config::kStatusLedPin));
  }
  if (now - last_report_ms >= firmware_config::kEncoderReportMs) {
    last_report_ms = now;
    const int32_t count = hardware.count();
    const int32_t delta = countDelta(count, last_report_count);
    last_report_count = count;
    char line[128];
    std::snprintf(line, sizeof(line), "ENCODER count=%ld delta=%ld direction=%s",
      static_cast<long>(count), static_cast<long>(delta),
      delta > 0 ? "FORWARD" : delta < 0 ? "REVERSE" : "STOP");
    reply(line);
  }
  if (heartbeat_enabled && now - last_heartbeat_ms >= firmware_config::kHeartbeatPeriodMs) {
    last_heartbeat_ms = now;
    char line[64];
    std::snprintf(line, sizeof(line), "HEARTBEAT %lu", static_cast<unsigned long>(now));
    reply(line);
  }
}
