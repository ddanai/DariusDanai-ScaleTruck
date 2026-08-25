# Jetson Xavier to Teensy 4.1 Bring-Up Guide

## Purpose

This procedure connects a Teensy 4.1 to an NVIDIA Jetson Xavier, loads the
scale-truck bring-up firmware, and verifies bidirectional USB serial
communication. A successful test consists of the Xavier sending `PING` and the
Teensy returning `PONG`.

The current firmware is diagnostic bring-up firmware. It blinks the onboard LED
and implements serial test commands, but it does not control the truck's motors
or steering.

## Required equipment

- NVIDIA Jetson Xavier running Ubuntu
- Teensy 4.1
- Micro-USB data cable (a charge-only cable will not work)
- Internet access on the Xavier for the initial software installation
- This repository checked out on the Xavier

## Safety preparation

Disconnect motors, motor controllers, actuators, batteries, and other external
power from the Teensy. Place the board on a nonconductive surface. During this
procedure, power the Teensy only through its USB connection to the Xavier.

Before continuing, confirm that the board is a **Teensy 4.1**. The project is
configured for `board = teensy41`; uploading a build intended for another model
is not supported by this procedure.

## 1. Connect the Teensy

Connect the Teensy's micro-USB connector to a normal USB host port on the
Xavier. Do not use a Xavier recovery/device-mode port.

Confirm that Linux detects the USB serial device:

```bash
ls /dev/ttyACM*
```

The expected result is usually:

```text
/dev/ttyACM0
```

The number may be different if other USB serial devices are connected. Use the
device that appears when the Teensy is connected. If necessary, compare the
output before and after connecting it.

Additional detection diagnostics are:

```bash
lsusb
dmesg | tail -30
```

## 2. Update the repository on the Xavier

The lab checkout used this location:

```bash
cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
git status
git pull --ff-only origin main
cd firmware/teensy
```

Review `git status` before pulling. If it reports modified files, preserve or
commit that work before updating the checkout.

## 3. Install PlatformIO

Install PlatformIO for the current Xavier user:

```bash
python3 -m pip install --user platformio
python3 -m platformio --version
```

Using `python3 -m platformio` avoids problems when `$HOME/.local/bin` is not on
the shell's `PATH`.

## 4. Select tools compatible with Jetson Ubuntu 20.04

The Jetson Xavier lab system uses Ubuntu 20.04 (`focal`). The newest PlatformIO
Teensy host utilities require newer `glibc` versions and fail with messages such
as:

```text
version `GLIBC_2.34' not found
```

Do **not** manually replace or upgrade the system `glibc`. In
`firmware/teensy/platformio.ini`, change:

```ini
platform = teensy
```

to:

```ini
platform = teensy@4.18.0
```

This can be done from the firmware directory with:

```bash
sed -i 's/^platform = teensy$/platform = teensy@4.18.0/' platformio.ini
```

## 5. Build the firmware

From `firmware/teensy`, run:

```bash
python3 -m platformio run --target clean
python3 -m platformio run
```

Many warnings can be printed by the Teensy framework because the project enables
strict compiler warnings. The build is usable if it produces this file:

```text
.pio/build/teensy41/firmware.hex
```

Confirm it exists:

```bash
ls -l .pio/build/teensy41/firmware.hex
```

## 6. Build a Teensy 4.1-compatible uploader

The `teensy-loader-cli` package included with Ubuntu 20.04 is too old to support
the `TEENSY41` target. PlatformIO's downloaded uploader may require a newer
`glibc`. Build the current PJRC command-line uploader natively on the Xavier:

```bash
sudo apt update
sudo apt install -y git build-essential libusb-dev
cd /tmp
git clone https://github.com/PaulStoffregen/teensy_loader_cli.git
cd teensy_loader_cli
make
ls -l teensy_loader_cli
```

The final `ls` command must show an executable named `teensy_loader_cli` before
continuing.

If `/tmp/teensy_loader_cli` already exists from an earlier session, use that
checkout instead of cloning it again:

```bash
cd /tmp/teensy_loader_cli
make
```

## 7. Upload the firmware

With the repository in the lab location shown above, run:

```bash
sudo /tmp/teensy_loader_cli/teensy_loader_cli \
  --mcu=TEENSY41 -w -v \
  "$HOME/ros2_humble_ws/src/DariusDanai-ScaleTruck/firmware/teensy/.pio/build/teensy41/firmware.hex"
