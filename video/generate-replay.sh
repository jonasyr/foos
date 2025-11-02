#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-/dev/shm/replay}"; IGN="${2:-1}"; LONG="${3:-25}"; SHORT="${4:-10}"
FR="$BASE/fragments"; mkdir -p "$BASE"
mapfile -t ALL < <(ls -1t "$FR"/out*.h264 2>/dev/null || true)
(( ${#ALL[@]} )) || { echo "No fragments"; exit 0; }
# long
cat "${ALL[@]:$IGN:$LONG}" > "$BASE/replay_long.h264" 2>/dev/null || true
# short
cat "${ALL[@]:$IGN:$SHORT}" > "$BASE/replay_short.h264" 2>/dev/null || true
# Rewrap
command -v ffmpeg &>/dev/null && \
  [[ -f "$BASE/replay_short.h264" ]] && ffmpeg -y -framerate 25 -i "$BASE/replay_short.h264" -c copy "$BASE/replay_short.mp4" &>/dev/null
command -v ffmpeg &>/dev/null && \
  [[ -f "$BASE/replay_long.h264"  ]] && ffmpeg -y -framerate 25 -i "$BASE/replay_long.h264"  -c copy "$BASE/replay_long.mp4"  &>/dev/null
