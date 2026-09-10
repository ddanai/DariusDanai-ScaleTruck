"""Camera, LiDAR and encoder feedback with Teensy command sending disabled."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare("scale_truck_bringup"), "launch", "vehicle.launch.py"
            ])),
            launch_arguments={
                "use_control": "false",
                "commands_enabled": "false",
                "use_camera": "true",
                "use_lidar": "true",
                "use_firmware_bridge": "true",
            }.items(),
        ),
    ])
