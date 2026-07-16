#pragma once

#include <arpa/inet.h>
#include <cstdint>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

namespace scale_truck_control
{
namespace udp
{

struct LaneCoef
{
  float a;
  float b;
  float c;
};

struct UdpData
{
  int index;
  int to;
  int sync;
  int cf;
  float target_vel;
  float current_vel;
  float predict_vel;
  float target_dist;
  float current_dist;
  float current_angle;
  float roi_dist;
  bool alpha;
  bool beta;
  bool gamma;
  uint8_t mode;
  LaneCoef coef[3];
};

class UdpSocket
{
public:
  UdpSocket();
  ~UdpSocket();

  UdpSocket(const UdpSocket &) = delete;
  UdpSocket & operator=(const UdpSocket &) = delete;

  bool init_receiver(const char * group, int port);
  bool init_sender(const char * group, int port);
  bool receive(UdpData * data);
  bool send(const UdpData & data);

private:
  int fd_;
  sockaddr_in addr_;
  ip_mreq mreq_;
};

}  // namespace udp
}  // namespace scale_truck_control

