"""Exercise the bridge with ROS dependencies mocked on non-ROS hosts."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch


class EncoderBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = ["rclpy", "rclpy.node", "rclpy.qos", "scale_truck_msgs",
                 "scale_truck_msgs.msg", "std_msgs", "std_msgs.msg",
                 "std_srvs", "std_srvs.srv", "serial"]
        modules = {name: MagicMock() for name in names}
        modules["rclpy.node"].Node = object
        modules["std_msgs.msg"].String = types.SimpleNamespace
        modules["std_msgs.msg"].Int32 = types.SimpleNamespace
        path = Path(__file__).resolve().parents[1] / "ros2_ws/src/scale_truck_firmware_bridge/src/serial_bridge_node.py"
        spec = importlib.util.spec_from_file_location("encoder_bridge_under_test", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(module)
        cls.bridge_class = module.SerialBridgeNode

    def setUp(self):
        self.bridge = object.__new__(self.bridge_class)
        for name in ("encoder_raw_pub", "encoder_count_pub", "encoder_delta_pub"):
            setattr(self.bridge, name, MagicMock())

    def test_forward_reverse_stop(self):
        for count, delta, direction in [(277, -18, "REVERSE"), (19, 1, "FORWARD"), (19, 0, "STOP")]:
            line = f"ENCODER count={count} delta={delta} direction={direction}"
            self.bridge.publish_encoder(line)
            self.assertEqual(self.bridge.encoder_raw_pub.publish.call_args.args[0].data, line)
            self.assertEqual(self.bridge.encoder_count_pub.publish.call_args.args[0].data, count)
            self.assertEqual(self.bridge.encoder_delta_pub.publish.call_args.args[0].data, delta)

    def test_rejects_unrelated_partial_overflow_and_inconsistent_lines(self):
        for line in ["OK COMMAND_ACCEPTED", "ENCODER count=2", "ENCODER count=2147483648 delta=0 direction=STOP",
                     "ENCODER count=2 delta=-1 direction=FORWARD"]:
            self.bridge.publish_encoder(line)
        self.bridge.encoder_raw_pub.publish.assert_not_called()
        self.bridge.encoder_count_pub.publish.assert_not_called()

    def test_feedback_only_never_writes_commands(self):
        self.bridge.commands_enabled = False
        self.bridge.serial = MagicMock()
        self.assertFalse(self.bridge.write_command("ARM"))
        self.bridge.serial.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
