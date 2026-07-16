#include "scale_truck_control/lrc.hpp"

#include <chrono>
#include <cmath>
#include <functional>

namespace scale_truck_control
{

LocalResiliencyCoordinator::LocalResiliencyCoordinator()
: rclcpp::Node("lrc_node")
{
  load_parameters();
  init_ros_interfaces();
  init_udp();
  running_ = true;
  udp_recv_thread_ = std::thread(&LocalResiliencyCoordinator::receive_udp_loop, this);
}

LocalResiliencyCoordinator::~LocalResiliencyCoordinator()
{
  running_ = false;
  if (udp_recv_thread_.joinable()) {
    udp_recv_thread_.join();
  }
}

void LocalResiliencyCoordinator::load_parameters()
{
  truck_index_ = this->declare_parameter<int>("params.truck_info", 0);
  udp_group_addr_ = this->declare_parameter<std::string>(
    "lrc_params.udp_group_addr", "239.255.255.250");
  udp_group_port_ = this->declare_parameter<int>("lrc_params.udp_group_port", 9392);
  epsilon_ = static_cast<float>(this->declare_parameter<double>("lrc_params.epsilon", 1.0));
  observer_a_ = static_cast<float>(this->declare_parameter<double>("lrc_params.lu_ob_a", 0.6817));
  observer_b_ = static_cast<float>(this->declare_parameter<double>("lrc_params.lu_ob_b", 0.3183));
  observer_l_ = static_cast<float>(this->declare_parameter<double>("lrc_params.lu_ob_l", 0.2817));
  enable_console_output_ = this->declare_parameter<bool>(
    "lrc_params.enable_console_output", true);
  update_period_s_ = this->declare_parameter<double>("lrc_params.update_period_s", 0.02);
}

void LocalResiliencyCoordinator::init_ros_interfaces()
{
  const auto xavier_to_lrc_topic = this->declare_parameter<std::string>(
    "topics.xavier_to_lrc", "xav2lrc_msg");
  const auto ocr_to_lrc_topic = this->declare_parameter<std::string>(
    "topics.ocr_to_lrc", "ocr2lrc_msg");
  const auto lrc_to_xavier_topic = this->declare_parameter<std::string>(
    "topics.lrc_to_xavier", "lrc2xav_msg");
  const auto lrc_to_ocr_topic = this->declare_parameter<std::string>(
    "topics.lrc_to_ocr", "lrc2ocr_msg");

  xavier_sub_ = this->create_subscription<scale_truck_msgs::msg::Xav2Lrc>(
    xavier_to_lrc_topic, rclcpp::QoS(1),
    std::bind(&LocalResiliencyCoordinator::xavier_callback, this, std::placeholders::_1));
  firmware_sub_ = this->create_subscription<scale_truck_msgs::msg::Ocr2Lrc>(
    ocr_to_lrc_topic, rclcpp::QoS(1),
    std::bind(&LocalResiliencyCoordinator::firmware_callback, this, std::placeholders::_1));

  xavier_pub_ = this->create_publisher<scale_truck_msgs::msg::Lrc2Xav>(
    lrc_to_xavier_topic, rclcpp::QoS(1));
  firmware_pub_ = this->create_publisher<scale_truck_msgs::msg::Lrc2Ocr>(
    lrc_to_ocr_topic, rclcpp::QoS(1));

  const auto period = std::chrono::duration<double>(update_period_s_);
  timer_ = this->create_wall_timer(
    std::chrono::duration_cast<std::chrono::nanoseconds>(period),
    std::bind(&LocalResiliencyCoordinator::update, this));
}

void LocalResiliencyCoordinator::init_udp()
{
  const bool send_ok = udp_send_.init_sender(udp_group_addr_.c_str(), udp_group_port_);
  const bool recv_ok = udp_recv_.init_receiver(udp_group_addr_.c_str(), udp_group_port_);
  if (!send_ok || !recv_ok) {
    RCLCPP_WARN(this->get_logger(), "UDP resiliency sockets were not fully initialized");
  }
}

void LocalResiliencyCoordinator::xavier_callback(
  const scale_truck_msgs::msg::Xav2Lrc::SharedPtr msg)
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  angle_degree_ = msg->steer_angle;
  current_dist_ = msg->cur_dist;
  target_dist_ = msg->tar_dist;
  target_vel_ = msg->tar_vel;
  beta_ = msg->beta;
  gamma_ = msg->gamma;
}

