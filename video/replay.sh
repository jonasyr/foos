#!/usr/bin/env bash
set -euo pipefail
FILE="${1:?Usage: replay.sh <file> [fps]}"; FPS="${2:-25}"
if command -v cvlc >/dev/null; then cvlc --play-and-exit --fullscreen "$FILE"; 
elif command -v vlc >/dev/null; then vlc --play-and-exit --fullscreen "$FILE";
elif command -v ffplay >/dev/null; then ffplay -autoexit -fs -framerate "$FPS" "$FILE";
elif command -v mpv    >/dev/null; then mpv --fs "$FILE"; else echo "no player"; exit 1; fi

