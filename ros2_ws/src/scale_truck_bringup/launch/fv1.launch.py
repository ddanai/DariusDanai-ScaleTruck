from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare("scale_truck_bringup")

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([bringup_share, "launch", "vehicle.launch.py"])
            ),
            launch_arguments={
                "vehicle_config": PathJoinSubstitution([bringup_share, "config", "fv1.yaml"]),
            }.items(),
        )
    ])