void LocalResiliencyCoordinator::firmware_callback(
  const scale_truck_msgs::msg::Ocr2Lrc::SharedPtr msg)
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  current_vel_ = msg->cur_vel;
  saturated_vel_ = msg->u_k;
}

void LocalResiliencyCoordinator::update()
{
  velocity_sensor_check();
  mode_check(crc_mode_);
  publish_feedback();
  send_udp();
  print_data();
}

void LocalResiliencyCoordinator::publish_feedback()
{
  scale_truck_msgs::msg::Lrc2Xav xavier_msg;
  scale_truck_msgs::msg::Lrc2Ocr firmware_msg;

  {
    const std::lock_guard<std::mutex> lock(state_mutex_);
    xavier_msg.cur_vel = current_vel_;
    firmware_msg.index = truck_index_;
    firmware_msg.steer_angle = angle_degree_;
    firmware_msg.cur_dist = current_dist_;
    firmware_msg.tar_dist = target_dist_;
    firmware_msg.tar_vel = target_vel_;
    firmware_msg.pred_vel = predicted_vel_;
    firmware_msg.alpha = alpha_;
  }

  xavier_pub_->publish(xavier_msg);
  firmware_pub_->publish(firmware_msg);
}

void LocalResiliencyCoordinator::send_udp()
{
  udp::UdpData data{};
  {
    const std::lock_guard<std::mutex> lock(state_mutex_);
    data.index = truck_index_;
    data.to = 100;
    data.alpha = alpha_;
    data.beta = beta_;
    data.gamma = gamma_;
    data.current_vel = current_vel_;
    data.current_dist = current_dist_;
    data.mode = lrc_mode_;
  }
  udp_send_.send(data);
}

void LocalResiliencyCoordinator::receive_udp_loop()
{
  while (running_ && rclcpp::ok()) {
    udp::UdpData data{};
    if (!udp_recv_.receive(&data)) {
      continue;
    }

    if (data.index == 100 && data.to == truck_index_) {
      const std::lock_guard<std::mutex> lock(state_mutex_);
      predicted_vel_ = data.predict_vel;
      crc_mode_ = data.mode;
      if (crc_mode_ >= lrc_mode_) {
        lrc_mode_ = crc_mode_;
      }
    }
  }
}

void LocalResiliencyCoordinator::velocity_sensor_check()
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  estimated_vel_ =
    (observer_a_ * estimated_vel_) + (observer_b_ * saturated_vel_) +
    (observer_l_ * (current_vel_ - estimated_vel_));

  if (std::fabs(current_vel_ - estimated_vel_) > epsilon_) {
    alpha_ = true;
  }
}

void LocalResiliencyCoordinator::mode_check(uint8_t crc_mode)
{
  const std::lock_guard<std::mutex> lock(state_mutex_);
  if (truck_index_ == 0) {
    if (beta_) {
      lrc_mode_ = 2;
    } else if ((alpha_ || gamma_) && (crc_mode == 0 || crc_mode == 1)) {
      lrc_mode_ = 1;
    } else if (crc_mode == 0) {
      lrc_mode_ = 0;
    }
    return;
  }

  if (beta_ && gamma_) {
    lrc_mode_ = 2;
  } else if ((alpha_ || beta_ || gamma_) && (crc_mode == 0 || crc_mode == 1)) {
    lrc_mode_ = 1;
  } else if (crc_mode == 0) {
    lrc_mode_ = 0;
  }
}

void LocalResiliencyCoordinator::print_data()
{
  static int count = 0;
  if (!enable_console_output_ || count++ <= 100) {
    return;
  }

  const std::lock_guard<std::mutex> lock(state_mutex_);
  RCLCPP_INFO(
    this->get_logger(),
    "pred=%.3f target=%.3f current=%.3f saturated=%.3f estimate_error=%.3f "
    "alpha=%d beta=%d gamma=%d mode=%d",
    predicted_vel_, target_vel_, current_vel_, saturated_vel_,
    std::fabs(current_vel_ - estimated_vel_), alpha_, beta_, gamma_, lrc_mode_);
  count = 0;
}

}  // namespace scale_truck_control
