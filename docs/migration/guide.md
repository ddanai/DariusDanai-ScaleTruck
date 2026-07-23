# ROS 1-to-ROS 2 Migration Guide

This guide documents the specific architectural and implementation changes required to migrate from ROS 1 Melodic to ROS 2 (target: Humble or Iron). It addresses the absence of ROS Master, introduction of DDS middleware, and all package/node/launch file changes.

## Humble Environment Validation Sequence

With ROS 2 Humble installed, the remaining core migration tasks should proceed in a predictable order:

1. Source the Humble environment and confirm `ros2` and `colcon` are available.
2. Build the workspace from `ros2_ws` with `colcon build --symlink-install`.
3. Run the DDS validation script from `scripts/validate_ros2_dds_discovery.sh` to confirm discovery without `roscore`.
4. Launch the bring-up packages and verify that the expected nodes and topics appear.
5. Move to the firmware bridge and control-node smoke tests once the baseline graph is healthy.

This sequence keeps the migration focused on the core runtime behavior instead of chasing package-level issues too early.

---

## Part 1: Architecture Changes Due to DDS Middleware

### ROS Master Elimination

**Change:** No `roscore` required.

| Aspect | ROS 1 (Melodic) | ROS 2 (Humble+) |
|--------|-----------------|-----------------|
| **Master process** | `roscore` must start first | No master; all nodes peer-to-peer |
| **Discovery mechanism** | Central XML-RPC registry | DDS discovery (UDP multicast by default) |
| **Node startup order** | Must wait for `roscore` | Nodes can start in any order |
| **Network requirement** | TCP/XML-RPC to master | Direct UDP multicast or configured DDS transport |
| **Launch file startup** | Explicitly start master | No master startup needed |

**Migration action:**
- Remove all `roscore` startup commands from launch files.
- Remove environment setup that waits for master.
- Nodes will discover each other automatically via DDS.

### DDS Middleware & Network Implications

**Key differences:**

1. **Default transport:** ROS 2 uses DDS with UDP multicast for discovery and communication.
2. **Network configuration:** Works automatically in most environments but may need tuning:
   - **Same machine:** Works out of the box.
   - **Ethernet LAN:** Works if multicast is enabled (common in corporate/home networks).
   - **Cloud/Docker/VPN:** May require:
     - DDS XML configuration file to enable unicast fallback or reduce multicast scope.
     - Explicit environment variables like `ROS_LOCALHOST_ONLY=1` for local-only communication.

**Migration action:**
- Assume multicast is available on your Xavier + companion machine setup.
- If Teensy is communicating via serial (not network), no DDS configuration needed for serial bridge.
- Test DDS discovery: `ros2 node list` and `ros2 topic list` should show peers without errors.

**For your deployment:**
- Xavier (main control computer) + optional companion network monitor.
- Teensy communicates only via USB serial to Xavier.
- No DDS configuration changes needed unless you add remote monitoring.

---

## Part 2: Build System Migration

### From `catkin` to `ament_cmake` / `ament_python`

The ROS 1 `scale_truck_control` package uses:
- **Build system:** `catkin`
- **Language:** C++ (roscpp), Python (rospy)

**ROS 2 approach:**
- **C++ nodes:** Use `ament_cmake`
- **Python nodes:** Use `ament_python` (simpler, preferred for scripts)

### Changes to `package.xml`

**ROS 1 `package.xml`:**
```xml
<?xml version="1.0"?>
<package format="2">
  <name>scale_truck_control</name>
  <version>0.0.1</version>
  <description>Scale truck control stack</description>
  <maintainer email="user@email.com">User Name</maintainer>
  <license>MIT</license>

  <buildtool_depend>catkin</buildtool_depend>
  <build_depend>roscpp</build_depend>
  <build_depend>rospy</build_depend>
  <build_depend>std_msgs</build_depend>
  <build_depend>sensor_msgs</build_depend>
  <build_depend>message_generation</build_depend>
  <run_depend>std_msgs</run_depend>
  <run_depend>sensor_msgs</run_depend>
  <run_depend>message_runtime</run_depend>
</package>
```

