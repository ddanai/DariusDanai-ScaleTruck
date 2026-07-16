#pragma once

#include "rclcpp/rclcpp.hpp"

namespace scale_truck_control
{
namespace qos
{

inline rclcpp::QoS command()
{
  return rclcpp::QoS(rclcpp::KeepLast(1)).reliable().durability_volatile();
}

inline rclcpp::QoS feedback()
{
  return rclcpp::QoS(rclcpp::KeepLast(5)).reliable().durability_volatile();
}

inline rclcpp::QoS lane()
{
  return rclcpp::QoS(rclcpp::KeepLast(1)).best_effort().durability_volatile();
}

inline rclcpp::QoS telemetry()
{
  return rclcpp::QoS(rclcpp::KeepLast(10)).reliable().durability_volatile();
}

}  // namespace qos
}  // namespace scale_truck_control

