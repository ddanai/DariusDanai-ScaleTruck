#include "scale_truck_control/ScaleTruckController.hpp"

#include <algorithm>
#include <chrono>
#include <functional>
#include <cmath>
#include <stdexcept>

#include "scale_truck_control/qos.hpp"
#include "scale_truck_control/distance_control.hpp"

namespace scale_truck_control
{

ScaleTruckController::ScaleTruckController()
: rclcpp::Node("scale_truck_control_node")
{
  load_parameters();
  init_ros_interfaces();
}

void ScaleTruckController::load_parameters()
{
  enable_console_output_ = this->declare_parameter<bool>(
    "image_view.enable_console_output", true);
  target_vel_ = static_cast<float>(this->declare_parameter<double>("params.target_vel", 0.0));
  lv_stop_dist_ = static_cast<float>(this->declare_parameter<double>("params.lv_stop_dist", 0.5));
  target_dist_ = static_cast<float>(this->declare_parameter<double>("params.target_dist", 0.8));
  update_period_s_ = this->declare_parameter<double>("params.update_period_s", 0.02);
  scan_timeout_s_ = this->declare_parameter<double>("closed_loop.scan_timeout_s", 0.3);
  front_center_rad_ = this->declare_parameter<double>("closed_loop.front_center_rad", 0.0);
  front_half_width_rad_ = this->declare_parameter<double>(
    "closed_loop.front_half_width_rad", 0.2617993878);
  distance_gain_ = this->declare_parameter<double>("closed_loop.distance_gain", 0.5);
  if (!std::isfinite(target_vel_) || target_vel_ < 0.0f || target_vel_ > 0.2f ||
    !std::isfinite(lv_stop_dist_) || lv_stop_dist_ <= 0.0f ||
    !std::isfinite(target_dist_) || target_dist_ < lv_stop_dist_ ||
    !std::isfinite(update_period_s_) || update_period_s_ < 0.001 || update_period_s_ > 0.1 ||
    !std::isfinite(scan_timeout_s_) || scan_timeout_s_ <= 0.0 || scan_timeout_s_ > 1.0 ||
    !std::isfinite(front_center_rad_) || !std::isfinite(front_half_width_rad_) ||
    front_half_width_rad_ <= 0.0 || front_half_width_rad_ > 1.5707963268 ||
    !std::isfinite(distance_gain_) || distance_gain_ <= 0.0)
  {
    throw std::invalid_argument(
      "Invalid distance-test settings: speed 0..0.2 m/s, gap >= positive stop distance, "
      "period 0.001..0.1 s, timeout 0..1 s, sector half-width 0..pi/2, positive gain");
  }
}

void ScaleTruckController::init_ros_interfaces()
{
  const auto image_topic = this->declare_parameter<std::string>(
    "topics.camera_reading", "usb_cam/image_raw");
  const auto velocity_topic = this->declare_parameter<std::string>(
    "topics.lrc_to_xavier", "lrc2xav_msg");
  const auto lane_topic = this->declare_parameter<std::string>(
    "topics.lane_coef", "lane_msg");
  const auto command_topic = this->declare_parameter<std::string>(
    "topics.xavier_to_lrc", "xav2lrc_msg");
  const auto scan_topic = this->declare_parameter<std::string>("topics.scan", "scan");

  scan_sub_ = this->create_subscription<sensor_msgs::msg::LaserScan>(
    scan_topic, rclcpp::SensorDataQoS(),
    std::bind(&ScaleTruckController::scan_callback, this, std::placeholders::_1));

  image_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
    image_topic, rclcpp::SensorDataQoS(),
    std::bind(&ScaleTruckController::image_callback, this, std::placeholders::_1));
  velocity_sub_ = this->create_subscription<scale_truck_msgs::msg::Lrc2Xav>(
    velocity_topic, qos::feedback(),
    std::bind(&ScaleTruckController::velocity_callback, this, std::placeholders::_1));

  lane_pub_ = this->create_publisher<scale_truck_msgs::msg::LaneCoef>(
    lane_topic, qos::lane());
  command_pub_ = this->create_publisher<scale_truck_msgs::msg::Xav2Lrc>(
    command_topic, qos::command());

  const auto period = std::chrono::duration<double>(update_period_s_);
  timer_ = this->create_wall_timer(
    std::chrono::duration_cast<std::chrono::nanoseconds>(period),
    std::bind(&ScaleTruckController::update, this));
}

void ScaleTruckController::image_callback(const sensor_msgs::msg::Image::SharedPtr msg)
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  image_seen_ = true;
}

void ScaleTruckController::scan_callback(const sensor_msgs::msg::LaserScan::SharedPtr msg)
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  scan_received_ = std::chrono::steady_clock::now();
  const rclcpp::Time stamp(msg->header.stamp);
  scan_header_age_ = stamp.nanoseconds() == 0 ? 0.0 : (this->now() - stamp).seconds();
  const double distance = front_distance(msg->ranges, msg->angle_min, msg->angle_increment,
    msg->range_min, msg->range_max, front_center_rad_, front_half_width_rad_);
  scan_seen_ = std::isfinite(distance) && scan_header_age_ >= 0.0 &&
    scan_header_age_ <= scan_timeout_s_;
  current_dist_ = scan_seen_ ? static_cast<float>(distance) : 0.0f;
  ++latest_trace_id_;
  latest_sensor_stamp_ = stamp.nanoseconds() == 0 ? this->now() : stamp;
}

void ScaleTruckController::velocity_callback(
  const scale_truck_msgs::msg::Lrc2Xav::SharedPtr msg)
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  current_vel_ = msg->cur_vel;
}

void ScaleTruckController::update()
{
  {
    const std::lock_guard<std::mutex> lock(state_mutex_);
    const double age = scan_header_age_ + std::chrono::duration<double>(
      std::chrono::steady_clock::now() - scan_received_).count();
    result_vel_ = scan_seen_ ? static_cast<float>(distance_speed(
      current_dist_, age, scan_timeout_s_, target_dist_, lv_stop_dist_,
      distance_gain_, target_vel_)) : 0.0f;
    angle_degree_ = 0.0f;  // Straight-line distance test; no camera steering yet.
  }

  publish_control();
}

void ScaleTruckController::publish_control()
{
  scale_truck_msgs::msg::Xav2Lrc command;
  scale_truck_msgs::msg::LaneCoef lane;

  {
    const std::lock_guard<std::mutex> lock(state_mutex_);
    command.trace_id = latest_trace_id_;
    command.sensor_stamp = latest_sensor_stamp_;
    command.steer_angle = angle_degree_;
    command.cur_dist = current_dist_;
    command.tar_dist = target_dist_;
    command.tar_vel = result_vel_;
    command.beta = beta_;
    command.gamma = gamma_;
  }

  command_pub_->publish(command);
  lane_pub_->publish(lane);

  if (enable_console_output_) {
    RCLCPP_DEBUG(
      this->get_logger(), "steer=%.3f target_vel=%.3f current_vel=%.3f image_seen=%d",
      command.steer_angle, command.tar_vel, current_vel_, image_seen_);
  }
}

}  // namespace scale_truck_control
