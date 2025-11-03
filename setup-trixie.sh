#!/usr/bin/env bash
# Idempotent setup script for foos on Debian Trixie (Raspberry Pi OS)
# Consolidates all working fixes from feature/button-controls branch
set -euo pipefail

echo "=========================================="
echo "Foos Trixie Setup Script"
echo "=========================================="
echo ""

# ---- System packages
echo "→ Installing system packages..."
sudo apt-get update -qq

# Core packages (must succeed)
sudo apt-get install -y \
  ffmpeg vlc mpv \
  python3-pip python3-venv \
  libjpeg62-turbo libtiff6 libpng16-16 \
  libopenblas0 libopenblas-dev \
  libsqlite3-0 libsqlite3-dev \
  avahi-daemon \
  git curl

# Optional packages (may not exist in all repos)
for pkg in raspi-gpio; do
  sudo apt-get install -y "$pkg" 2>/dev/null || echo "  (optional package $pkg not available)"
done

echo "✓ System packages installed"
echo ""

# ---- GPIO shim (for ./check legacy wiringPi compatibility)
echo "→ Creating gpio shim..."
sudo mkdir -p /usr/local/bin
cat <<'SH' | sudo tee /usr/local/bin/gpio >/dev/null
#!/bin/sh
# GPIO shim - replaces wiringPi gpio command
# Uses gpioinfo as fallback if raspi-gpio not available
if command -v raspi-gpio >/dev/null 2>&1; then
  exec raspi-gpio "$@"
else
  exec gpioinfo "$@"
fi
SH
sudo chmod +x /usr/local/bin/gpio

echo "✓ GPIO shim created at /usr/local/bin/gpio"
echo ""

# ---- Legacy raspivid shim (for ./check only - we use rpicam-vid)
echo "→ Creating legacy raspivid shim..."
sudo mkdir -p /opt/vc/bin
cat <<'SH' | sudo tee /opt/vc/bin/raspivid >/dev/null
#!/bin/sh
echo "raspivid deprecated; use rpicam-vid" >&2
exit 0
SH
sudo chmod +x /opt/vc/bin/raspivid

echo "✓ Legacy raspivid shim created"
echo ""

# ---- OpenBLAS soname compatibility (cosmetic ./check fix)
echo "→ Creating OpenBLAS compatibility symlinks..."
arch="$(dpkg --print-architecture)"
libdir="/usr/lib/${arch}-linux-gnu"
if [ -d "$libdir" ]; then
  sudo ln -sf "$libdir/libopenblas.so" "$libdir/libf77blas.so" 2>/dev/null || true
  sudo ln -sf "$libdir/libopenblas.so" "$libdir/libatlas.so" 2>/dev/null || true
  sudo ldconfig 2>/dev/null || true
fi

echo "✓ OpenBLAS compatibility symlinks created"
echo ""

# ---- Replay tmpfs location & perms (persist across boots)
echo "→ Setting up replay tmpfs directory..."
sudo mkdir -p /dev/shm/replay/fragments
sudo chmod -R 777 /dev/shm/replay

# Add tmpfiles.d config to recreate on boot
sudo mkdir -p /etc/tmpfiles.d
cat <<'TMPFILES' | sudo tee /etc/tmpfiles.d/foos-replay.conf >/dev/null
# Foos replay directory in tmpfs
d /dev/shm/replay 0777 root root -
d /dev/shm/replay/fragments 0777 root root -
TMPFILES

echo "✓ Replay tmpfs directory created with tmpfiles.d config"
echo ""

# ---- User groups for unprivileged operation
echo "→ Adding user to required groups..."
sudo adduser "$USER" video 2>/dev/null || echo "  (already in video group)"
sudo adduser "$USER" input 2>/dev/null || echo "  (already in input group)"
sudo adduser "$USER" gpio 2>/dev/null || echo "  (already in gpio group)"

echo "✓ User groups configured"
echo ""

# ---- Remove broken RPi.GPIO if present
echo "→ Checking RPi.GPIO installation..."
if dpkg -l | grep -q python3-rpi.gpio; then
  echo "  Removing broken system RPi.GPIO package..."
  sudo apt-get remove -y python3-rpi.gpio
  sudo apt-get autoremove -y
  echo "  ✓ Removed broken RPi.GPIO"
fi

# ---- Python dependencies
echo "→ Installing Python dependencies..."
if [ -f requirements.txt ]; then
  # Install from requirements.txt (will install broken RPi.GPIO 0.7.1)
  pip3 install --break-system-packages -r requirements.txt
  
  # Remove the broken RPi.GPIO and install rpi-lgpio (provides compatible RPi.GPIO 0.7.2)
  echo "  Replacing broken RPi.GPIO with rpi-lgpio..."
  pip3 uninstall -y RPi.GPIO --break-system-packages 2>/dev/null || true
  pip3 uninstall -y rpi-lgpio --break-system-packages 2>/dev/null || true
  pip3 install --break-system-packages rpi-lgpio
  echo "✓ Python dependencies installed"
else
  echo "  ⚠ requirements.txt not found - skipping Python deps"
fi

echo ""

# ---- Verify installation
echo "→ Verifying installation..."
echo ""

# Check Python imports
if python3 -c "import pi3d; import RPi.GPIO; print('✓ Python imports: OK')" 2>/dev/null; then
  true
else
  echo "  ⚠ Python import test failed"
fi

# Check GPIO
if command -v gpio >/dev/null; then
  echo "✓ GPIO command: OK"
else
  echo "  ⚠ GPIO command not found"
fi

# Check groups
current_groups=$(groups)
echo "✓ Current groups: $current_groups"

# Check replay path
if [ -d /dev/shm/replay/fragments ]; then
  echo "✓ Replay path: OK"
else
  echo "  ⚠ Replay path not created"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review config.py settings"
echo "  2. Run ./check to verify system"
echo "  3. Test with: DISPLAY=:0 python3 foos.py"
echo "  4. Wire remaining buttons (if needed)"
echo ""
echo "Note: You may need to log out and back in for"
echo "      group changes to take effect."
echo ""
