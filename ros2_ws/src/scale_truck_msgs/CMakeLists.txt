cmake_minimum_required(VERSION 3.8)
project(scale_truck_msgs)

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Lane.msg"
  "msg/LaneCoef.msg"
  "msg/Xav2Lrc.msg"
  "msg/Lrc2Xav.msg"
  "msg/Lrc2Ocr.msg"
  "msg/Ocr2Lrc.msg"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(builtin_interfaces rosidl_default_runtime)

ament_package()