**ROS 2 `package.xml` (for mixed C++/Python):**
```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>scale_truck_control</name>
  <version>0.0.1</version>
  <description>Scale truck control stack for ROS 2</description>
  <maintainer email="user@email.com">User Name</maintainer>
  <license>MIT</license>

  <!-- For mixed C++/Python, use ament_cmake -->
  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>ament_cmake_python</buildtool_depend>

  <!-- Build dependencies -->
  <build_depend>rclcpp</build_depend>
  <build_depend>rclpy</build_depend>
  <build_depend>std_msgs</build_depend>
  <build_depend>sensor_msgs</build_depend>
  <build_depend>geometry_msgs</build_depend>
  <build_depend>rosidl_default_generators</build_depend>

  <!-- Runtime dependencies -->
  <exec_depend>rclcpp</exec_depend>
  <exec_depend>rclpy</exec_depend>
  <exec_depend>std_msgs</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>geometry_msgs</exec_depend>
  <exec_depend>rosidl_default_runtime</exec_depend>

  <!-- Optional: if using ament_cmake_python for Python nodes -->
  <exec_depend>ament_cmake_python</exec_depend>

  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>
</package>
```

**Key changes:**
- `buildtool_depend` changes from `catkin` to `ament_cmake` + `ament_cmake_python`.
- `build_depend` / `run_depend` merge into `build_depend` / `exec_depend`.
- `message_generation` → `rosidl_default_generators`.
- `message_runtime` → `rosidl_default_runtime`.
- `roscpp` → `rclcpp`.
- `rospy` → `rclpy`.

---

### Changes to `CMakeLists.txt` (For C++ Nodes)

**ROS 1 pattern:**
```cmake
cmake_minimum_required(VERSION 2.8.3)
project(scale_truck_control)

find_package(catkin REQUIRED COMPONENTS roscpp std_msgs sensor_msgs message_generation)

add_message_files(FILES
  lane.msg
  lane_coef.msg
  xav2lrc.msg
  lrc2xav.msg
  lrc2ocr.msg
  ocr2lrc.msg
)

generate_messages(DEPENDENCIES std_msgs)

catkin_package(
  INCLUDE_DIRS include
  LIBRARIES ${PROJECT_NAME}
  CATKIN_DEPENDS roscpp std_msgs
)

include_directories(include ${catkin_INCLUDE_DIRS})

add_executable(scale_truck_control_node src/control_node.cpp src/ScaleTruckController.cpp)
target_link_libraries(scale_truck_control_node ${catkin_LIBRARIES})

add_executable(lrc_node src/lrc_node.cpp src/lrc.cpp)
target_link_libraries(lrc_node ${catkin_LIBRARIES})
```

**ROS 2 pattern:**
```cmake
cmake_minimum_required(VERSION 3.8)
project(scale_truck_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Generate custom messages
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Lane.msg"
  "msg/LaneCoef.msg"
  "msg/Xav2Lrc.msg"
  "msg/Lrc2Xav.msg"
  "msg/Lrc2Ocr.msg"
  "msg/Ocr2Lrc.msg"
  DEPENDENCIES std_msgs
)

# C++ control node
add_executable(scale_truck_control_node 
  src/control_node.cpp 
  src/ScaleTruckController.cpp
)

ament_target_dependencies(scale_truck_control_node
  rclcpp
  std_msgs
  sensor_msgs
  geometry_msgs
)

rosidl_target_interfaces(scale_truck_control_node
  ${PROJECT_NAME} "rosidl_typesupport_cpp"
)

target_include_directories(scale_truck_control_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# C++ LRC node
add_executable(lrc_node
  src/lrc_node.cpp
  src/lrc.cpp
)

ament_target_dependencies(lrc_node
  rclcpp
  std_msgs
  geometry_msgs
)

rosidl_target_interfaces(lrc_node
  ${PROJECT_NAME} "rosidl_typesupport_cpp"
)

# Python serial bridge node (optional: can be C++ too)
ament_python_install_package(${PROJECT_NAME})

install(TARGETS scale_truck_control_node lrc_node
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  src/serial_bridge_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
```

