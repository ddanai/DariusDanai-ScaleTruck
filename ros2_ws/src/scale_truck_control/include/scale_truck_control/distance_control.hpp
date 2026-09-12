#pragma once

#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

namespace scale_truck_control
{

// Nearest finite return in a configurable sector of the sensor frame.
// No return is unknown, not permission to drive into unobserved space.
inline double front_distance(
  const std::vector<float> & ranges, double angle_min, double angle_increment,
  double range_min, double range_max, double center, double half_width)
{
  if (!std::isfinite(angle_min) || !std::isfinite(angle_increment) ||
    angle_increment == 0.0 || !std::isfinite(range_min) ||
    !std::isfinite(range_max) || range_min < 0.0 || range_max <= range_min)
  {
    return std::numeric_limits<double>::quiet_NaN();
  }
  double nearest = std::numeric_limits<double>::infinity();
  for (size_t i = 0; i < ranges.size(); ++i) {
    const double offset = std::remainder(angle_min + i * angle_increment - center,
      2.0 * 3.14159265358979323846);
    const double distance = ranges[i];
    if (std::abs(offset) <= half_width && std::isfinite(distance) &&
      distance >= range_min && distance <= range_max)
    {
      nearest = std::min(nearest, distance);
    }
  }
  return std::isfinite(nearest) ? nearest : std::numeric_limits<double>::quiet_NaN();
}

inline double distance_speed(
  double distance, double age, double timeout, double desired_gap,
  double stop_distance, double gain, double speed_limit)
{
  if (!std::isfinite(distance) || !std::isfinite(age) || age < 0.0 ||
    age > timeout || distance <= stop_distance)
  {
    return 0.0;
  }
  return std::max(0.0, std::min(speed_limit, gain * (distance - desired_gap)));
}

}  // namespace scale_truck_control
