#!/bin/bash
# AutoCaption pipeline: video in -> transcribe (whisper) -> burn captions -> "<name> (captioned).mp4"
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

APPDIR="$HOME/Library/Application Support/AutoCaption"
MODEL="$APPDIR/ggml-small.bin"
FFMPEG="$(command -v ffmpeg)"
WHISPER="$(command -v whisper-cli)"
PYTHON="$APPDIR/venv/bin/python3"

notify() {
  /usr/bin/osascript -e "display notification \"$2\" with title \"AutoCaption\" subtitle \"$1\"" || true
}

VIDEO="$1"
BASE="$(basename "$VIDEO")"
NAME="${BASE%.*}"
DIR="$(dirname "$VIDEO")"
OUT="$DIR/$NAME (captioned).mp4"
LOG="$APPDIR/last_run.log"

{
  echo "=== $(date) — $VIDEO ==="
  notify "$BASE" "Transcribing… this takes a minute or two."

  WORK="$(mktemp -d /tmp/autocaption.XXXXXX)"
  trap 'rm -rf "$WORK"' EXIT

  "$FFMPEG" -y -v error -i "$VIDEO" -ar 16000 -ac 1 -c:a pcm_s16le "$WORK/audio.wav"
  "$WHISPER" -m "$MODEL" -f "$WORK/audio.wav" -l auto -osrt -sow -ml 1 -of "$WORK/captions"

  notify "$BASE" "Burning captions into the video…"
  "$PYTHON" "$APPDIR/render_captions.py" "$VIDEO" "$WORK/captions.srt" "$OUT"

  # keep the SRT next to the video too, in case they want to edit/reuse it
  cp "$WORK/captions.srt" "$DIR/$NAME.srt" || true

  notify "$BASE" "Done! Saved as: $NAME (captioned).mp4"
  echo "OK -> $OUT"
} >"$LOG" 2>&1 || {
  notify "$BASE" "Failed — see last_run.log in the AutoCaption folder."
  exit 1
}
