#pragma once

#include <mutex>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "scale_truck_msgs/msg/lane_coef.hpp"
#include "scale_truck_msgs/msg/lrc2_xav.hpp"
#include "scale_truck_msgs/msg/xav2_lrc.hpp"
#include "sensor_msgs/msg/image.hpp"

namespace scale_truck_control
{

class ScaleTruckController : public rclcpp::Node
{
public:
  ScaleTruckController();

private:
  void load_parameters();
  void init_ros_interfaces();
  void image_callback(const sensor_msgs::msg::Image::SharedPtr msg);
  void velocity_callback(const scale_truck_msgs::msg::Lrc2Xav::SharedPtr msg);
  void update();
  void publish_control();

  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Subscription<scale_truck_msgs::msg::Lrc2Xav>::SharedPtr velocity_sub_;
  rclcpp::Publisher<scale_truck_msgs::msg::Xav2Lrc>::SharedPtr command_pub_;
  rclcpp::Publisher<scale_truck_msgs::msg::LaneCoef>::SharedPtr lane_pub_;
  rclcpp::TimerBase::SharedPtr timer_;

  std::mutex state_mutex_;

  bool image_seen_{false};
  bool enable_console_output_{true};
  bool beta_{false};
  bool gamma_{false};
  double update_period_s_{0.02};
  float angle_degree_{0.0f};
  float target_vel_{0.5f};
  float safety_vel_{0.3f};
  float result_vel_{0.0f};
  float current_vel_{0.0f};
  float target_dist_{0.8f};
  float current_dist_{10.0f};
  float lv_stop_dist_{0.5f};
  float safety_dist_{1.5f};
};

}  // namespace scale_truck_control

