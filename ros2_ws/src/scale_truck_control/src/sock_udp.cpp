#include "scale_truck_control/sock_udp.hpp"

#include <cstdio>
#include <cstring>

namespace scale_truck_control
{
namespace udp
{

UdpSocket::UdpSocket()
: fd_(socket(AF_INET, SOCK_DGRAM, 0)), addr_{}, mreq_{}
{
  if (fd_ < 0) {
    perror("socket");
  }
}

UdpSocket::~UdpSocket()
{
  if (fd_ >= 0) {
    close(fd_);
  }
}

bool UdpSocket::init_receiver(const char * group, int port)
{
  if (fd_ < 0) {
    return false;
  }

  int yes = 1;
  if (setsockopt(fd_, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(yes)) < 0) {
    perror("setsockopt SO_REUSEADDR");
    return false;
  }

  timeval timeout{0, 10000};
  if (setsockopt(fd_, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout)) < 0) {
    perror("setsockopt SO_RCVTIMEO");
    return false;
  }

  std::memset(&addr_, 0, sizeof(addr_));
  addr_.sin_family = AF_INET;
  addr_.sin_addr.s_addr = htonl(INADDR_ANY);
  addr_.sin_port = htons(port);

  if (bind(fd_, reinterpret_cast<sockaddr *>(&addr_), sizeof(addr_)) < 0) {
    perror("bind");
    return false;
  }

  mreq_.imr_multiaddr.s_addr = inet_addr(group);
  mreq_.imr_interface.s_addr = htonl(INADDR_ANY);
  if (setsockopt(fd_, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq_, sizeof(mreq_)) < 0) {
    perror("setsockopt IP_ADD_MEMBERSHIP");
    return false;
  }

  return true;
}

bool UdpSocket::init_sender(const char * group, int port)
{
  if (fd_ < 0) {
    return false;
  }

  std::memset(&addr_, 0, sizeof(addr_));
  addr_.sin_family = AF_INET;
  addr_.sin_addr.s_addr = inet_addr(group);
  addr_.sin_port = htons(port);
  return true;
}

bool UdpSocket::receive(UdpData * data)
{
  socklen_t addrlen = sizeof(addr_);
  const auto nbytes = recvfrom(
    fd_, data, sizeof(*data), 0, reinterpret_cast<sockaddr *>(&addr_), &addrlen);
  return nbytes == static_cast<ssize_t>(sizeof(*data));
}

bool UdpSocket::send(const UdpData & data)
{
  const auto nbytes = sendto(
    fd_, &data, sizeof(data), 0, reinterpret_cast<sockaddr *>(&addr_), sizeof(addr_));
  if (nbytes < 0) {
    perror("sendto");
    return false;
  }
  return nbytes == static_cast<ssize_t>(sizeof(data));
}

}  // namespace udp
}  // namespace scale_truck_control

