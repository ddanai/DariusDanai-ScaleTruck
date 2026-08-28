# Xavier–Teensy Basic Bring-Up

Use this checklist to build, upload, and confirm basic USB serial communication.
Run commands from the Xavier unless stated otherwise.

## One-time setup

```bash
python3 -m pip install --user platformio pyserial
sudo apt update
sudo apt install -y git build-essential libusb-dev
cd /tmp
git clone https://github.com/PaulStoffregen/teensy_loader_cli.git
cd teensy_loader_cli
make
```

If the loader directory already exists, just rebuild it:

```bash
cd /tmp/teensy_loader_cli
make
```

## Repeatable bring-up

1. Open the firmware checkout and update the branch:

   ```bash
   cd ~/ros2_humble_ws/src/DariusDanai-ScaleTruck
   git switch fixed-command-testing
   git pull
   cd firmware/teensy
   ```

2. Connect the Teensy and find its serial device:

   ```bash
   ls /dev/ttyACM*
   ```

3. Build with the Xavier-compatible PlatformIO environment:

   ```bash
   python3 -m platformio run -e teensy41_xavier
   ls -l .pio/build/teensy41_xavier/firmware.hex
   ```

   A final `GLIBC_2.34` error from `teensy_size` is acceptable only if the
   `firmware.hex` file exists. Do not upgrade the Xavier's system `glibc`.

4. Upload the generated firmware:

   ```bash
   sudo /tmp/teensy_loader_cli/teensy_loader_cli \
     --mcu=TEENSY41 -w -v \
     "$PWD/.pio/build/teensy41_xavier/firmware.hex"
   ```

   When the loader says `Waiting for Teensy device`, press the Teensy Program
   button once. A successful upload ends with `Programming` and `Booting`.

5. Confirm basic communication:

   ```bash
   python3 -m serial.tools.miniterm /dev/ttyACM0 115200
   ```

   Type `PING` and press Enter. The Teensy should reply `PONG`. Exit with
   `Ctrl+]`. Substitute the correct `/dev/ttyACM*` path if it is not ACM0.

For the controller acceptance test, continue with
[Xavier Fixed-Command Test](XAVIER_FIXED_COMMAND_TEST.md).