**Key changes:**
- `find_package(catkin ...)` → `find_package(ament_cmake REQUIRED)` + specific `find_package()` calls.
- `add_message_files()` + `generate_messages()` → `rosidl_generate_interfaces()`.
- `catkin_package()` → `ament_package()`.
- `target_link_libraries()` → `ament_target_dependencies()` + `rosidl_target_interfaces()`.
- Install directives use `install()` instead of `catkin_install_python()`.

---

## Part 3: Node Code Changes

### C++ Node Changes: ROS Client Library

**ROS 1 includes:**
```cpp
#include "ros/ros.h"
#include "std_msgs/String.h"
#include "sensor_msgs/Image.h"
```

**ROS 2 includes:**
```cpp
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "sensor_msgs/msg/image.hpp"
```

**Node initialization:**

ROS 1:
```cpp
int main(int argc, char** argv) {
  ros::init(argc, argv, "scale_truck_control");
  ros::NodeHandle nh;
  ros::spin();
  return 0;
}
```

ROS 2:
```cpp
int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ScaleTruckController>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
```

**Class-based node (ROS 2 recommended):**

ROS 1:
```cpp
class ScaleTruckController {
private:
  ros::NodeHandle nh_;
  ros::Subscriber image_sub_;
  ros::Publisher command_pub_;
  
public:
  ScaleTruckController() {
    image_sub_ = nh_.subscribe("/usb_cam/image_raw", 1, 
                               &ScaleTruckController::imageCallback, this);
    command_pub_ = nh_.advertise<scale_truck_control::xav2lrc>("/xav2lrc_msg", 1);
  }
  
  void imageCallback(const sensor_msgs::Image::ConstPtr& msg) {
    // process image
  }
};
```

ROS 2:
```cpp
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "scale_truck_control/msg/xav2_lrc.hpp"

class ScaleTruckController : public rclcpp::Node {
private:
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Publisher<scale_truck_control::msg::Xav2Lrc>::SharedPtr command_pub_;
  
public:
  ScaleTruckController() : rclcpp::Node("scale_truck_control") {
    image_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
      "/usb_cam/image_raw", 1,
      std::bind(&ScaleTruckController::imageCallback, this, std::placeholders::_1)
    );
    
    command_pub_ = this->create_publisher<scale_truck_control::msg::Xav2Lrc>(
      "/xav2lrc_msg", 1
    );
  }
  
  void imageCallback(const sensor_msgs::msg::Image::SharedPtr msg) {
    // process image
  }
};
```

**Parameter access:**

ROS 1:
```cpp
double gain;
nh_.param("control_gain", gain, 1.0);  // default 1.0
```

ROS 2:
```cpp
this->declare_parameter("control_gain", 1.0);
double gain = this->get_parameter("control_gain").as_double();
```

---

### Python Node Changes

**ROS 1 pattern:**
```python
#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image

class MyNode:
    def __init__(self):
        rospy.init_node('my_node')
        self.sub = rospy.Subscriber('/topic', Image, self.callback)
        self.pub = rospy.Publisher('/output', String, queue_size=10)
    
    def callback(self, msg):
        # process
        pass

if __name__ == '__main__':
    node = MyNode()
    rospy.spin()
```

**ROS 2 pattern:**
```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Image

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.sub = self.create_subscription(Image, '/topic', self.callback, 10)
        self.pub = self.create_publisher(String, '/output', 10)
    
    def callback(self, msg):
        # process
        pass

def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## Part 4: Custom Message Changes

Messages must follow ROS 2 naming conventions: use CamelCase, stored in `msg/` subdirectory.

### Message File Renaming

| ROS 1 | ROS 2 |
|-------|-------|
| `msg/lane.msg` | `msg/Lane.msg` |
| `msg/lane_coef.msg` | `msg/LaneCoef.msg` |
| `msg/xav2lrc.msg` | `msg/Xav2Lrc.msg` |
| `msg/lrc2xav.msg` | `msg/Lrc2Xav.msg` |
| `msg/lrc2ocr.msg` | `msg/Lrc2Ocr.msg` |
| `msg/ocr2lrc.msg` | `msg/Ocr2Lrc.msg` |

### Message File Content (No change needed)

**ROS 1 & ROS 2 `msg/Lane.msg`:**
```
float32 a
float32 b
float32 c
```

**ROS 1 & ROS 2 `msg/LaneCoef.msg`:**
```
Lane left
Lane right
Lane center
```

### C++ Generated Code Access

**ROS 1:**
```cpp
#include "scale_truck_control/lane.h"
#include "scale_truck_control/xav2lrc.h"

