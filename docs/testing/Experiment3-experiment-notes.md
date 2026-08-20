# Experiment 3: experiment notes

## ROS 1 source bag verification

Verified on the Xavier before the matched-workload comparison.

| Property | Recorded value |
|---|---|
| Bag path on Xavier | `/home/krg/left_camera_templergraben.bag` |
| SHA-256 | `cce3dfa34d42a7e0278638ce9557e83fb66c6784c383e37c58892a511d01812b` |
| Image topic | `/sensors/camera/left/image_raw` |
| Message type | `sensor_msgs/Image` |
| Image count | 540 |
| Bag duration | 18.0 seconds |
| Approximate image rate | 30 Hz |
| Image height | 1216 pixels |
| Image width | 1936 pixels |
| Image encoding | `bayer_rggb8` |
| Row step | 1936 bytes |

### First inspected image message

| Property | Recorded value |
|---|---|
| Sequence | 34267 |
| Timestamp | 1565341141.827898224 |
| Frame ID | `left_optical` |

Verification commands:

```bash
rosbag info ~/left_camera_templergraben.bag
rostopic echo -b ~/left_camera_templergraben.bag -n 1 \
  /sensors/camera/left/image_raw/header
rostopic echo -b ~/left_camera_templergraben.bag -n 1 \
  /sensors/camera/left/image_raw | grep -E "height:|width:|encoding:|step:"
sha256sum ~/left_camera_templergraben.bag
```

## ROS 2 conversion verification

An existing rosbag2 conversion was found in the shared Xavier workspace and inspected inside the
`ros2-humble` container with `ros2 bag info`.

| Bag property | Recorded value |
|---|---|
| Path inside ROS 2 container | `/ros2_ws/bags/left_camera_templergraben_ros2` |
| Database file | `left_camera_templergraben_ros2.db3` |
| Bag size | 1.2 GiB |
| Storage ID | `sqlite3` |
| Serialization format | `cdr` |
| Duration | 17.978476936 seconds |
| Start timestamp | 1565341141.833875233 |
| End timestamp | 1565341159.812352169 |
| Total messages | 540 |

| Property | Expected value | Recorded value |
|---|---|---|
| Converted directly from the verified ROS 1 bag | Yes | Existing Experiment 2 conversion; provenance documented, pilot confirmation pending |
| Source ROS 1 SHA-256 recorded above | Match | Source checksum now recorded; historical conversion checksum linkage not independently recorded |
| Image topic | `/sensors/camera/left/image_raw` | `/sensors/camera/left/image_raw` |
| Message type | `sensor_msgs/msg/Image` | `sensor_msgs/msg/Image` |
| Image count | 540 | 540 |
| Bag duration | Approximately 18.0 seconds | 17.978476936 seconds |
| Approximate image rate | 30 Hz | Approximately 30.04 Hz |
| Image height | 1216 pixels | Pending |
| Image width | 1936 pixels | Pending |
| Image encoding | `bayer_rggb8` | Pending |
| Row step | 1936 bytes | Pending |
| Playback rate | 1.0 | Pending |

The ROS 1 and ROS 2 metadata match for topic, message count, message type, duration, and approximate
rate. Image fields and corresponding workload outputs will be confirmed during the pilot before the
bag is accepted for official runs.

## Pilot-run verification

Validated using ROS 2 pilot 94 and ROS 1 pilot 96. Earlier pilot IDs were diagnostic runs rejected
because they exposed recorder, analysis-window, discovery, or disk-threshold problems.

The accepted protocol uses a one-second warm-up after the first nonzero controller trace and a
five-second measurement window. The analyzer requires at least 4.5 seconds of observed controller
activity.

| Check | ROS 1 | ROS 2 |
|---|---|---|
| Run completed | Yes (run 96) | Yes (run 94) |
| Workload version `fnv1a-strided-v1` | Confirmed | Confirmed |
| Workload passes `4` | Confirmed | Confirmed |
| Nonzero matched traces | 117 | 114 |
| No negative latency | Confirmed | Confirmed |
| Complete observed controller span | 4.986 s | 4.951 s |
| Controller frequency | 23.27 Hz | 22.82 Hz |
| Actuator frequency | 23.27 Hz | 22.87 Hz |
| Resource samples recorded | Confirmed | Confirmed |
| Shared controller computation | Same `matched_controller_workload.py` implementation | Same `matched_controller_workload.py` implementation |

## Official run record

Record acceptance or rejection immediately after each run. Never reject a run solely because it is
slow.

| Sequence | System | Run ID | Accepted? | Reason if rejected | Notes |
|---:|---|---:|---|---|---|
| 1 | ROS 1 | 01 | Pending |  |  |
| 2 | ROS 2 | 01 | Pending |  |  |
| 3 | ROS 2 | 02 | Pending |  |  |
| 4 | ROS 1 | 02 | Pending |  |  |
| 5 | ROS 1 | 03 | Pending |  |  |
| 6 | ROS 2 | 03 | Pending |  |  |
| 7 | ROS 2 | 04 | Pending |  |  |
| 8 | ROS 1 | 04 | Pending |  |  |
| 9 | ROS 1 | 05 | Pending |  |  |
| 10 | ROS 2 | 05 | Pending |  |  |
| 11 | ROS 2 | 06 | Pending |  |  |
| 12 | ROS 1 | 06 | Pending |  |  |
| 13 | ROS 1 | 07 | Pending |  |  |
| 14 | ROS 2 | 07 | Pending |  |  |
| 15 | ROS 2 | 08 | Pending |  |  |
| 16 | ROS 1 | 08 | Pending |  |  |
| 17 | ROS 1 | 09 | Pending |  |  |
| 18 | ROS 2 | 09 | Pending |  |  |
| 19 | ROS 2 | 10 | Pending |  |  |
| 20 | ROS 1 | 10 | Pending |  |  |
