#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-/dev/shm/replay}"; IGN="${2:-1}"; LONG="${3:-25}"; SHORT="${4:-10}"
FR="$BASE/fragments"; mkdir -p "$BASE"

# Get all fragments sorted by modification time (newest first)
# IGN=1 skips the most recent fragment to avoid incomplete tail
mapfile -t ALL < <(ls -1t "$FR"/out*.h264 2>/dev/null || true)
(( ${#ALL[@]} )) || { echo "No fragments"; exit 0; }

# Extract the fragments we want, then reverse to chronological order (oldest to newest)
mapfile -t LONG_FRAGS < <(printf '%s\n' "${ALL[@]:$IGN:$LONG}" | tac)
mapfile -t SHORT_FRAGS < <(printf '%s\n' "${ALL[@]:$IGN:$SHORT}" | tac)

# Concatenate in chronological order
cat "${LONG_FRAGS[@]}" > "$BASE/replay_long.h264" 2>/dev/null || true
cat "${SHORT_FRAGS[@]}" > "$BASE/replay_short.h264" 2>/dev/null || true
# Rewrap
command -v ffmpeg &>/dev/null && \
  [[ -f "$BASE/replay_short.h264" ]] && ffmpeg -y -framerate 25 -i "$BASE/replay_short.h264" -c copy "$BASE/replay_short.mp4" &>/dev/null
command -v ffmpeg &>/dev/null && \
  [[ -f "$BASE/replay_long.h264"  ]] && ffmpeg -y -framerate 25 -i "$BASE/replay_long.h264"  -c copy "$BASE/replay_long.mp4"  &>/dev/null
