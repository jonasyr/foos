#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?Usage: replay.sh <file> [fps]}"; FPS="${2:-25}"

# Ensure DISPLAY is set for Pi3D compatibility
export DISPLAY=${DISPLAY:-:0}

# Use MPV with DRM/KMS on hardware overlay plane (below Pi3D)
if command -v mpv >/dev/null; then
    # Primary strategy: Use DRM with explicit overlay plane
    # --drm-draw-plane=overlay puts video beneath the primary plane (where Pi3D renders)
    mpv --vo=gpu --gpu-context=drm \
        --drm-connector=HDMI-A-1 \
        --drm-draw-plane=overlay \
        --drm-draw-surface-size=1920x1080 \
        --fs --no-osc --no-osd-bar --keep-open=no \
        --no-input-default-bindings --really-quiet \
        --untimed --no-audio \
        "$FILE" </dev/null 2>&1 || {

        # Fallback: Try without explicit plane (may still work)
        echo "Trying MPV DRM fallback..." >&2
        mpv --vo=gpu --gpu-context=drm \
            --drm-connector=HDMI-A-1 \
            --fs --no-osc --no-osd-bar --keep-open=no \
            --no-input-default-bindings --really-quiet \
            --untimed --no-audio \
            "$FILE" </dev/null 2>&1
    }
elif command -v cvlc >/dev/null; then
    # VLC fallback with KMS backend
    cvlc --play-and-exit --fullscreen \
         --vout=drm --drm-vout-display=HDMI-A-1 \
         --no-video-title-show --no-osd \
         --no-video-deco --quiet "$FILE" </dev/null 2>&1
elif command -v vlc >/dev/null; then
    vlc --play-and-exit --fullscreen \
        --vout=drm --drm-vout-display=HDMI-A-1 \
        --no-video-title-show --no-osd \
        --no-video-deco --quiet "$FILE" </dev/null 2>&1
else
    echo "ERROR: No suitable video player found (need mpv or vlc with DRM support)" >&2
    exit 1
fi

