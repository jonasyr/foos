# Quick Start Guide - Foos Setup

This is a condensed version of the full setup guide. For complete details, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## TL;DR for Raspberry Pi (Debian Trixie/Bookworm)

```bash
# 1. Clone and enter directory
git clone https://github.com/swehner/foos.git
cd foos

# 2. Run automated setup (Raspberry Pi only)
./setup-trixie.sh

# 3. Configure
cp config.py.sample config.py
nano config.py  # Edit as needed

# 4. Verify
./check

# 5. Run
python3 foos.py
```

## TL;DR for x86_64 Development

```bash
# 1. Clone
git clone https://github.com/swehner/foos.git
cd foos

# 2. Install dependencies
sudo apt-get install -y python3-pip libopenblas-dev
pip3 install --break-system-packages pi3d numpy Pillow pygame evdev

# 3. Create RPi.GPIO mock
sudo mkdir -p /usr/local/lib/python3.11/dist-packages/RPi
# See SETUP_GUIDE.md for full mock code

# 4. Setup directories and config
mkdir -p /dev/shm/replay/fragments
cp config.py.sample config.py

# 5. Run in test mode
python3 foos.py -s 3
```

## What Was Done in This Setup

### Files Created
- ✅ `config.py` - Configuration file (from sample)
- ✅ `/dev/shm/replay/fragments/` - Video replay storage
- ✅ `/usr/local/lib/python3.11/dist-packages/RPi/GPIO.py` - GPIO mock for x86_64
- ✅ `SETUP_GUIDE.md` - Complete setup documentation
- ✅ `QUICKSTART.md` - This file

### Packages Installed
- ✅ pi3d (3D graphics library)
- ✅ numpy (numerical computing)
- ✅ Pillow (image processing)
- ✅ pygame (for X11 mode)
- ✅ google-api-python-client (YouTube uploads)
- ✅ evdev (keyboard input)
- ✅ pyserial (Arduino communication)
- ✅ inotify_simple (file watching)
- ✅ requests (HTTP client)

### System Configuration
- ✅ Replay directory created in tmpfs
- ✅ RPi.GPIO mock for non-Pi systems
- ✅ Python dependencies installed

## Next Steps

1. **On Raspberry Pi:**
   - Configure camera and GPIO pins in `config.py`
   - Wire physical buttons and sensors
   - Enable plugins (replay, camera, etc.)
   - Run `./check` to verify hardware
   - Test with `python3 foos.py`

2. **On x86_64:**
   - Disable hardware plugins in `config.py`
   - Test core logic and game modes
   - Develop new features
   - Test with `python3 foos.py -s 3`

3. **For Both:**
   - Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed configuration
   - See [doc/HWSetup.md](doc/HWSetup.md) for hardware assembly
   - Check [doc/Troubleshooting.md](doc/Troubleshooting.md) for common issues

## Current System Status

Run the check script to see what's configured:
```bash
./check
```

## Configuration Quick Reference

Edit `config.py` to customize:

```python
from config_base import *

# Enable features by adding plugins
plugins.add('camera')      # Enable camera
plugins.add('replay')      # Enable replay system
plugins.add('upload')      # Enable YouTube upload
plugins.add('io_raspberry') # Enable GPIO (Pi only)

# Configure team names
team_names = {"yellow": "blue", "black": "red"}

# Configure GPIO pins (Pi only)
io_raspberry_pins = {
    "irbarrier_team_black": 8,
    "irbarrier_team_yellow": 26,
    # ... see SETUP_GUIDE.md for full list
}
```

## Keyboard Controls (X11 and Pi)

- **Score +**: `q` (left), `e` (right)
- **Score -**: `z` (left), `c` (right)
- **OK/Select**: `s`
- **Simulate Goal**: `a` (left), `d` (right)
- **Exit**: `.` (period)

## Help & Documentation

- **Full Setup Guide**: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Hardware Setup**: [doc/HWSetup.md](doc/HWSetup.md)
- **Troubleshooting**: [doc/Troubleshooting.md](doc/Troubleshooting.md)
- **Project README**: [Readme.md](Readme.md)
- **GitHub Issues**: https://github.com/swehner/foos/issues

## Common Issues

### Import Error: No module named 'pi3d'
```bash
pip3 install --break-system-packages -r requirements.txt
```

### OpenGL Error on x86_64
This is expected - pi3d requires OpenGL ES which may not be available. The application is designed for Raspberry Pi hardware.

### Permission Denied: /dev/input
```bash
sudo usermod -a -G input $USER
# Log out and back in
```

### Camera Not Working (Pi)
```bash
sudo raspi-config
# → Interface Options → Legacy Camera → Enable
sudo reboot
```

---

**For complete setup instructions and troubleshooting, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**
