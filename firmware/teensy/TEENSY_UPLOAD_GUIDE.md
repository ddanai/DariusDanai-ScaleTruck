# Uploading the Firmware to the Teensy 4.1

This guide records how the scale-truck firmware was built, uploaded, and
verified from a Windows PC using PlatformIO.

## Equipment

- Teensy 4.1 board
- USB data cable (a charge-only cable will not work)
- Windows PC with VS Code and PlatformIO installed

For the initial board test, the Teensy was connected directly to the PC rather
than the NVIDIA Jetson Xavier. Motors, the motor controller, and the steering
actuator remained disconnected.

## 1. Connect the board

Connect the Teensy to the PC using its USB data port. The Teensy's LED may begin
blinking when the board receives power.

## 2. Open the firmware directory

In VS Code, open this project directory:

```text
C:\Users\dariu\OneDrive\Desktop\Documents\scaletruck\firmware\teensy
```

Open a PowerShell terminal with **Terminal > New Terminal**. If the terminal is
in another directory, run:

```powershell
cd "C:\Users\dariu\OneDrive\Desktop\Documents\scaletruck\firmware\teensy"
```

## 3. Build and upload

Run:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run --target upload
```

PlatformIO builds the Teensy 4.1 firmware and uploads the generated image. A
successful operation ends with a message similar to:

```text
========================= [SUCCESS] =========================
```

If PlatformIO asks for the Teensy Program button, press the small push button on
the board once. Do not hold it down.

## 4. Open the serial monitor

After the upload completes, run:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" device monitor --baud 115200 --echo --filter send_on_enter
```

The board should print startup messages and periodic heartbeats:

```text
BOOT scale-truck-teensy 0.1.0
READY
HEARTBEAT 1000
```

The heartbeat number is the approximate number of milliseconds since the board
started; it is not a sequence number.

## 5. Verify commands

Click inside the monitor terminal, type each command, and press Enter.

Test communication:

```text
PING
```

Expected response:

```text
PONG
```

Stop periodic heartbeat output:

```text
HEARTBEAT OFF
```

Expected response:

```text
OK HEARTBEAT OFF
```

Check the firmware and safety state:

```text
STATUS
```

The response should show a disarmed controller, zero actuator commands, and the
heartbeat setting:

```text
STATUS uptime_ms=... safety_state=DISARMED throttle_cmd=0.0000 steering_cmd=0.0000 heartbeat=OFF
```

Restart heartbeat output with:

```text
HEARTBEAT ON
```

Exit the serial monitor with **Ctrl+C**.

## Safety test

The software emergency-stop command can be tested while actuators are
disconnected:

```text
ESTOP
STATUS
```

The status should report `safety_state=ESTOP` and both commands should remain
`0.0000`. The E-stop is latched; reset or power-cycle the Teensy to return the
current bring-up firmware to `DISARMED`.

## Troubleshooting

### The upload cannot open the serial port

Close every serial monitor with **Ctrl+C**, then run the upload again. Only one
program can own a Windows COM port at a time.

### PlatformIO cannot find the board

- Confirm the cable supports data.
- Try another USB port.
- Press the Teensy Program button once when the upload tool requests it.
- List detected ports with:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" device list
```

### Typed commands do not appear

Restart the monitor with both `--echo` and `--filter send_on_enter`, as shown
above. Stop the heartbeat first with `HEARTBEAT OFF` if its output makes the
terminal difficult to read.

### A command returns `ERR UNKNOWN_COMMAND`

Check spelling and capitalization. If a newly added command is not recognized,
rebuild and upload the latest firmware before testing it.

## Moving the connection to the Xavier

PC testing verifies firmware upload and USB serial communication only. After
board-level verification, the Teensy can be connected to the Xavier by USB.
Actuators must remain disconnected until the physical emergency-stop input,
sensor feedback, command protocol, and verified neutral actuator outputs are
integrated and tested.
