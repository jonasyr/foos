#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?Usage: replay.sh <file> [fps]}"; FPS="${2:-25}"

# Ensure DISPLAY is set for X11
export DISPLAY=${DISPLAY:-:0}

# Try to use hardware-accelerated players first, then fallback to software
if command -v omxplayer >/dev/null 2>&1; then 
    # Legacy hardware player (if available)
    omxplayer --blank --layer 10000 "$FILE" </dev/null
elif command -v mpv >/dev/null; then 
    # MPV with hardware acceleration, fullscreen, on top, no GUI elements
    mpv --fs --no-osc --no-osd-bar --keep-open=no --ontop --no-border \
        --no-input-default-bindings --really-quiet "$FILE" </dev/null
elif command -v cvlc >/dev/null; then 
    # VLC command line with minimal interface
    cvlc --play-and-exit --fullscreen --no-video-title-show --no-osd \
         --no-video-deco --quiet "$FILE" </dev/null 2>&1
elif command -v vlc >/dev/null; then 
    vlc --play-and-exit --fullscreen --no-video-title-show --no-osd \
        --no-video-deco --quiet "$FILE" </dev/null 2>&1
elif command -v ffplay >/dev/null; then 
    # ffplay with fullscreen, no decorations
    ffplay -autoexit -fs -framerate "$FPS" -noborder -left 0 -top 0 \
           -window_title "" "$FILE" </dev/null 2>&1
else 
    echo "ERROR: No video player found (tried: omxplayer, mpv, vlc, ffplay)" >&2
    exit 1
fi

