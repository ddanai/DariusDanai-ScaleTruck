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

Complete this section after creating and inspecting the rosbag2 conversion.

| Property | Expected value | Recorded value |
|---|---|---|
| Converted directly from the verified ROS 1 bag | Yes | Pending |
| Source ROS 1 SHA-256 recorded above | Match | Pending |
| Image topic | `/sensors/camera/left/image_raw` | Pending |
| Message type | `sensor_msgs/msg/Image` | Pending |
| Image count | 540 | Pending |
| Bag duration | Approximately 18.0 seconds | Pending |
| Approximate image rate | 30 Hz | Pending |
| Image height | 1216 pixels | Pending |
| Image width | 1936 pixels | Pending |
| Image encoding | `bayer_rggb8` | Pending |
| Row step | 1936 bytes | Pending |
| Playback rate | 1.0 | Pending |

## Pilot-run verification

Complete after ROS 1 pilot 90 and ROS 2 pilot 90.

| Check | ROS 1 | ROS 2 |
|---|---|---|
| Run completed | Pending | Pending |
| Workload version `fnv1a-strided-v1` | Pending | Pending |
| Workload passes `8` | Pending | Pending |
| Nonzero matched traces | Pending | Pending |
| No negative latency | Pending | Pending |
| Resource samples recorded | Pending | Pending |
| Controller commands equivalent for corresponding frames | Pending | Pending |

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
