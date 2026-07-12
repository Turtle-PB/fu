#!/usr/bin/env python3
"""Build the final Echonation-style FU video: narration + synthwave track + car visuals."""
import subprocess, os, sys

DIR = os.path.dirname(__file__)
FRAMES = os.path.join(DIR, "frames")
NARRATION = os.path.join(DIR, "narration.mp3")
MUSIC = os.path.join(DIR, "echonation.wav")
OUTPUT = os.path.join(DIR, "fu_video_echonation.mp4")

cmd = [
    "ffmpeg", "-y",
    "-framerate", "30",
    "-i", os.path.join(FRAMES, "frame_%05d.png"),
    "-i", NARRATION,
    "-i", MUSIC,
    "-filter_complex",
    "[1:a]volume=1.5,aecho=0.8:0.6:300:0.1,aresample=44100[vo];"
    "[2:a]volume=0.20[bg];"
    "[vo][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
    "-map", "0:v",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "20",
    "-preset", "medium",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    "-movflags", "+faststart",
    OUTPUT
]

print("Compositing Echonation video...")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("FFMPEG ERROR:")
    print(result.stderr[-2000:])
    sys.exit(1)

size = os.path.getsize(OUTPUT)
dur = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                               "-of", "csv=p=0", OUTPUT]).decode().strip()
print(f"\nVideo complete: {OUTPUT}")
print(f"  Size: {size/1024/1024:.1f} MB")
print(f"  Duration: {dur}s")
