#pragma once

#include <cstdint>
#include <chrono>
#include <mutex>
#include <string>

#include "builtin_interfaces/msg/time.hpp"
#include "rclcpp/rclcpp.hpp"
#include "scale_truck_msgs/msg/lane_coef.hpp"
#include "scale_truck_msgs/msg/lrc2_xav.hpp"
#include "scale_truck_msgs/msg/xav2_lrc.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

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
  void scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg);
  void velocity_callback(const scale_truck_msgs::msg::Lrc2Xav::SharedPtr msg);
  void update();
  void publish_control();

  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
  rclcpp::Subscription<scale_truck_msgs::msg::Lrc2Xav>::SharedPtr velocity_sub_;
  rclcpp::Publisher<scale_truck_msgs::msg::Xav2Lrc>::SharedPtr command_pub_;
  rclcpp::Publisher<scale_truck_msgs::msg::LaneCoef>::SharedPtr lane_pub_;
  rclcpp::TimerBase::SharedPtr timer_;

  std::mutex state_mutex_;

  bool image_seen_{false};
  bool scan_seen_{false};
  std::chrono::steady_clock::time_point scan_received_{};
  double scan_header_age_{0.0};
  double scan_timeout_s_{0.3};
  double front_center_rad_{0.0};
  double front_half_width_rad_{0.2617993878};
  double distance_gain_{0.5};
  uint64_t latest_trace_id_{0};
  builtin_interfaces::msg::Time latest_sensor_stamp_{};
  bool enable_console_output_{true};
  bool beta_{false};
  bool gamma_{false};
  double update_period_s_{0.02};
  float angle_degree_{0.0f};
  float target_vel_{0.0f};
  float result_vel_{0.0f};
  float current_vel_{0.0f};
  float target_dist_{0.8f};
  float current_dist_{0.0f};
  float lv_stop_dist_{0.5f};
};

}  // namespace scale_truck_control

