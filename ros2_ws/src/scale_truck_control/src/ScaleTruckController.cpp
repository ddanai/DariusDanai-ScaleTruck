#include "scale_truck_control/ScaleTruckController.hpp"

#include <algorithm>
#include <chrono>
#include <functional>

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
  target_vel_ = static_cast<float>(this->declare_parameter<double>("params.target_vel", 0.5));
  safety_vel_ = static_cast<float>(this->declare_parameter<double>("params.safety_vel", 0.3));
  lv_stop_dist_ = static_cast<float>(this->declare_parameter<double>("params.lv_stop_dist", 0.5));
  safety_dist_ = static_cast<float>(this->declare_parameter<double>("params.safety_dist", 1.5));
  target_dist_ = static_cast<float>(this->declare_parameter<double>("params.target_dist", 0.8));
  update_period_s_ = this->declare_parameter<double>("params.update_period_s", 0.02);
}

void ScaleTruckController::init_ros_interfaces()
{
  const auto image_topic = this->declare_parameter<std::string>(
    "topics.camera_reading", "/usb_cam/image_raw");
  const auto velocity_topic = this->declare_parameter<std::string>(
    "topics.lrc_to_xavier", "/lrc2xav_msg");
  const auto lane_topic = this->declare_parameter<std::string>(
    "topics.lane_coef", "/lane_msg");
  const auto command_topic = this->declare_parameter<std::string>(
    "topics.xavier_to_lrc", "/xav2lrc_msg");

  image_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
    image_topic, rclcpp::SensorDataQoS(),
    std::bind(&ScaleTruckController::image_callback, this, std::placeholders::_1));
  velocity_sub_ = this->create_subscription<scale_truck_msgs::msg::Lrc2Xav>(
    velocity_topic, rclcpp::QoS(1),
    std::bind(&ScaleTruckController::velocity_callback, this, std::placeholders::_1));

  lane_pub_ = this->create_publisher<scale_truck_msgs::msg::LaneCoef>(
    lane_topic, rclcpp::QoS(10));
  command_pub_ = this->create_publisher<scale_truck_msgs::msg::Xav2Lrc>(
    command_topic, rclcpp::QoS(1));

  const auto period = std::chrono::duration<double>(update_period_s_);
  timer_ = this->create_wall_timer(
    std::chrono::duration_cast<std::chrono::nanoseconds>(period),
    std::bind(&ScaleTruckController::update, this));
}

void ScaleTruckController::image_callback(const sensor_msgs::msg::Image::SharedPtr)
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  image_seen_ = true;
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
    if (current_dist_ <= lv_stop_dist_) {
      result_vel_ = 0.0f;
    } else if (current_dist_ <= safety_dist_) {
      const auto scaled_vel =
        (target_vel_ - safety_vel_) * ((current_dist_ - lv_stop_dist_) /
        (safety_dist_ - lv_stop_dist_)) + safety_vel_;
      result_vel_ = std::min(target_vel_, scaled_vel);
    } else {
      result_vel_ = target_vel_;
    }
  }

  publish_control();
}

void ScaleTruckController::publish_control()
{
  scale_truck_msgs::msg::Xav2Lrc command;
  scale_truck_msgs::msg::LaneCoef lane;

  {
    const std::lock_guard<std::mutex> lock(state_mutex_);
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
