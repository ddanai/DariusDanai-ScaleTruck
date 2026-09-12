"""Start sensors, control nodes, and the Teensy bridge for integration testing."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "vehicle_config",
            default_value=PathJoinSubstitution([
                FindPackageShare("scale_truck_bringup"), "config", "closed_loop_test.yaml"
            ]),
            description="Distance-test controller configuration.",
        ),
        DeclareLaunchArgument(
            "use_control", default_value="true", choices=["true", "false"],
            description="Start control/LRC command publishers; disable for manual command tests.",
        ),
        LogInfo(msg=(
            "Teensy integration launch: sensors and USB commands enabled. "
            "LiDAR distance control enabled; physical actuation still requires "
            "integrated actuator/feedback firmware. No automatic arming."
        )),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare("scale_truck_bringup"), "launch", "vehicle.launch.py"
            ])),
            launch_arguments={
                "vehicle_config": LaunchConfiguration("vehicle_config"),
                "use_control": LaunchConfiguration("use_control"),
                "commands_enabled": "true",
                "use_camera": "true",
                "use_lidar": "true",
                "use_laser_filter": "false",
                "use_obstacles": "false",
                "use_firmware_bridge": "true",
            }.items(),
        ),
    ])
