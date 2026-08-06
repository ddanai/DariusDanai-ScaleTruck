# Identifies the sensor frame used for this command.
uint64 trace_id
# Acquisition time copied from the sensor message header.
builtin_interfaces/Time sensor_stamp
float32 steer_angle
float32 cur_dist
float32 tar_dist
float32 tar_vel
bool beta
bool gamma

