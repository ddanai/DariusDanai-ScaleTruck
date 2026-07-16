#include "rclcpp/rclcpp.hpp"
#include "scale_truck_control/ScaleTruckController.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<scale_truck_control::ScaleTruckController>());
  rclcpp::shutdown();
  return 0;
}

