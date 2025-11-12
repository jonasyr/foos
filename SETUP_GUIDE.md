# Complete Setup Guide for Foos Project

This comprehensive guide will walk you through every step needed to set up the Foos foosball table scoring system from scratch. This project provides automatic goal detection, instant replay, score-keeping, and integration with various services.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Hardware Requirements](#hardware-requirements)
3. [Quick Start for Raspberry Pi](#quick-start-for-raspberry-pi)
4. [Detailed Setup for Raspberry Pi](#detailed-setup-for-raspberry-pi)
5. [Setup for Development on x86_64 Linux](#setup-for-development-on-x8664-linux)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Running the Application](#running-the-application)
9. [Troubleshooting](#troubleshooting)
10. [Next Steps](#next-steps)

---

## System Requirements

### Raspberry Pi Requirements (Production)
- **Raspberry Pi 2 or 3** (Raspberry Pi 4 is NOT currently supported)
- **Raspberry Pi OS** (formerly Raspbian) - Bookworm or Trixie
- **Python 3.7+** (tested with Python 3.11)
- **256MB GPU memory** (recommended for proper video replay)
- **SD card** (16GB+ recommended)
- **Network connection** (for updates and optional features)

### x86_64 Linux Requirements (Development/Testing)
- **Ubuntu/Debian-based Linux** (tested on Debian-based systems)
- **Python 3.7+**
- **X11 display server** (for GUI testing)
- **OpenGL ES libraries** (optional, for full GUI functionality)

### Hardware Components
See [doc/HWSetup.md](doc/HWSetup.md) for detailed hardware setup including:
- Raspberry Pi Camera Module
- IR barrier sensors for goal detection
- Physical buttons for manual control
- TV/Display with HDMI
- Optional: Arduino for additional I/O

---

## Quick Start for Raspberry Pi

If you're setting up on a **Raspberry Pi running Debian Trixie** (the latest Raspberry Pi OS), use the automated setup script:

```bash
# Clone the repository
cd ~
git clone https://github.com/swehner/foos.git
cd foos

# Run the automated setup script
./setup-trixie.sh

# Copy and configure your settings
cp config.py.sample config.py
nano config.py  # Edit as needed

# Test the setup
./check

# Run the application
python3 foos.py
```

The `setup-trixie.sh` script handles all system dependencies, Python packages, GPIO setup, and directory structure. **Skip to [Configuration](#configuration) after running this script.**

---

## Detailed Setup for Raspberry Pi

### Step 1: Install Raspberry Pi OS

1. **Download Raspberry Pi OS Lite** from the official site:
   - https://www.raspberrypi.org/software/operating-systems/
   - Use the **Lite** version (no desktop) for better performance

2. **Flash the OS to your SD card** using Raspberry Pi Imager or Etcher:
   - https://www.raspberrypi.org/software/

3. **Enable SSH** (optional but recommended):
   - After flashing, create an empty file named `ssh` in the boot partition
   - Or use Raspberry Pi Imager's advanced options to enable SSH

4. **Boot your Raspberry Pi** and connect via SSH or keyboard:
   ```bash
   ssh pi@raspberrypi.local
   # Default password: raspberry (change this immediately!)
   ```

### Step 2: Update System and Install Base Dependencies

```bash
# Update package lists
sudo apt-get update

# Upgrade existing packages
sudo apt-get upgrade -y

# Install git
sudo apt-get install -y git

# Install system dependencies
sudo apt-get install -y \
    ffmpeg \
    vlc \
    mpv \
    python3-pip \
    python3-venv \
    sox \
    cec-utils \
    libjpeg62-turbo \
    libtiff6 \
    libpng16-16 \
    libopenblas0 \
    libopenblas-dev \
    libsqlite3-0 \
    libsqlite3-dev \
    avahi-daemon \
    curl
```

**What each package does:**
- `ffmpeg`: Video encoding for uploads
- `vlc/mpv`: Video playback (alternative players)
- `sox`: Sound playback (`play` command)
- `cec-utils`: TV control via HDMI-CEC for standby mode
- `libjpeg62-turbo, libtiff6, libpng16-16`: Image processing libraries
- `libopenblas*`: Optimized linear algebra (required by NumPy)
- `avahi-daemon`: mDNS/Bonjour for network discovery

### Step 3: Clone the Repository

```bash
# Navigate to home directory
cd ~

# Clone the foos repository
git clone https://github.com/swehner/foos.git
cd foos
```

### Step 4: Create Replay Directory

The replay system uses shared memory (`tmpfs`) for fast video chunk storage:

```bash
# Create replay directories
sudo mkdir -p /dev/shm/replay/fragments
sudo chmod -R 777 /dev/shm/replay

# Make it persistent across reboots
sudo mkdir -p /etc/tmpfiles.d
sudo tee /etc/tmpfiles.d/foos-replay.conf << 'EOF'
# Foos replay directory in tmpfs
d /dev/shm/replay 0777 root root -
d /dev/shm/replay/fragments 0777 root root -
EOF
```

**Why `/dev/shm`?**
- It's RAM-based storage (tmpfs), extremely fast for video chunks
- No SD card wear from constant video writes
- Automatically cleared on reboot (videos are temporary anyway)

### Step 5: Configure Raspberry Pi Settings

```bash
# Open Raspberry Pi configuration
sudo raspi-config
```

**Required Settings:**

1. **Enable Camera (Legacy)**:
   - Navigate to: `Interface Options` → `Legacy Camera` → `Yes`
   - Note: Newer Pi OS versions use `libcamera`, but foos uses legacy camera API

2. **Increase GPU Memory to 256MB**:
   - Navigate to: `Performance Options` → `GPU Memory`
   - Set to: `256` (minimum 192MB recommended)
   - This is crucial for video replay and UI rendering

3. **Optional - Enable Serial Console** (for Arduino integration):
   - Navigate to: `Interface Options` → `Serial Port`

4. **Reboot** to apply changes:
   ```bash
   sudo reboot
   ```

### Step 6: Install Python Dependencies

```bash
cd ~/foos

# Install Python packages
pip3 install --break-system-packages -r requirements.txt

# Fix RPi.GPIO for newer systems (if needed)
# On Trixie/Bookworm, the default RPi.GPIO may be broken
pip3 uninstall -y RPi.GPIO --break-system-packages
pip3 install --break-system-packages rpi-lgpio
```

**Note:** The `--break-system-packages` flag is required on newer Debian/Pi OS versions that use externally-managed Python environments.

**Python Dependencies Explained:**
- `pi3d`: 3D graphics library for the UI (uses OpenGL ES)
- `numpy`: Numerical computing (required by pi3d)
- `Pillow`: Image processing
- `pyserial`: Arduino/serial communication
- `google-api-python-client`: YouTube upload functionality
- `evdev`: Direct keyboard input from `/dev/input`
- `RPi.GPIO` (or `rpi-lgpio`): GPIO pin control for sensors/buttons

### Step 7: Add User to Required Groups

```bash
# Add user to video group (camera access)
sudo usermod -a -G video $USER

# Add user to input group (evdev keyboard access)
sudo usermod -a -G input $USER

# Add user to gpio group (GPIO access)
sudo usermod -a -G gpio $USER

# Log out and back in for changes to take effect
# Or reboot
```

### Step 8: Build Video Player

The video player is a custom OpenMAX IL player for hardware-accelerated playback:

```bash
cd ~/foos/video/player

# Build the player
make

# Verify it was built
ls -lh player
```

If the build fails, ensure you have the VideoCore libraries:
```bash
# These should be included in Raspberry Pi OS
ls /opt/vc/lib/
```

### Step 9: Create Configuration File

```bash
cd ~/foos

# Copy the sample configuration
cp config.py.sample config.py

# Edit configuration
nano config.py
```

See the [Configuration](#configuration) section below for details on what to configure.

### Step 10: Verify Installation

```bash
cd ~/foos

# Run the check script
./check
```

**What the check script verifies:**
- Binary dependencies (ffmpeg, sox, etc.)
- Shared libraries (libjpeg, libpng, etc.)
- Raspberry Pi specific components (raspivid, player)
- Replay path configuration
- GPU memory settings
- Input device permissions
- Python dependencies

Fix any issues reported by the check script before proceeding.

---

## Setup for Development on x86_64 Linux

For development and testing on a regular Linux PC (without Raspberry Pi hardware):

### Step 1: Install System Dependencies

```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    libgl1-mesa-dev \
    libgles2-mesa-dev \
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    libopenblas-dev
```

### Step 2: Clone Repository

```bash
cd ~
git clone https://github.com/swehner/foos.git
cd foos
```

### Step 3: Create Replay Directory

```bash
sudo mkdir -p /dev/shm/replay/fragments
sudo chmod -R 777 /dev/shm/replay
```

### Step 4: Install Python Dependencies

```bash
cd ~/foos

# Install most dependencies (skip RPi.GPIO initially)
pip3 install --break-system-packages \
    pi3d \
    numpy \
    Pillow \
    pyserial \
    google-api-python-client \
    six \
    inotify_simple \
    requests \
    evdev \
    pygame
```

### Step 5: Create RPi.GPIO Mock

Since RPi.GPIO only works on Raspberry Pi hardware, create a mock for development:

```bash
# Create RPi package directory
sudo mkdir -p /usr/local/lib/python3.11/dist-packages/RPi

# Create GPIO mock module
sudo tee /usr/local/lib/python3.11/dist-packages/RPi/GPIO.py << 'EOF'
"""Mock RPi.GPIO module for non-Raspberry Pi systems"""

# GPIO modes
BCM = 11
BOARD = 10

# Pin modes
IN = 1
OUT = 0

# Pull up/down resistors
PUD_UP = 22
PUD_DOWN = 21
PUD_OFF = 20

# Edge detection
RISING = 31
FALLING = 32
BOTH = 33

# Pin states
HIGH = 1
LOW = 0

def setmode(mode):
    pass

def setwarnings(flag):
    pass

def setup(channel, mode, **kwargs):
    pass

def cleanup(channel=None):
    pass

def output(channel, state):
    pass

def input(channel):
    return LOW

def add_event_detect(channel, edge, callback=None, bouncetime=None):
    pass

def remove_event_detect(channel):
    pass

def gpio_function(channel):
    return OUT

def PWM(channel, frequency):
    return MockPWM(channel, frequency)

class MockPWM:
    def __init__(self, channel, frequency):
        self.channel = channel
        self.frequency = frequency
        self.duty_cycle = 0

    def start(self, duty_cycle):
        self.duty_cycle = duty_cycle

    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle

    def ChangeFrequency(self, frequency):
        self.frequency = frequency

    def stop(self):
        pass
EOF

# Create package init file
sudo tee /usr/local/lib/python3.11/dist-packages/RPi/__init__.py << 'EOF'
"""Mock RPi package for non-Raspberry Pi systems"""
EOF

# Verify mock works
python3 -c "import RPi.GPIO; print('RPi.GPIO mock imported successfully')"
```

**Note:** Adjust the Python version in the path if you're using a different version (e.g., `python3.9`, `python3.10`).

### Step 6: Create Configuration

```bash
cd ~/foos
cp config.py.sample config.py

# Edit config (disable hardware-dependent plugins)
nano config.py
```

For x86_64 development, your `config.py` should start with:
```python
from config_base import *

# Disable hardware plugins for development
plugins = set(['score', 'game', 'menu', 'control', 'io_debug'])

# Enable keyboard for testing
# Note: io_evdev_keyboard won't work without /dev/input
```

### Step 7: Test Configuration

```bash
# Test that config loads
python3 -c "import foos.config; print('Config OK')"

# Try running (may fail on OpenGL, but verifies imports)
python3 foos.py -s 3
```

**Expected Behavior:**
- On x86_64 without proper OpenGL ES setup, the application may fail when initializing pi3d
- This is normal - the core logic can still be tested and developed
- For full GUI testing, use a Raspberry Pi or set up proper OpenGL ES emulation

---

## Configuration

The `config.py` file controls all aspects of the foos application. It overrides defaults from `config_base.py`.

### Basic Configuration Structure

```python
""" Override config values from config_base using this file """
from config_base import *

# Your customizations go here
```

### Plugin Configuration

Plugins provide different features. Enable/disable by modifying the `plugins` set:

```python
# Default plugins (always loaded)
plugins = set(['score', 'game', 'sound', 'io_debug', 'menu', 'control', 'league', 'leds'])

# Enable camera and replay features
plugins.add('replay')
plugins.add('camera')
plugins.add('motiondetector')

# Enable YouTube uploads
plugins.add('upload')

# Enable HipChat/Slack notifications
plugins.add('hipbot')

# Enable Arduino serial communication
plugins.add('io_serial')

# Enable Raspberry Pi GPIO (for buttons and sensors)
plugins.add('io_raspberry')

# Enable automatic TV standby
plugins.add('standby')
```

### GPIO Pin Configuration (Raspberry Pi only)

If using `io_raspberry` plugin, configure your GPIO pins:

```python
plugins.add('io_raspberry')

# Pin numbers in BCM mode
io_raspberry_pins = {
    "irbarrier_team_black": 8,      # Goal sensor - black team
    "irbarrier_team_yellow": 26,    # Goal sensor - yellow team
    "yellow_plus": 10,              # Score + button - yellow
    "yellow_minus": 16,             # Score - button - yellow
    "black_plus": 3,                # Score + button - black
    "black_minus": 22,              # Score - button - black
    "ok_button": 24,                # OK/confirm button
}

# PWM output for IR LED is always BCM18 (hardware PWM)
```

### Camera Configuration

```python
# Enable camera plugins
plugins.update(set(['replay', 'camera', 'motiondetector']))

# Camera resolution (adjust to your display aspect ratio)
video_size = (1280, 720)  # 16:9 aspect ratio
# video_size = (1152, 720)  # 16:10 aspect ratio

# Camera framerate
video_fps = 49  # Must be 49 for 720p on Pi Camera v2

# Camera preview window position and size
camera_preview = "-p 0,0,128,72"  # x,y,width,height

# Exposure compensation (-10 to +10)
camera_extra_params = "--ev 7"

# Replay settings
replay_path = '/dev/shm/replay'
replay_fps = 25
short_chunks = 10  # seconds of pre-roll
long_chunks = 25   # seconds of post-roll
```

### Team Customization

```python
# Change team names
team_names = {"yellow": "blue", "black": "red"}

# Change team colors (RGB values 0.0-1.0)
team_colors = {
    "yellow": (0.1, 0.1, 0.4),  # Dark blue
    "black": (0.7, 0, 0)         # Dark red
}
```

### Game Modes

```python
# Game modes shown in the menu
# Format: (winning_score, timeout_in_minutes)
game_modes = [
    (None, None),  # Free play (no score limit, no timeout)
    (3, None),     # First to 3
    (5, None),     # First to 5
    (10, None),    # First to 10
    (3, 120)       # First to 3, with 2-hour timeout
]
```

### YouTube Upload Configuration

```python
# Enable upload plugin
plugins.add('upload')

# You'll need to:
# 1. Create a Google Cloud project
# 2. Enable YouTube Data API v3
# 3. Create OAuth 2.0 credentials
# 4. Download client_secrets.json

# Copy client_secrets.json.sample to client_secrets.json
# and fill in your OAuth credentials
```

### League Integration

```python
# Enable league sync
plugins.add('league_sync')

# League server settings
league_url = 'http://your-league-server:8888/api'
league_apikey = 'your-api-key-here'
league_dir = './league'  # Local cache directory
```

### HipChat/Slack Integration

```python
# For HipChat (deprecated)
plugins.add('hipbot')
hipchat_token = 'your_hipchat_token'
hipchat_room = 'your_room_id'

# For Slack
slack_webhook = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
```

### UI Configuration

```python
# Clock format (strftime format)
clock_format = "%H:%M"      # 24-hour format
# clock_format = "%-I:%M %p"  # 12-hour format with AM/PM

# Background change interval (seconds)
bg_change_secs = 300  # 5 minutes

# Standby timeout (seconds)
standby_timeout_secs = 600  # 10 minutes

# Show onscreen LEDs (for testing without hardware)
onscreen_leds_enabled = True

# Use dispmanx for background (Raspberry Pi only)
draw_bg_with_dispmanx = True
```

---

## Testing

### Check Script

Always run the check script after making changes:

```bash
cd ~/foos
./check
```

This verifies:
- ✅ All required binaries are installed
- ✅ Shared libraries are available
- ✅ Raspberry Pi components are functional
- ✅ Replay directory is configured correctly
- ✅ GPU has enough memory
- ✅ Permissions are correct

### Manual Testing

#### Test 1: Config Loading
```bash
python3 -c "import foos.config as config; print('Plugins:', config.plugins)"
```

Expected output:
```
Plugins: {'game', 'leds', 'io_debug', 'score', 'control', 'league', 'menu', 'sound'}
```

#### Test 2: Import All Modules
```bash
python3 -c "
from foos.bus import Bus
from foos.plugin_handler import PluginHandler
print('All imports successful')
"
```

#### Test 3: Camera Test (Raspberry Pi only)
```bash
# Test that camera works
raspivid -t 5000 -o /tmp/test.h264

# Play the test video
omxplayer /tmp/test.h264
```

#### Test 4: GPIO Test (Raspberry Pi only)
```bash
# Test GPIO access
python3 << 'EOF'
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
print("GPIO test successful")
GPIO.cleanup()
EOF
```

### Integration Tests

The project includes integration tests in `test_client_integration.py`:

```bash
# Note: These tests may need path adjustments
python3 test_client_integration.py
```

---

## Running the Application

### On Raspberry Pi (Full Experience)

```bash
cd ~/foos

# Run with default settings (full screen)
python3 foos.py

# Or use the convenience script
./foos.sh
```

**Controls (Keyboard):**
- `q, e, KP7, KP9`: Increment score (left/right team)
- `z, c, KP1, KP3`: Decrement score (left/right team)
- `s, KP5`: OK/Select in menus
- `a, d, KP4, KP6`: Simulate goal (for testing)
- `.` (period): Exit application

### On x86_64 (Development Mode)

```bash
cd ~/foos

# Run in windowed mode with scaling
DISPLAY=:0 python3 foos.py -s 3

# -s 3 = scale to 1/3 size (makes window smaller)
# -f 25 = set framerate to 25 fps
```

**Note:** X11 mode is primarily for development. Some features won't work without Raspberry Pi hardware:
- Camera/replay (no Pi camera)
- GPIO (no Pi GPIO pins)
- Hardware video decoding

### Start on Boot (Raspberry Pi)

To have foos start automatically when the Pi boots:

```bash
# Edit rc.local
sudo nano /etc/rc.local

# Add before 'exit 0':
sudo -u pi /home/pi/foos/foos.sh &

# Save and exit
```

Alternative: Create a systemd service:

```bash
sudo tee /etc/systemd/system/foos.service << 'EOF'
[Unit]
Description=Foos Foosball Scoreboard
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/foos
ExecStart=/usr/bin/python3 /home/pi/foos/foos.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable foos.service
sudo systemctl start foos.service

# Check status
sudo systemctl status foos.service
```

---

## Troubleshooting

### Problem: Rainbow Square in Corner of Screen

**Symptom:** A small rainbow square appears in the top-right corner of the display.

**Cause:** Under-voltage warning from the Raspberry Pi.

**Solution:** Use a better power supply that can deliver stable 5V at 2.5A+ (3A for Pi 3).
- Official Raspberry Pi power supply recommended
- Use short, good quality USB cable

### Problem: Replay Video Doesn't Show

**Symptom:** After a goal, the screen stays on the score display instead of showing replay.

**Cause:** Insufficient GPU memory or missing video player.

**Solution:**
1. Check GPU memory: `vcgencmd get_mem gpu`
   - Should be 256MB (minimum 192MB)
   - Change with `sudo raspi-config` → Performance Options → GPU Memory

2. Verify video player is built:
   ```bash
   ls -lh ~/foos/video/player/player
   # Should exist and be executable
   ```

3. Check replay files are being created:
   ```bash
   ls -lh /dev/shm/replay/fragments/
   # Should contain *.h264 files during recording
   ```

### Problem: UI Elements Show as Gray/Black Boxes

**Cause:** Insufficient GPU memory or texture loading issues.

**Solution:**
- Increase GPU memory to 256MB (see above)
- Check that image files exist:
  ```bash
  ls -lh ~/foos/img/
  ```

### Problem: Camera Not Working

**Error:** `mmal: Failed to create camera component`

**Solutions:**
1. Enable legacy camera interface:
   ```bash
   sudo raspi-config
   # → Interface Options → Legacy Camera → Yes
   sudo reboot
   ```

2. Verify camera is connected:
   ```bash
   vcgencmd get_camera
   # Should show: supported=1 detected=1
   ```

3. Test camera manually:
   ```bash
   raspivid -t 5000 -o /tmp/test.h264
   ```

### Problem: Python Import Errors

**Error:** `ModuleNotFoundError: No module named 'pi3d'`

**Solution:**
```bash
# Reinstall requirements
cd ~/foos
pip3 install --break-system-packages -r requirements.txt

# Check what's installed
pip3 list | grep pi3d
```

### Problem: Permission Denied on /dev/input

**Error:** `PermissionError: [Errno 13] Permission denied: '/dev/input/event0'`

**Solution:**
```bash
# Add user to input group
sudo usermod -a -G input $USER

# Log out and back in, or reboot
sudo reboot
```

### Problem: RPi.GPIO Errors on Newer Pi OS

**Error:** `RuntimeError: Cannot determine SOC peripheral base address`

**Solution:**
```bash
# Remove old RPi.GPIO
pip3 uninstall -y RPi.GPIO --break-system-packages

# Install rpi-lgpio (drop-in replacement)
pip3 install --break-system-packages rpi-lgpio
```

### Problem: Display Tearing or Blank Screen

**Cause:** Dispmanx layer conflicts.

**Solutions:**

1. Disable dispmanx background in `config.py`:
   ```python
   draw_bg_with_dispmanx = False
   ```

2. Or force blank the console before starting:
   ```bash
   sudo sh -c "setterm -term linux -blank force >/dev/tty0 </dev/tty0"
   python3 foos.py
   ```

3. Or try offline compositing in `/boot/config.txt`:
   ```
   dispmanx_offline=1
   ```

### Problem: Replay Doesn't Fill Screen

**Cause:** Video aspect ratio doesn't match display.

**Solution:** Adjust `video_size` in `config.py`:
```python
# For 16:10 monitors
video_size = (1152, 720)
camera_preview = "-p 0,0,115,72"

# For 16:9 monitors (default)
video_size = (1280, 720)
camera_preview = "-p 0,0,128,72"

# For 4:3 monitors
video_size = (960, 720)
camera_preview = "-p 0,0,96,72"
```

### Problem: Sound Not Playing

**Solutions:**
```bash
# Install sox if missing
sudo apt-get install sox

# Test sound manually
play ~/foos/sounds/goal.wav

# Check ALSA config
aplay -l  # List sound devices
```

### Getting More Help

1. **Check Logs:**
   ```bash
   tail -f /dev/shm/foos_event.log
   ```

2. **Run with Debug Output:**
   ```bash
   python3 foos.py 2>&1 | tee foos_debug.log
   ```

3. **Consult Documentation:**
   - [Hardware Setup](doc/HWSetup.md)
   - [UI Guide](doc/ui/ui.md)
   - [Troubleshooting](doc/Troubleshooting.md)

4. **Check GitHub Issues:**
   - https://github.com/swehner/foos/issues

---

## Next Steps

### Hardware Setup

See [doc/HWSetup.md](doc/HWSetup.md) for detailed instructions on:
- Building IR barrier goal sensors
- Wiring buttons to GPIO pins
- Mounting the camera
- Arduino integration
- TV mounting and positioning

### UI Customization

Explore the UI configuration options in [doc/ui/ui.md](doc/ui/ui.md):
- Custom backgrounds
- Team colors and names
- Custom sounds
- Display layouts

### Plugin Development

Create your own plugins to extend functionality:
- Study existing plugins in `plugins/` directory
- See `plugins/io_debug.py` for a minimal example
- Plugins use an event bus architecture (see `foos/bus.py`)

### League Integration

Set up the league server for tournament management:
- https://github.com/swehner/foos-tournament
- Tracks player rankings and statistics
- Manages tournaments and seasons

### Advanced Features

Once basic setup is complete, explore:
- **YouTube Upload**: Automatically upload replays to YouTube
- **Motion Detection**: Detect when players leave the table
- **Slack Integration**: Post game results to Slack
- **Custom Game Modes**: Add your own scoring rules
- **Multi-table Setup**: Network multiple tables together

---

## Summary Checklist

### Raspberry Pi Setup
- [ ] Install Raspberry Pi OS
- [ ] Update system packages
- [ ] Clone foos repository
- [ ] Create replay directory structure
- [ ] Configure Pi (camera, GPU memory)
- [ ] Install Python dependencies
- [ ] Build video player
- [ ] Create config.py
- [ ] Run ./check and fix issues
- [ ] Test application
- [ ] Configure autostart (optional)
- [ ] Wire hardware components
- [ ] Calibrate sensors

### x86_64 Development Setup
- [ ] Install system dependencies
- [ ] Clone foos repository
- [ ] Create replay directory
- [ ] Install Python dependencies
- [ ] Create RPi.GPIO mock
- [ ] Create config.py (minimal plugins)
- [ ] Test imports
- [ ] Begin development

---

## Appendix: File Structure

```
foos/
├── foos.py                 # Main entry point
├── config.py               # Your configuration (create from sample)
├── config.py.sample        # Configuration template
├── config_base.py          # Default configuration
├── requirements.txt        # Python dependencies
├── setup-trixie.sh        # Automated setup for Debian Trixie
├── check                  # System check script
├── boot.sh                # Boot script
├── foos.sh                # Convenience launch script
├── main.sh                # Alternative launch script
├── Readme.md              # Project overview
├── SETUP_GUIDE.md         # This file
├── LICENSE.TXT            # License information
├── Changelog.md           # Version history
│
├── foos/                  # Main Python package
│   ├── __init__.py
│   ├── bus.py             # Event bus system
│   ├── config.py          # Config loader
│   ├── platform.py        # Platform detection
│   ├── plugin_handler.py  # Plugin loader
│   ├── ui/                # UI components
│   └── ...
│
├── plugins/               # Plugin modules
│   ├── camera.py          # Camera capture
│   ├── replay.py          # Replay system
│   ├── game.py            # Game logic
│   ├── score.py           # Score tracking
│   ├── io_raspberry.py    # GPIO input/output
│   ├── io_serial.py       # Arduino serial communication
│   ├── io_keyboard.py     # X11 keyboard input
│   ├── io_evdev_keyboard.py  # Direct keyboard input
│   ├── upload.py          # YouTube upload
│   ├── hipbot.py          # HipChat integration
│   └── ...
│
├── video/                 # Video handling
│   ├── player/            # Custom video player
│   │   ├── Makefile
│   │   └── player.c
│   └── replay.sh          # Replay script
│
├── doc/                   # Documentation
│   ├── Installation.md    # Original install guide
│   ├── HWSetup.md         # Hardware setup
│   ├── Troubleshooting.md # Common issues
│   ├── ui/                # UI documentation
│   └── *.jpg              # Photos and diagrams
│
├── img/                   # UI images
│   ├── backgrounds/       # Background images
│   ├── buttons/           # Button graphics
│   └── ...
│
├── sounds/                # Sound effects
│   ├── goal.wav
│   └── ...
│
├── arduino/               # Arduino sketches
│   └── ...
│
└── tools/                 # Utility scripts
    └── ...
```

---

## Credits

**Team:**
- Jesús Bravo
- Daniel Pañeda
- Stefan Wehner

**Thanks to:**
- Tuenti, where this project started
- Laura Andina for UI design
- Adam Bartha for the Pi-only version
- Steve Brockman for the Arduino micro version
- The Pi3d team

**Built with:**
- [Pi3d](https://pi3d.github.io/) - Python 3D graphics library
- Raspberry Pi hardware
- OpenGL ES
- Love for foosball ⚽🏓

---

## License

See [LICENSE.TXT](LICENSE.TXT) for details.

---

**Last Updated:** 2025-11-12
**Version:** 1.0
**Author:** Setup Guide created for complete project setup documentation