scale_truck_control::lane my_lane;
scale_truck_control::xav2lrc cmd;
```

**ROS 2:**
```cpp
#include "scale_truck_control/msg/lane.hpp"
#include "scale_truck_control/msg/xav2_lrc.hpp"

scale_truck_control::msg::Lane my_lane;
scale_truck_control::msg::Xav2Lrc cmd;
```

---

## Part 5: Launch File Migration

### From XML to Python

**ROS 1 `launch/LV.launch`:**
```xml
<?xml version="1.0"?>
<launch>
  <param name="vehicle_index" value="1"/>
  <param name="zipcode" value="1"/>
  
  <node pkg="usb_cam" type="usb_cam_node" name="usb_cam">
    <param name="video_device" value="/dev/video0"/>
    <param name="pixel_format" value="yuyv"/>
    <param name="image_width" value="640"/>
    <param name="image_height" value="480"/>
    <param name="framerate" value="30"/>
  </node>
  
  <node pkg="rplidar_ros" type="rplidarNode" name="rplidarNode">
    <param name="serial_port" value="/dev/ttyUSB0"/>
    <param name="serial_baudrate" value="256000"/>
    <param name="frame_id" value="laser"/>
  </node>
  
  <node pkg="laser_filters" type="scan_to_scan_filter_chain" name="laser_filter">
    <rosparam command="load" file="$(find scale_truck_control)/config/laser_filter.yaml"/>
  </node>
  
  <node pkg="obstacle_detector" type="obstacle_extractor_node" name="obstacle_extractor"/>
  <node pkg="obstacle_detector" type="obstacle_tracker_node" name="obstacle_tracker">
    <param name="tracking_frequency" value="30"/>
  </node>
  
  <node pkg="scale_truck_control" type="scale_truck_control" name="scale_truck_control">
    <rosparam command="load" file="$(find scale_truck_control)/config/LV.yaml"/>
  </node>
  
  <node pkg="scale_truck_control" type="LRC" name="LRC"/>
  
  <node pkg="rosserial_python" type="serial_node.py" name="serial_node">
    <param name="port" value="/dev/ttyACM0"/>
    <param name="baud" value="57600"/>
  </node>
</launch>
```

**ROS 2 `launch/lv.launch.py`:**
```python
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    config_dir = PathJoinSubstitution([FindPackageShare('scale_truck_control'), 'config'])
    
    # Declare launch arguments
    vehicle_index = DeclareLaunchArgument(
        'vehicle_index',
        default_value='1',
        description='Vehicle index (1=LV, 2=FV1, 3=FV2)'
    )
    
    # Global parameters
    declare_params = [
        DeclareLaunchArgument('vehicle_index', default_value='1'),
        DeclareLaunchArgument('zipcode', default_value='1'),
    ]
    
    # USB Camera node
    usb_cam_node = Node(
        package='usb_cam',
        executable='usb_cam_node',
        name='usb_cam',
        parameters=[{
            'video_device': '/dev/video0',
            'pixel_format': 'yuyv',
            'image_width': 640,
            'image_height': 480,
            'framerate': 30.0,
        }]
    )
    
    # RPLidar node
    rplidar_node = Node(
        package='rplidar_ros',
        executable='rplidarNode',
        name='rplidarNode',
        parameters=[{
            'serial_port': '/dev/ttyUSB0',
            'serial_baudrate': 256000,
            'frame_id': 'laser',
        }]
    )
    
    # Laser filter node
    laser_filter_node = Node(
        package='laser_filters',
        executable='scan_to_scan_filter_chain',
        name='laser_filter',
        parameters=[PathJoinSubstitution([config_dir, 'laser_filter.yaml'])]
    )
    
    # Obstacle detector nodes
    obstacle_extractor_node = Node(
        package='obstacle_detector',
        executable='obstacle_extractor_node',
        name='obstacle_extractor'
    )
    
    obstacle_tracker_node = Node(
        package='obstacle_detector',
        executable='obstacle_tracker_node',
        name='obstacle_tracker',
        parameters=[{'tracking_frequency': 30}]
    )
    
    # Main control node
    scale_truck_node = Node(
        package='scale_truck_control',
        executable='scale_truck_control_node',
        name='scale_truck_control',
        parameters=[PathJoinSubstitution([config_dir, 'LV.yaml'])]
    )
    
    # LRC node
    lrc_node = Node(
        package='scale_truck_control',
        executable='lrc_node',
        name='LRC'
    )
    
    # Serial bridge node (Python, new implementation for ROS 2)
    serial_node = Node(
        package='scale_truck_control',
        executable='serial_bridge_node.py',
        name='serial_node',
        parameters=[{
            'port': '/dev/ttyACM0',
            'baud': 57600,
        }]
    )
    
    return LaunchDescription([
        *declare_params,
        usb_cam_node,
        rplidar_node,
        laser_filter_node,
        obstacle_extractor_node,
        obstacle_tracker_node,
        scale_truck_node,
        lrc_node,
        serial_node,
    ])
