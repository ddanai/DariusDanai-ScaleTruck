from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_share = FindPackageShare("scale_truck_bringup")
    config_dir = PathJoinSubstitution([bringup_share, "config"])

    vehicle_config = LaunchConfiguration("vehicle_config")
    sensor_config = LaunchConfiguration("sensor_config")
    laser_filter_config = LaunchConfiguration("laser_filter_config")
    serial_bridge_config = LaunchConfiguration("serial_bridge_config")

    use_camera = LaunchConfiguration("use_camera")
    use_lidar = LaunchConfiguration("use_lidar")
    use_laser_filter = LaunchConfiguration("use_laser_filter")
    use_obstacles = LaunchConfiguration("use_obstacles")
    use_firmware_bridge = LaunchConfiguration("use_firmware_bridge")

    return LaunchDescription([
        DeclareLaunchArgument(
            "vehicle_config",
            default_value=PathJoinSubstitution([config_dir, "lv.yaml"]),
            description="Vehicle-specific ROS 2 parameter file.",
        ),
        DeclareLaunchArgument(
            "sensor_config",
            default_value=PathJoinSubstitution([config_dir, "sensors.yaml"]),
            description="Sensor and perception parameter file.",
        ),
        DeclareLaunchArgument(
            "laser_filter_config",
            default_value=PathJoinSubstitution([config_dir, "laser_filter.yaml"]),
            description="Laser filter parameter file.",
        ),
        DeclareLaunchArgument(
            "serial_bridge_config",
            default_value=PathJoinSubstitution([config_dir, "serial_bridge.yaml"]),
            description="Firmware bridge parameter file.",
        ),
        DeclareLaunchArgument("use_camera", default_value="false"),
        DeclareLaunchArgument("use_lidar", default_value="false"),
        DeclareLaunchArgument("use_laser_filter", default_value="false"),
        DeclareLaunchArgument("use_obstacles", default_value="false"),
        DeclareLaunchArgument("use_firmware_bridge", default_value="false"),
        DeclareLaunchArgument("camera_package", default_value="usb_cam"),
        DeclareLaunchArgument("camera_executable", default_value="usb_cam_node_exe"),
        DeclareLaunchArgument("lidar_package", default_value="rplidar_ros"),
        DeclareLaunchArgument("lidar_executable", default_value="rplidarNode"),
        DeclareLaunchArgument("firmware_bridge_package", default_value="scale_truck_firmware_bridge"),
        DeclareLaunchArgument("firmware_bridge_executable", default_value="serial_bridge_node"),

        Node(
            package="scale_truck_control",
            executable="scale_truck_control_node",
            name="scale_truck_control_node",
            output="screen",
            parameters=[vehicle_config],
        ),
        Node(
            package="scale_truck_control",
            executable="lrc_node",
            name="lrc_node",
            output="screen",
            parameters=[vehicle_config],
        ),
        Node(
            package=LaunchConfiguration("camera_package"),
            executable=LaunchConfiguration("camera_executable"),
            name="usb_cam",
            output="screen",
            parameters=[sensor_config],
            condition=IfCondition(use_camera),
        ),
        Node(
            package=LaunchConfiguration("lidar_package"),
            executable=LaunchConfiguration("lidar_executable"),
            name="rplidar_node",
            output="screen",
            parameters=[sensor_config],
            condition=IfCondition(use_lidar),
        ),
        Node(
            package="laser_filters",
            executable="scan_to_scan_filter_chain",
            name="laser_filter",
            output="screen",
            parameters=[laser_filter_config],
            condition=IfCondition(use_laser_filter),
        ),
        Node(
            package="obstacle_detector",
            executable="obstacle_extractor_node",
            name="obstacle_extractor",
            output="screen",
            parameters=[sensor_config],
            remappings=[("scan", "scan_filtered")],
            condition=IfCondition(use_obstacles),
        ),
        Node(
            package="obstacle_detector",
            executable="obstacle_tracker_node",
            name="obstacle_tracker",
            output="screen",
            parameters=[sensor_config],
            remappings=[("scan", "scan_filtered")],
            condition=IfCondition(use_obstacles),
        ),
        Node(
            package=LaunchConfiguration("firmware_bridge_package"),
            executable=LaunchConfiguration("firmware_bridge_executable"),
            name="serial_bridge_node",
            output="screen",
            parameters=[serial_bridge_config],
            condition=IfCondition(use_firmware_bridge),
        ),
    ])

