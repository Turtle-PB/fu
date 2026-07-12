#!/usr/bin/env python3
"""Build the final FU video: composite narration + ambient music + animated frames."""
import subprocess, os, sys

DIR = os.path.dirname(__file__)
FRAMES = os.path.join(DIR, "frames")
NARRATION = os.path.join(DIR, "narration.mp3")
AMBIENT = os.path.join(DIR, "ambient.wav")
OUTPUT = os.path.join(DIR, "fu_video.mp4")

# Duck ambient under narration: music at 25%, narration at 150%
# Add subtle reverb to narration for cinematic feel
cmd = [
    "ffmpeg", "-y",
    "-framerate", "30",
    "-i", os.path.join(FRAMES, "frame_%05d.png"),
    "-i", NARRATION,
    "-i", AMBIENT,
    "-filter_complex",
    "[1:a]volume=1.5,aecho=0.8:0.7:400:0.15,aresample=44100[vo];"
    "[2:a]volume=0.25[bg];"
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

print("Compositing video...")
print(f"  Frames: {FRAMES}")
print(f"  Narration: {NARRATION}")
print(f"  Ambient: {AMBIENT}")
print(f"  Output: {OUTPUT}")

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("FFMPEG ERROR:")
    print(result.stderr[-2000:])
    sys.exit(1)

# Verify output
size = os.path.getsize(OUTPUT)
dur = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                               "-of", "csv=p=0", OUTPUT]).decode().strip()
print(f"\nVideo complete: {OUTPUT}")
print(f"  Size: {size/1024/1024:.1f} MB")
print(f"  Duration: {dur}s")
