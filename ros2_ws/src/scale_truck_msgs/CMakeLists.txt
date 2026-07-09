cmake_minimum_required(VERSION 3.8)
project(scale_truck_msgs)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  action
  msg
  srv
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

