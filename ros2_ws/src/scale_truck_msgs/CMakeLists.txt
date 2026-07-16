cmake_minimum_required(VERSION 3.8)
project(scale_truck_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Lane.msg"
  "msg/LaneCoef.msg"
  "msg/Xav2Lrc.msg"
  "msg/Lrc2Xav.msg"
  "msg/Lrc2Ocr.msg"
  "msg/Ocr2Lrc.msg"
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
