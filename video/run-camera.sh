#!/usr/bin/env bash
set -euo pipefail
REPLAY_PATH=$(python3 -c 'import config; print(getattr(config,"replay_path","/dev/shm/replay"))' 2>/dev/null || echo "/dev/shm/replay")
W=$(python3 -c 'import config; print(getattr(config,"video_size",(1280,720))[0])' 2>/dev/null || echo 1280)
H=$(python3 -c 'import config; print(getattr(config,"video_size",(1280,720))[1])' 2>/dev/null || echo 720)
FPS=$(python3 -c 'import config; print(getattr(config,"video_fps",25))' 2>/dev/null || echo 25)

mkdir -p "$REPLAY_PATH/fragments"
# Note: --save-pts with %05d pattern not supported in rpicam-vid 1.9.1 with --segment
exec rpicam-vid --codec h264 --width "$W" --height "$H" --framerate "$FPS" --inline \
  --nopreview --segment 4000 \
  --output "$REPLAY_PATH/fragments/out%05d.h264" --timeout 0

