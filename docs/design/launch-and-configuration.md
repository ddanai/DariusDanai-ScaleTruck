# ROS 2 Launch and Configuration

This note records the first ROS 2 launch/config migration from the ROS 1 reference launch files.

## Migrated Launch Files

| ROS 1 Launch | ROS 2 Launch |
|--------------|--------------|
| `launch/LV.launch` | `ros2_ws/src/scale_truck_bringup/launch/lv.launch.py` |
| `launch/FV1.launch` | `ros2_ws/src/scale_truck_bringup/launch/fv1.launch.py` |
| `launch/FV2.launch` | `ros2_ws/src/scale_truck_bringup/launch/fv2.launch.py` |

The shared ROS 2 launch logic lives in:

```text
ros2_ws/src/scale_truck_bringup/launch/vehicle.launch.py
```

## Migrated Runtime Config

| ROS 1 Config | ROS 2 Config |
|--------------|--------------|
| `config/LV.yaml` + shared config | `ros2_ws/src/scale_truck_bringup/config/lv.yaml` |
| `config/FV1.yaml` + shared config | `ros2_ws/src/scale_truck_bringup/config/fv1.yaml` |
| `config/FV2.yaml` + shared config | `ros2_ws/src/scale_truck_bringup/config/fv2.yaml` |
| `config/laser_filter.yaml` | `ros2_ws/src/scale_truck_bringup/config/laser_filter.yaml` |
| sensor/perception params from launch XML | `ros2_ws/src/scale_truck_bringup/config/sensors.yaml` |
| ROS 1 `rosserial_python` params | `ros2_ws/src/scale_truck_bringup/config/serial_bridge.yaml` |

## Launch Defaults

The default launch path starts only the migrated ROS 2 control and LRC nodes:

```bash
ros2 launch scale_truck_bringup lv.launch.py
```

Hardware and perception dependencies are disabled by default until their migration tasks are complete:

```bash
ros2 launch scale_truck_bringup lv.launch.py use_camera:=true use_lidar:=true
ros2 launch scale_truck_bringup lv.launch.py use_obstacles:=true
ros2 launch scale_truck_bringup lv.launch.py use_firmware_bridge:=true
```

## Namespaces and Remapping

The migrated config uses relative topic names so launch namespaces and remappings work correctly. For example, this starts the leader under the `lv` namespace:

```bash
ros2 launch scale_truck_bringup lv.launch.py namespace:=lv
```

Common topics can be remapped at launch:

```bash
ros2 launch scale_truck_bringup lv.launch.py \
  xav2lrc_topic:=/xav2lrc_msg \
  lrc2xav_topic:=/lrc2xav_msg \
  lrc2ocr_topic:=/lrc2ocr_msg \
  ocr2lrc_topic:=/ocr2lrc_msg
```

## Notes

- ROS 1 `<rosparam>` blocks were converted to ROS 2 `ros__parameters` YAML.
- ROS 1 `rosserial_python` is not launched. It is replaced by `scale_truck_firmware_bridge/serial_bridge_node` and `serial_bridge.yaml`.
- Driver package/executable names are launch arguments so they can be corrected when dependency migration chooses final ROS 2 drivers.
- The lane-camera-specific ROS 1 launch files are not converted yet; they should be handled with the broader camera/perception migration.