```

**Key launch file changes:**
- No `<launch>` wrapper; use Python functions instead.
- No XML; use Python `Node()` actions and `DeclareLaunchArgument`.
- `$(find ...)` → `FindPackageShare()`
- `<rosparam command="load">` → `parameters=[]` with file paths.
- No global `<param>` tags; use node-specific `parameters=[]`.

---

## Part 6: Dependency Migration Strategy

### External Package Replacements

| ROS 1 Package | ROS 2 Status | Migration Path |
|---------------|--------------|-----------------|
| `usb_cam` | ✅ Available in ROS 2 | Direct migration (already ported) |
| `rplidar_ros` | ⚠️ Community port | Use `ros2_rplidar` (check version compatibility) or fork the ROS 1 version |
| `laser_filters` | ✅ Available in ROS 2 | Direct migration (already ported) |
| `obstacle_detector` | ❓ No official port | Fork and port to ROS 2 (C++ node conversion required) |
| `rosserial_python` | ⚠️ Limited ROS 2 support | **See Part 7: Serial Bridge Changes** |
| `cv_bridge` | ✅ Available in ROS 2 | Direct migration; requires `python3-opencv` |
| `roscpp` / `rospy` | ✅ Renamed | Use `rclcpp` / `rclpy` (already handled above) |

### Dependency Resolution Priority

**Phase 1 (Minimal Core):**
- `usb_cam` (already ported)
- `rplidar_ros` (community port or fork)
- `laser_filters` (already ported)
- Custom C++ control node

**Phase 2 (Perception):**
- Port or fork `obstacle_detector` to ROS 2
- Build custom ROS 2 serial bridge

**Phase 3 (Integration):**
- Test all nodes together
- Verify topic communication
- Add instrumentation and telemetry

---

## Part 7: Serial Bridge Changes (Teensy Communication)

### Problem: `rosserial_python` in ROS 2

`rosserial_python` (ROS 1 bridge) has limited ROS 2 support. The Teensy/OpenCR still communicates via USB serial, but you need a **ROS 2 native serial bridge**.

### Option A: Custom Python Serial Bridge Node (Recommended for Your Use Case)

Create a simple Python node that:
1. Reads `/lrc2ocr_msg` topic (command from LRC).
2. Serializes and sends via USB to OpenCR.
3. Reads response from OpenCR.
4. Publishes `/ocr2lrc_msg` (feedback).

**File: `src/serial_bridge_node.py`**

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import serial
import struct
import threading

from scale_truck_control.msg import Lrc2Ocr, Ocr2Lrc

class SerialBridgeNode(Node):
    def __init__(self):
        super().__init__('serial_bridge_node')
        
        # Declare parameters
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baud', 57600)
        self.declare_parameter('timeout', 1.0)
        
        port = self.get_parameter('port').value
        baud = self.get_parameter('baud').value
        
        self.ser = serial.Serial(port, baud, timeout=1)
        self.get_logger().info(f"Serial port {port} opened at {baud} baud")
        
        # Subscriber to command topic
        self.cmd_sub = self.create_subscription(
            Lrc2Ocr, '/lrc2ocr_msg', self.cmd_callback, 10
        )
        
        # Publisher for feedback topic
        self.fb_pub = self.create_publisher(Ocr2Lrc, '/ocr2lrc_msg', 10)
        
        # Thread for reading responses
        self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.read_thread.start()
    
    def cmd_callback(self, msg):
        """Serialize command message and send to OpenCR."""
        try:
            # Pack the command message into bytes
            # Format depends on your OpenCR firmware protocol
            cmd_bytes = struct.pack('<hhhhhhB',
                msg.index,
                int(msg.steer_angle * 100),  # scale angle
                int(msg.cur_dist * 100),
                int(msg.tar_dist * 100),
                int(msg.tar_vel * 100),
                int(msg.pred_vel * 100),
                1 if msg.alpha else 0
            )
            
            self.ser.write(cmd_bytes)
            self.get_logger().debug(f"Sent command: {msg}")
        except Exception as e:
            self.get_logger().error(f"Error sending command: {e}")
    
    def read_loop(self):
        """Continuously read feedback from OpenCR."""
        while rclpy.ok():
            try:
                if self.ser.in_waiting >= 10:  # Adjust size for your feedback packet
                    data = self.ser.read(10)
                    
                    # Unpack feedback message
                    fb_msg = Ocr2Lrc()
                    fb_msg.cur_vel = struct.unpack('<h', data[0:2])[0] / 100.0
                    fb_msg.sat_vel = struct.unpack('<h', data[2:4])[0] / 100.0
                    # Add other fields as needed
                    
                    self.fb_pub.publish(fb_msg)
                    self.get_logger().debug(f"Received feedback: {fb_msg}")
            except Exception as e:
                self.get_logger().error(f"Error reading feedback: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = SerialBridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**Migration action:**
- Keep OpenCR firmware **unchanged** (it communicates via serial protocol, not ROS).
- Implement a new Python serial bridge node in ROS 2.
- Adjust serialization format to match your OpenCR protocol.

### Option B: micro-ROS (Advanced Alternative)

If you want the Teensy/OpenCR to behave like a true ROS 2 node:
- Compile micro-ROS on the Teensy.
- OpenCR subscribes/publishes directly to ROS 2 topics over a dedicated serial transport layer.
- More complex; recommended only if you need full ROS 2 integration on the microcontroller.

**For Scaletruck, Option A (custom Python bridge) is simpler and sufficient.**

---

## Part 8: Parameter Handling

### Configuration File Format (No Change)

YAML files remain the same syntax between ROS 1 and ROS 2.

**ROS 1 & ROS 2 `config/LV.yaml`:**
```yaml
vehicle_index: 1
zipcode: 1

