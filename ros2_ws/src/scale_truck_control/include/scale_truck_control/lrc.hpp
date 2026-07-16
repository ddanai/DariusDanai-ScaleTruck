#pragma once

#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "scale_truck_control/sock_udp.hpp"
#include "scale_truck_msgs/msg/lrc2_ocr.hpp"
#include "scale_truck_msgs/msg/lrc2_xav.hpp"
#include "scale_truck_msgs/msg/ocr2_lrc.hpp"
#include "scale_truck_msgs/msg/xav2_lrc.hpp"

namespace scale_truck_control
{

class LocalResiliencyCoordinator : public rclcpp::Node
{
public:
  LocalResiliencyCoordinator();
  ~LocalResiliencyCoordinator() override;

private:
  void load_parameters();
  void init_ros_interfaces();
  void init_udp();
  void xavier_callback(const scale_truck_msgs::msg::Xav2Lrc::SharedPtr msg);
  void firmware_callback(const scale_truck_msgs::msg::Ocr2Lrc::SharedPtr msg);
  void update();
  void publish_feedback();
  void send_udp();
  void receive_udp_loop();
  void velocity_sensor_check();
  void mode_check(uint8_t crc_mode);
  void print_data();

  rclcpp::Subscription<scale_truck_msgs::msg::Xav2Lrc>::SharedPtr xavier_sub_;
  rclcpp::Subscription<scale_truck_msgs::msg::Ocr2Lrc>::SharedPtr firmware_sub_;
  rclcpp::Publisher<scale_truck_msgs::msg::Lrc2Xav>::SharedPtr xavier_pub_;
  rclcpp::Publisher<scale_truck_msgs::msg::Lrc2Ocr>::SharedPtr firmware_pub_;
  rclcpp::TimerBase::SharedPtr timer_;

  udp::UdpSocket udp_send_;
  udp::UdpSocket udp_recv_;
  std::thread udp_recv_thread_;
  std::atomic_bool running_{false};

  std::mutex state_mutex_;

  std::string udp_group_addr_;
  int truck_index_{0};
  int udp_group_port_{9392};
  bool enable_console_output_{true};
  double update_period_s_{0.02};
  float epsilon_{1.0f};
  float observer_a_{0.6817f};
  float observer_b_{0.3183f};
  float observer_l_{0.2817f};

  bool alpha_{false};
  bool beta_{false};
  bool gamma_{false};
  uint8_t lrc_mode_{0};
  uint8_t crc_mode_{0};
  float angle_degree_{0.0f};
  float current_dist_{0.0f};
  float target_dist_{0.0f};
  float current_vel_{0.0f};
  float target_vel_{0.0f};
  float predicted_vel_{0.0f};
  float estimated_vel_{0.0f};
  float saturated_vel_{0.0f};
};

}  // namespace scale_truck_control

