#!/bin/bash
# AutoCaption installer for macOS.
# Installs dependencies, the whisper speech model, and the "Auto Caption" drag-and-drop app.
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
APPDIR="$HOME/Library/Application Support/AutoCaption"
MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"

echo "==> AutoCaption installer"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it first from https://brew.sh then re-run this script."
  exit 1
fi

for pkg in ffmpeg whisper-cpp; do
  if ! brew list "$pkg" >/dev/null 2>&1; then
    echo "==> Installing $pkg (Homebrew)…"
    brew install "$pkg"
  else
    echo "==> $pkg already installed"
  fi
done

echo "==> Setting up app files in $APPDIR"
mkdir -p "$APPDIR"
cp "$REPO_DIR/src/caption.sh" "$REPO_DIR/src/render_captions.py" "$APPDIR/"
chmod +x "$APPDIR/caption.sh"

if [ ! -x "$APPDIR/venv/bin/python3" ]; then
  echo "==> Creating Python environment…"
  python3 -m venv "$APPDIR/venv"
fi
"$APPDIR/venv/bin/pip" install --quiet --upgrade pip Pillow

if [ ! -f "$APPDIR/ggml-small.bin" ]; then
  echo "==> Downloading speech-recognition model (~465 MB, one time)…"
  curl -L --progress-bar -o "$APPDIR/ggml-small.bin" "$MODEL_URL"
else
  echo "==> Speech model already present"
fi

echo "==> Building the Auto Caption app on your Desktop…"
osacompile -o "$HOME/Desktop/Auto Caption.app" "$REPO_DIR/src/droplet.applescript"

echo ""
echo "Done! Drag any video onto 'Auto Caption' on your Desktop."
echo "A captioned copy appears next to the original when it finishes."