control:
  steering_gain: 0.5
  velocity_gain: 1.0
  
camera:
  calibration_file: "calibration.yaml"
  roi_x: 0
  roi_y: 0
  roi_width: 640
  roi_height: 480

lidar:
  filter_range: 2.62  # radians
```

### C++ Parameter Access Changes

**ROS 1:**
```cpp
ros::NodeHandle nh;
double gain;
nh.param("control/steering_gain", gain, 0.5);  // default 0.5
```

**ROS 2:**
```cpp
this->declare_parameter("control.steering_gain", 0.5);
double gain = this->get_parameter("control.steering_gain").as_double();
```

### Python Parameter Access Changes

**ROS 1:**
```python
import rospy
gain = rospy.get_param("control/steering_gain", 0.5)
```

**ROS 2:**
```python
from rclpy.node import Node

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.declare_parameter('control.steering_gain', 0.5)
        gain = self.get_parameter('control.steering_gain').value
```

---

## Part 9: Testing and Validation

### Topic Discovery Verification

**ROS 1:**
```bash
rostopic list  # requires roscore running
```

**ROS 2:**
```bash
ros2 topic list  # no master required; uses DDS discovery
ros2 node list
```

### Testing the DDS Middleware

1. **Same machine test:**
   ```bash
   # Terminal 1
   ros2 run scale_truck_control scale_truck_control_node
   
   # Terminal 2
   ros2 topic list
   # Should see /xav2lrc_msg, /usb_cam/image_raw, etc.
   ```

2. **Network test (if remote monitoring is added later):**
   ```bash
   ROS_DOMAIN_ID=42 ros2 run scale_truck_control scale_truck_control_node
   # Both machines should use the same DOMAIN_ID to discover each other
   ```

### Serial Bridge Testing

```bash
# Terminal 1: Launch ROS 2 stack
ros2 launch scale_truck_control lv.launch.py

