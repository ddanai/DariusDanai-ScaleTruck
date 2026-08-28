#!/usr/bin/env python3
"""Software-only fixed-command acceptance test for the Teensy controller."""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass

try:
    import serial
except ImportError:
    print("ERROR: pyserial is required. Install it with: python -m pip install pyserial")
    raise SystemExit(2)


STATUS_RE = re.compile(
    r"^STATUS uptime_ms=(?P<uptime>\d+) "
    r"safety_state=(?P<state>[A-Z_]+) "
    r"throttle_cmd=(?P<throttle>-?\d+(?:\.\d+)?) "
    r"steering_cmd=(?P<steering>-?\d+(?:\.\d+)?) "
    r"heartbeat=(?P<heartbeat>ON|OFF)$"
)


@dataclass
class Status:
    state: str
    throttle: float
    steering: float
    heartbeat: str


class TeensyTest:
    def __init__(self, port: str, baud: int) -> None:
        self.serial = serial.Serial(port, baud, timeout=0.25)
        self.failures: list[str] = []
        self.passes = 0

    def close(self) -> None:
        self.serial.close()

    def drain_startup(self) -> None:
        time.sleep(1.5)
        while self.serial.in_waiting:
            self._read_line()

    def _read_line(self) -> str:
        line = self.serial.readline().decode("utf-8", errors="replace").strip()
        if line:
            print(f"  RX  {line}")
        return line

    def command(self, command: str, expected_prefix: str, timeout: float = 1.0) -> str:
        print(f"  TX  {command}")
        self.serial.write((command + "\n").encode("ascii"))
        self.serial.flush()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = self._read_line()
            if line.startswith(expected_prefix):
                return line
        raise TimeoutError(f"no '{expected_prefix}' response to '{command}'")

    def status(self) -> Status:
        line = self.command("STATUS", "STATUS ")
        match = STATUS_RE.fullmatch(line)
        if not match:
            raise ValueError(f"malformed STATUS response: {line}")
        return Status(
            state=match.group("state"),
            throttle=float(match.group("throttle")),
            steering=float(match.group("steering")),
            heartbeat=match.group("heartbeat"),
        )

    def check(self, condition: bool, name: str, detail: str) -> None:
        if condition:
            self.passes += 1
            print(f"PASS {name}: {detail}")
        else:
            self.failures.append(f"{name}: {detail}")
            print(f"FAIL {name}: {detail}")

    def prepare_active(self) -> None:
        self.command("CLEAR", "OK FAULTS_CLEARED")
        self.command("ARM", "OK ARMED")
        self.command("FEEDBACK 0.0 0.0", "OK FEEDBACK")

    def hold_command(self, speed: float, steering: float, duration: float = 0.30) -> None:
        command = f"CMD {speed:.3f} {steering:.3f}"
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            self.command(command, "OK COMMAND_ACCEPTED")
            time.sleep(0.05)

    def active_case(
        self,
        name: str,
        speed: float,
        steering: float,
        throttle_range: tuple[float, float],
        steering_range: tuple[float, float],
    ) -> None:
        self.hold_command(speed, steering)
        result = self.status()
        correct = (
            result.state == "ACTIVE"
            and throttle_range[0] <= result.throttle <= throttle_range[1]
            and steering_range[0] <= result.steering <= steering_range[1]
        )
        self.check(
            correct,
            name,
            f"state={result.state}, throttle={result.throttle:.4f}, "
            f"steering={result.steering:.4f}",
        )


def run(args: argparse.Namespace) -> int:
    test = TeensyTest(args.port, args.baud)
    try:
        test.drain_startup()
        test.command("HEARTBEAT OFF", "OK HEARTBEAT OFF")
        test.prepare_active()

        test.active_case("neutral", 0.0, 0.0, (-0.01, 0.01), (-0.01, 0.01))
        test.active_case("forward", 0.2, 0.0, (0.05, 0.20), (-0.01, 0.01))
        test.active_case("reverse", -0.2, 0.0, (-0.20, -0.05), (-0.01, 0.01))
        test.active_case("left", 0.0, 10.0, (-0.01, 0.01), (0.20, 0.25))
        test.active_case("right", 0.0, -10.0, (-0.01, 0.01), (-0.25, -0.20))
        test.active_case("combined", 0.2, -10.0, (0.05, 0.20), (-0.25, -0.20))

        test.command("CMD 16.0 0.0", "ERR COMMAND_REJECTED")
        result = test.status()
        test.check(
            result.state == "COMMAND_FAULT"
            and result.throttle == 0.0
            and result.steering == 0.0,
            "invalid command",
            f"state={result.state}, throttle={result.throttle:.4f}, "
            f"steering={result.steering:.4f}",
        )

        test.prepare_active()
        test.command("CMD 0.2 0.0", "OK COMMAND_ACCEPTED")
        time.sleep(0.35)
        result = test.status()
        test.check(
            result.state == "WATCHDOG_FAULT"
            and result.throttle == 0.0
            and result.steering == 0.0,
            "watchdog",
            f"state={result.state}, throttle={result.throttle:.4f}, "
            f"steering={result.steering:.4f}",
        )

        test.command("CLEAR", "OK FAULTS_CLEARED")
        test.command("ARM", "OK ARMED")
        test.command("DISARM", "OK DISARMED")
        result = test.status()
        test.check(
            result.state == "DISARMED"
            and result.throttle == 0.0
            and result.steering == 0.0,
            "disarm",
            f"state={result.state}, throttle={result.throttle:.4f}, "
            f"steering={result.steering:.4f}",
        )

        test.command("ESTOP", "OK ESTOP_LATCHED")
        result = test.status()
        test.check(
            result.state == "ESTOP"
            and result.throttle == 0.0
            and result.steering == 0.0,
            "emergency stop",
            f"state={result.state}, throttle={result.throttle:.4f}, "
            f"steering={result.steering:.4f}",
        )
        test.command("CLEAR", "OK FAULTS_CLEARED")
        result = test.status()
        test.check(result.state == "DISARMED", "clear fault", f"state={result.state}")

    except (serial.SerialException, TimeoutError, ValueError) as error:
        test.failures.append(str(error))
        print(f"ERROR: {error}")
    finally:
        test.close()

    print(f"\nRESULT: {test.passes} passed, {len(test.failures)} failed")
    for failure in test.failures:
        print(f"  - {failure}")
    return 1 if test.failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default="COM5", help="Teensy serial port (default: COM5)")
    parser.add_argument("--baud", type=int, default=115200, help="serial baud rate")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(run(parse_args()))
