#include <cassert>
#include <cmath>
#include <limits>

#include "scale_truck_control/distance_control.hpp"

int main()
{
  using scale_truck_control::distance_speed;
  using scale_truck_control::front_distance;
  const float nan = std::numeric_limits<float>::quiet_NaN();
  const float inf = std::numeric_limits<float>::infinity();
  // Side obstacles must not become the forward target.
  assert(std::abs(front_distance({0.2f, 1.0f, 1.2f, 0.3f}, -0.3, 0.2,
    0.15, 25.0, 0.0, 0.11) - 1.0) < 1e-6);
  assert(std::isnan(front_distance({nan, inf, 0.1f, 26.0f}, -0.3, 0.2,
    0.15, 25.0, 0.0, 1.0)));
  assert(std::isnan(front_distance({}, 0, 0.1, 0.15, 25, 0, 0.2)));
  assert(std::isnan(front_distance({1.0f}, 0, 0, 0.15, 25, 0, 0.2)));
  // Sector wraps around +/-pi and supports reversed scan ordering.
  assert(std::abs(front_distance({0.7f}, -3.13, -0.1, 0.15, 25,
    3.13, 0.05) - 0.7) < 1e-6);
  assert(distance_speed(2.0, 0, 0.3, 0.8, 0.5, 0.5, 0.2) == 0.2);
  assert(std::abs(distance_speed(1.0, 0.1, 0.3, 0.8, 0.5, 0.5, 0.2) - 0.1) < 1e-6);
  assert(distance_speed(0.8, 0.1, 0.3, 0.8, 0.5, 0.5, 0.2) == 0.0);
  assert(distance_speed(0.4, 0.1, 0.3, 0.8, 0.5, 0.5, 0.2) == 0.0);
  assert(distance_speed(2.0, 0.31, 0.3, 0.8, 0.5, 0.5, 0.2) == 0.0);
  assert(distance_speed(2.0, -0.1, 0.3, 0.8, 0.5, 0.5, 0.2) == 0.0);
  assert(distance_speed(nan, 0, 0.3, 0.8, 0.5, 0.5, 0.2) == 0.0);
  assert(distance_speed(inf, 0, 0.3, 0.8, 0.5, 0.5, 0.2) == 0.0);
  assert(distance_speed(2, 0, 0.3, 0.8, 0.5, 0.5, 0) == 0.0);
}
