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

## ROS 1 Reference Architecture

```mermaid
flowchart LR
    Camera["USB camera (/usb_cam/image_raw)"] --> Xavier["scale_truck_control"]
    Lidar["RPLidar A3 (/scan)"] --> Filter["laser_filter"]
    Filter --> Obstacles["obstacle_detector (/tracked_obstacles)"]
    Obstacles --> Xavier
    ZMQ["ZeroMQ command/coordination"] --> Xavier
    Xavier --> Lane["/lane_msg"]
    Xavier --> Xav2Lrc["/xav2lrc_msg"]
    Ocr2Lrc["/ocr2lrc_msg"] --> LRC["LRC"]
    Xav2Lrc --> LRC
    LRC --> Lrc2Xav["/lrc2xav_msg"]
    Lrc2Xav --> Xavier
    LRC --> Lrc2Ocr["/lrc2ocr_msg"]
    Lrc2Ocr --> Rosserial["rosserial_python"]
    Rosserial --> OpenCR["OpenCR firmware"]
    OpenCR --> Rosserial
    LRC <--> Multicast["UDP multicast resiliency data"]
    Controller["Qt Controller UI"] --> Multicast
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
