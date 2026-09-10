# Copied from Xav2Lrc so the command can be matched across the pipeline.
uint64 trace_id
builtin_interfaces/Time sensor_stamp
int32 index
# Requested steering angle in degrees. Physical sign/centre require calibration.
float32 steer_angle
# Separation in metres by interface convention; not serialized to Teensy.
float32 cur_dist
float32 tar_dist
# Requested signed speed in m/s; serialized with steer_angle as CMD.
float32 tar_vel
# Predicted speed in m/s; not serialized to Teensy.
float32 pred_vel
# LRC velocity-sensor discrepancy flag; not serialized to Teensy.
bool alpha