```

When the uploader displays `Waiting for Teensy device`, press the small Program
button on the Teensy once. Do not hold it down. Successful output ends with:

```text
Found HalfKay Bootloader
Programming....................
Booting
```

The firmware is now running. The onboard LED should change state approximately
once per second.

## 8. Verify serial output

The Teensy can briefly disappear from `/dev` while rebooting. Check the device
name again:

```bash
ls /dev/ttyACM*
```

Open it at 115200 baud:

```bash
python3 -m serial.tools.miniterm /dev/ttyACM0 115200
```

Expected output includes:

```text
BOOT scale-truck-teensy 0.1.0
READY
HEARTBEAT 1000
```

If the monitor is opened after the Teensy boots, `BOOT` and `READY` may already
have been sent. Continuing `HEARTBEAT` messages are sufficient to show data is
traveling from the Teensy to the Xavier.

Miniterm may not visibly echo typed characters while heartbeat messages scroll.
Type `PING` and press Enter anyway. The expected reply is:

```text
PONG
```

Exit miniterm by pressing `Ctrl+]`.

## 9. Automatic bidirectional test

For a less ambiguous test, close miniterm and run:

```bash
python3 -c "import serial,time; s=serial.Serial('/dev/ttyACM0',115200,timeout=3); s.write(b'PING\n'); end=time.time()+3; lines=[]; exec('while time.time()<end:\n line=s.readline().decode(errors=\"replace\").strip()\n if line: lines.append(line)\n if line==\"PONG\": break'); print('\\n'.join(lines)); s.close()"
```

The test passes if the output contains:

```text
PONG
```

Heartbeat messages can appear before or after command responses because serial
messages are asynchronous. `ERR UNKNOWN_COMMAND` can also appear after malformed
or leftover terminal input; it does not invalidate a later successful
`PING`/`PONG` exchange.

## Acceptance criteria

The connection is verified when all of the following are true:

1. The Xavier enumerates the Teensy as `/dev/ttyACM0` (or another `ttyACM`
   number).
2. The firmware uploads and the loader reports `Programming` followed by
   `Booting`.
3. The Xavier receives `HEARTBEAT` messages from the Teensy.
4. The Xavier sends the newline-terminated `PING` command and receives `PONG`.

## Troubleshooting

### `/dev/ttyACM0` does not exist

- Confirm that the micro-USB cable supports data, not only charging.
- Try another USB host port or cable.
- Reconnect the Teensy and inspect `dmesg | tail -30`.
- Check whether the device enumerated with another number, such as
  `/dev/ttyACM1`.

### Permission denied when opening the serial port

Add the current user to the serial-device group:

```bash
sudo usermod -aG dialout "$USER"
```

Log out and back in before retrying.

### `pio: command not found`

Use the module form:

```bash
python3 -m platformio run
```

### `GLIBC_2.33` or `GLIBC_2.34` not found

Confirm that `platformio.ini` uses `teensy@4.18.0` for the build, then use the
natively compiled `/tmp/teensy_loader_cli/teensy_loader_cli` for upload. Do not
upgrade `glibc` manually.

### `Unknown MCU type "TEENSY41"`

The Ubuntu-provided uploader is too old. Use the uploader built from the PJRC
GitHub repository in Step 6.

### The monitor scrolls too quickly to type

Typing still works even if characters are hidden by heartbeat output. Use the
automatic test in Step 9 if the interactive test is difficult to read.

### `ERR UNKNOWN_COMMAND` appears

The Teensy received a line other than a supported command. Close other programs
using the serial port, reopen it, and send exactly `PING` followed by Enter. A
subsequent `PONG` is a successful test.
