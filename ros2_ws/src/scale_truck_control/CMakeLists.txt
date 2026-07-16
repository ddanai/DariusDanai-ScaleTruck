cmake_minimum_required(VERSION 3.8)
project(scale_truck_control)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(scale_truck_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

add_library(${PROJECT_NAME}_support
  src/ScaleTruckController.cpp
  src/lrc.cpp
  src/sock_udp.cpp
)

target_include_directories(${PROJECT_NAME}_support PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(${PROJECT_NAME}_support
  rclcpp
  scale_truck_msgs
  sensor_msgs
)

add_executable(scale_truck_control_node
  src/control_node.cpp
)

target_link_libraries(scale_truck_control_node
  ${PROJECT_NAME}_support
)

ament_target_dependencies(scale_truck_control_node
  rclcpp
)

add_executable(lrc_node
  src/lrc_node.cpp
)

target_link_libraries(lrc_node
  ${PROJECT_NAME}_support
)

ament_target_dependencies(lrc_node
  rclcpp
)

install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY
  include/
  DESTINATION include
)

ament_export_include_directories(include)
ament_export_dependencies(rclcpp scale_truck_msgs sensor_msgs)
ament_export_targets(${PROJECT_NAME}_targets HAS_LIBRARY_TARGET)

install(TARGETS
  ${PROJECT_NAME}_support
  EXPORT ${PROJECT_NAME}_targets
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(EXPORT
  ${PROJECT_NAME}_targets
  DESTINATION share/${PROJECT_NAME}/cmake
)

install(TARGETS
  scale_truck_control_node
  lrc_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
