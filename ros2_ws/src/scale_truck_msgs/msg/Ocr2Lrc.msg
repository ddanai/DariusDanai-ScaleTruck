# Reserved interface: the current serial bridge does not publish this message.
# Intended measured signed speed in m/s; requires encoder calibration.
float32 cur_vel
# Legacy saturated observer input; Teensy physical scaling is not yet defined.
float32 u_k
