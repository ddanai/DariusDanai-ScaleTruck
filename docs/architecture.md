# System Architecture

## Target Architecture

```mermaid
flowchart LR
    Operator["Operator / Test Script"] --> ROS2["ROS 2 Control Stack"]
    Sensors["Camera / LiDAR / IMU / Encoders"] --> ROS2
    ROS2 --> Bridge["Teensy Serial Bridge"]
    Bridge --> Teensy["Teensy PID Firmware"]
    Teensy --> Actuators["Steering / Throttle / Brake"]
    Teensy --> Bridge
    ROS2 --> Telemetry["ADDT Telemetry Interface"]
    Telemetry --> ADDT["Autonomous Driving Digital Twin"]
```

## Main Interfaces

- High-level commands: velocity, steering, stop/go, emergency stop.
- Low-level serial commands: throttle setpoint, steering setpoint, watchdog heartbeat.
- Feedback: encoder speed, steering state, battery or fault status, sensor measurements.
- Digital twin telemetry: pose, velocity, commands, sensor status, test-run metadata.

## Week 1 Architecture Tasks

- Replace placeholder boxes with package and node names after ROS 1 inventory is complete.
- Add topic names, message types, and expected publish rates.
- Document failure paths for communication loss and emergency stop.

