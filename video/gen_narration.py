#!/usr/bin/env python3
"""Generate narration TTS audio using edge-tts."""
import asyncio, sys, os

OUT = os.path.join(os.path.dirname(__file__), "narration.mp3")
TEXT_FILE = os.path.join(os.path.dirname(__file__), "narration.txt")

async def main():
    text = open(TEXT_FILE, "r").read().strip()
    # Deep, serious male voice
    import edge_tts
    comm = edge_tts.Communicate(text, voice="en-US-GuyNeural", rate="-15%", pitch="-10Hz")
    await comm.save(OUT)
    # Get duration
    import subprocess
    dur = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", OUT]).decode().strip()
    print(f"Saved narration: {OUT}")
    print(f"Duration: {dur}s")

asyncio.run(main())
