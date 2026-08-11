# Auto Caption

Drag a video onto the app — get it back with **word-by-word pop-in captions** burned in, CapCut-style, for free.

Each word pops onto the screen at the exact moment it's spoken. The word being said is highlighted in yellow, the rest are white with a black outline, so captions stay readable over any background.

- 100% free and runs **entirely on your Mac** — no uploads, no accounts, no subscriptions
- Works with any video (portrait or landscape, any resolution)
- Auto-detects the spoken language ([Whisper](https://github.com/ggml-org/whisper.cpp) speech recognition)
- Keeps original video quality and audio untouched
- Also saves a plain `.srt` subtitle file next to the video, in case you want to edit the text

## Install

Requires macOS with [Homebrew](https://brew.sh). In Terminal:

```bash
git clone https://github.com/Setopy/AutoCaption.git
cd AutoCaption
bash install.sh
```

The installer sets up [ffmpeg](https://ffmpeg.org) and [whisper.cpp](https://github.com/ggml-org/whisper.cpp), downloads the speech model (~465 MB, one time), and puts an **Auto Caption** app on your Desktop.

## Use

1. Drag any video file onto the **Auto Caption** app (or double-click it and choose a video).
2. Wait for the "Done!" notification — a couple of minutes for a short video.
3. Find `YourVideo (captioned).mp4` next to the original. The original is never modified.

## How it works

1. `ffmpeg` extracts the audio track
2. `whisper-cli` transcribes it with per-word timestamps
3. A small Python script renders each caption state as a transparent overlay and `ffmpeg` composites them back onto the video at high quality (CRF 15)

Everything lives in `~/Library/Application Support/AutoCaption`. If a run fails, check `last_run.log` in that folder.

## Customize

Edit `render_captions.py` (in the folder above, or in `src/` before installing):

- `YELLOW` — highlight color of the current word
- `MAX_WORDS` — words shown per phrase (default 4)
- `fsize` / `margin_bottom` — caption size and position

Re-run `bash install.sh` after editing files in `src/`.

## License

MIT