# Terminal 2: Monitor serial communication
ros2 topic echo /ocr2lrc_msg
# Should see feedback messages from Teensy

# Terminal 3: Publish test command
ros2 topic pub /lrc2ocr_msg scale_truck_control/msg/Lrc2Ocr "{index: 1, steer_angle: 0.1, tar_vel: 0.5}"
```

---

## Part 10: Build System Validation

### Workspace Layout (ROS 2)

```
ros2_ws/
├── src/
│   └── scale_truck_control/
│       ├── CMakeLists.txt          (updated for ament_cmake)
│       ├── package.xml             (updated for ROS 2)
│       ├── include/
│       │   └── scale_truck_control/
│       │       ├── ScaleTruckController.h
│       │       └── lrc.h
│       ├── src/
│       │   ├── control_node.cpp    (updated for rclcpp)
│       │   ├── ScaleTruckController.cpp
│       │   ├── lrc_node.cpp        (updated for rclcpp)
│       │   ├── lrc.cpp
│       │   └── serial_bridge_node.py  (new Python bridge)
│       ├── msg/
│       │   ├── Lane.msg
│       │   ├── LaneCoef.msg
│       │   ├── Xav2Lrc.msg
│       │   ├── Lrc2Xav.msg
│       │   ├── Lrc2Ocr.msg
│       │   └── Ocr2Lrc.msg
│       ├── launch/
│       │   ├── lv.launch.py        (converted from LV.launch)
│       │   ├── fv1.launch.py       (converted from FV1.launch)
│       │   └── fv2.launch.py       (converted from FV2.launch)
│       └── config/
│           ├── LV.yaml
│           ├── FV1.yaml
│           ├── FV2.yaml
│           └── laser_filter.yaml
```

### Build Command

```bash
cd ros2_ws
colcon build --packages-select scale_truck_control
source install/setup.bash
```

---

## Part 11: Dependency Porting Checklist

### Must Implement / Port

- [ ] `scale_truck_control` main node → ROS 2 C++ (rclcpp)
- [ ] `LRC` node → ROS 2 C++ (rclcpp)
- [ ] Custom serial bridge node → ROS 2 Python (rclpy)
- [ ] All custom messages → ROS 2 IDL format
- [ ] Launch files → Python launch files
- [ ] Configuration files → Keep as YAML (no change needed)

### Already Available in ROS 2

- [ ] `usb_cam`
- [ ] `laser_filters`
- [ ] `cv_bridge`
- [ ] Message types: `std_msgs`, `sensor_msgs`, `geometry_msgs`

### Need Community Port or Fork

- [ ] `rplidar_ros` → Find/use `ros2_rplidar` community port
- [ ] `obstacle_detector` → Fork and port to ROS 2 C++

---

## Summary of Changes

| Category | ROS 1 | ROS 2 | Action |
|----------|-------|-------|--------|
| **Startup** | `roscore` required | No master | Remove master startup |
| **Discovery** | XML-RPC registry | DDS multicast | Automatic in LAN; configure if needed |
| **Build system** | catkin | ament_cmake / ament_python | Update CMakeLists.txt, package.xml |
| **C++ library** | roscpp | rclcpp | Update includes, node class |
| **Python library** | rospy | rclpy | Update imports, node class |
| **Messages** | lowercase.msg | CamelCase.msg | Rename files, update C++ includes |
| **Launch** | XML | Python | New .launch.py files |
| **Serial bridge** | rosserial_python | Custom ROS 2 node | New serial_bridge_node.py |
| **OpenCR firmware** | N/A | Unchanged | Serial protocol stays the same |
| **Parameters** | ros::param | rclcpp::Node::declare/get_parameter | Update C++ and Python code |

