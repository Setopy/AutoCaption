#!/usr/bin/env python3
"""Burn word-by-word pop-in captions into a video (CapCut karaoke style).

Takes a word-level SRT (whisper-cli -sow -ml 1: one word per entry).
Words pop in one at a time as spoken; the current word is yellow,
earlier words in the phrase are white, all with a black outline.

Usage: render_captions.py <video> <word_srt> <output>
"""
import os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

FFMPEG = shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/usr/local/bin/ffprobe"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]
FONT_PATH = next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
if FONT_PATH is None:
    raise SystemExit("no usable font found")

WHITE = (255, 255, 255, 255)
YELLOW = (255, 214, 0, 255)
BLACK = "black"

MAX_WORDS = 4      # words per phrase before starting a new one
GAP_BREAK = 0.7    # silence (s) that forces a new phrase


def parse_words(path):
    words = []
    for block in open(path, encoding="utf-8").read().strip().split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue

        def t2s(t):
            h, m, rest = t.split(":")
            s, ms = rest.split(",")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

        start, end = [t2s(x.strip()) for x in lines[1].split("-->")]
        text = " ".join(l.strip() for l in lines[2:]).strip()
        if not text:
            continue
        toks = text.split()
        step = (end - start) / len(toks)
        for i, tok in enumerate(toks):
            words.append([start + i * step, start + (i + 1) * step, tok])
    return words


def chunk_words(words):
    chunks, cur = [], []
    for w in words:
        if cur:
            gap = w[0] - cur[-1][1]
            ended = cur[-1][2].rstrip('"”')[-1:] in ".!?"
            if len(cur) >= MAX_WORDS or gap > GAP_BREAK or ended:
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def main(video, srt, output):
    dims = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", video],
        capture_output=True, text=True, check=True).stdout.strip().split(",")
    W, H = int(dims[0]), int(dims[1])

    fsize = max(20, round(min(W, H * 0.56) / 13))
    stroke = max(2, fsize // 9)
    lh = round(fsize * 1.3)
    strip_h = lh * 3
    margin_bottom = round(H * 0.10)
    max_w = W - 2 * round(W * 0.04)
    font = ImageFont.truetype(FONT_PATH, fsize)

    words = parse_words(srt)
    if not words:
        raise SystemExit("no words parsed from " + srt)
    chunks = chunk_words(words)

    tmp = tempfile.mkdtemp(prefix="autocaption_")
    meas = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    space_w = meas.textlength(" ", font=font)

    def layout(tokens):
        """Wrap tokens into lines, return centered (x, y) per token index."""
        lines, cur, cur_w = [], [], 0
        for idx, tok in enumerate(tokens):
            tw = meas.textlength(tok, font=font)
            add = tw if not cur else cur_w + space_w + tw
            if cur and add > max_w:
                lines.append((cur, cur_w))
                cur, cur_w = [(idx, tw)], tw
            else:
                cur.append((idx, tw))
                cur_w = add
        if cur:
            lines.append((cur, cur_w))
        placed = {}
        y = strip_h - len(lines) * lh
        for line, width in lines:
            x = (W - width) / 2
            for idx, tw in line:
                placed[idx] = (x, y)
                x += tw + space_w
            y += lh
        return placed

    inputs = ["-i", video]
    chains = []
    prev = "0:v"
    n = 0
    for chunk in chunks:
        tokens = [w[2] for w in chunk]
        placed = layout(tokens)
        for i in range(len(chunk)):
            img = Image.new("RGBA", (W, strip_h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            for j in range(i + 1):
                x, y = placed[j]
                d.text((x, y), tokens[j], font=font,
                       fill=YELLOW if j == i else WHITE,
                       stroke_width=stroke, stroke_fill=BLACK)
            p = os.path.join(tmp, f"c{n:04d}.png")
            img.save(p)
            inputs += ["-i", p]
            s = chunk[i][0]
            e = chunk[i + 1][0] if i + 1 < len(chunk) else chunk[-1][1] + 0.12
            n += 1
            chains.append(
                f"[{prev}][{n}:v]overlay=0:{H - strip_h - margin_bottom}"
                f":enable='between(t,{s:.3f},{e:.3f})'[v{n}]")
            prev = f"v{n}"
    chains[-1] = chains[-1].rsplit("[", 1)[0] + "[vout]"

    script = os.path.join(tmp, "filters.txt")
    open(script, "w").write(";\n".join(chains))

    has_audio = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", video],
        capture_output=True, text=True).stdout.strip() != ""
    audio = ["-map", "0:a", "-c:a", "copy"] if has_audio else []

    subprocess.run(
        [FFMPEG, "-y", "-v", "error"] + inputs +
        ["-filter_complex_script", script, "-map", "[vout]"] + audio +
        ["-c:v", "libx264", "-crf", "15", "-preset", "slow",
         "-movflags", "+faststart", output],
        check=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
