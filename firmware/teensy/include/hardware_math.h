#pragma once
#include <cstdint>
#include <cmath>

inline int32_t signedCount(uint32_t value) {
  return value <= 0x7fffffffU ? static_cast<int32_t>(value) :
    -1 - static_cast<int32_t>(0xffffffffU - value);
}

inline int32_t countDelta(int32_t current, int32_t previous) {
  return signedCount(static_cast<uint32_t>(current) - static_cast<uint32_t>(previous));
}

inline int boundedPulse(double command, double minimum, double maximum,
                        int center, double span) {
  if (!std::isfinite(command)) return center;
  if (command < minimum) command = minimum;
  if (command > maximum) command = maximum;
  return center + static_cast<int>(std::lround(command * span));
}
