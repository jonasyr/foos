# Troubleshooting

### The rainbow box appears in the upper right corner

This is Raspberry PI under-power warning - it means that your power supply is not delivering 5V. Try a supply with a higher power rating. See here for recommendations:
https://www.raspberrypi.org/help/faqs/#power

### When the replay is supposed to show nothing appears on screen and the score counters don't go back to their original position

This is most likely because you don't have enough RAM assigned to your GPU. See next question.

### Some UI elements are not drawn correctly and show as gray/black boxes instead

This is most likely because you don't have enoguh RAM assigned to your GPU. We recommend 256MB. Use raspi-config to change it.

### The player blacks out after a few seconds or video shows tearing

This could be related to issues with dispmanx compositing:
Check if you have enabled drawing the background as a dispmanx layer in the config:
```
draw_bg_with_dispmanx = True
```

You can disable it in config (it is False by default) - if you still want to do it as a dispmanx layer there are several options to fixing this problem.
A solution to this problem is reducing the dispmanx layers - you have several options for that:

You can turn off the framebuffer doing the following before launching foos.py. This is done automatically when starting it from the console, but if you've started if through ssh you need root permissions to do this:
```
sudo sh -c "setterm -term linux -blank force >/dev/tty0 </dev/tty0"
```
Or you can use tvservice to disable and reenable HDMI output:

```
tvservice -o; tvservice -p
```

To get the console back you can run:
```
sudo sh -c "setterm -term linux -blank poke >/dev/tty0 </dev/tty0"
```

Another option is to disable the camera preview in config.py:
```
camera_preview="-n"
```

If none of these work you can try enabling offline compositing in dispmanx in /boot/config.txt (reboot required!):
```
dispmanx_offline=1
```

### Replay video doesn't cover full screen

Probably your screen doesn't have a 16/9 aspect ratio.
You can configure the recording size in config.py. This is the config I use for a 16/10 monitor:

```
video_size=(1152, 720)
camera_preview="-p 0,0,115,72"
```

## Raspberry Pi 4: Video Overlay Not Working

### Symptoms
- Replay video covers entire screen instead of showing UI overlay
- Score counters disappear during replay instead of moving to top-right corner
- UI completely hidden when replay plays

### Background

Raspberry Pi 4 uses a different GPU architecture (VideoCore VI vs VideoCore IV) and doesn't support the OpenMAX IL player used on Pi 0-3. The new implementation uses MPV with KMS/DRM hardware planes to achieve layered compositing:
- **Layer 0 (overlay plane):** Video playback
- **Layer 1 (primary plane):** Pi3D UI rendering

### Diagnosis

```bash
# Check if MPV has DRM support
mpv --vo=help | grep drm

# Verify KMS is enabled
dmesg | grep -i drm

# List available display planes
sudo modetest -M vc4 -p
```

### Solutions

#### 1. Ensure KMS is Enabled

```bash
# Edit boot config
sudo nano /boot/firmware/config.txt

# Add or verify these lines:
dtoverlay=vc4-kms-v3d
dtparam=audio=on

# Reboot
sudo reboot
```

#### 2. Install MPV with Full DRM Support

```bash
sudo apt-get update
sudo apt-get install --reinstall mpv libmpv2
```

#### 3. Test Video Overlay Manually

```bash
# Start foos in background
./foos.sh start

# Test replay with explicit DRM
mpv --vo=gpu --gpu-context=drm \
    --drm-draw-plane=overlay \
    /dev/shm/replay/replay_long.mp4
```

**Expected:** Video should play, but your terminal/UI should still be visible (not covered).

#### 4. Check Display Connector

Different Pi 4 boards may use different HDMI connector names:

```bash
# List available connectors
sudo modetest -M vc4 -c

# Common connector names:
# - HDMI-A-1 (HDMI port 0)
# - HDMI-A-2 (HDMI port 1)
```

If your display is on a different connector, edit `video/replay.sh` and update the `--drm-connector=` parameter.

#### 5. Verify Display Layer Configuration

The Pi3D display must be created with `layer=1` to render above the video. This should already be configured in `foos/ui/ui.py:303` and `foos/ui/ui.py:313`. Verify:

```bash
grep -n "layer=1" foos/ui/ui.py
```

**Expected output:**
```
303:            self.DISPLAY = pi3d.Display.create(background=bgcolor, layer=1, use_pygame=True)
313:            self.DISPLAY = pi3d.Display.create(x=0, y=0, w=int(self.width / sf), h=int(self.height / sf),
```

### Fallback Behavior

If overlay planes are not available on your hardware, the script will fall back to standard DRM mode:
- Video will still play smoothly
- UI may be covered (like the old behavior)
- This is acceptable but not ideal

### Testing Full Integration

```bash
# Start foos application
DISPLAY=:0 python3 foos.py

# From GPIO buttons or keyboard:
# 1. Press OK button (short press) to open menu
# 2. Select a game mode
# 3. Score a goal (triggers auto-replay)
# OR
# 4. Press OK button (long press ~1 second) to trigger manual replay

# Expected behavior:
# - Video plays full screen
# - Score counters shrink and move to top-right corner
# - Score counters remain visible during entire replay
# - After replay, score counters return to center
```

### Monitoring Overlay Mode

```bash
# Monitor bus events while testing
tail -f /tmp/foos.log | grep -E "replay_start|overlay_mode"

# Should see:
# - "overlay_mode = True" when replay starts
# - Score counter position changes
# - "overlay_mode = False" when replay ends
```

### Common Issues

**MPV not found:**
```bash
sudo apt-get install mpv
```

**Permission denied on /dev/dri/card0:**
```bash
# Add your user to the video group
sudo usermod -a -G video $USER
# Log out and log back in
```

**Screen flickers or tears:**
- Reduce GPU memory allocation in `/boot/firmware/config.txt`
- Try `gpu_mem=128` instead of higher values
- KMS uses less GPU memory than legacy firmware

**No audio in replay:**
- This is expected behavior - the `--no-audio` flag is intentional
- Original system didn't have replay audio either
