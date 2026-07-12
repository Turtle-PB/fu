#!/usr/bin/env python3
"""Generate ambient soundtrack — dark, cinematic, building tension.
Synthesized entirely with numpy. No external audio files."""
import numpy as np, wave, struct, sys, os

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "ambient.wav")

# Get narration duration
import subprocess
dur_out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                                   "-of", "csv=p=0",
                                   os.path.join(os.path.dirname(__file__), "narration.mp3")]).decode().strip()
DURATION = float(dur_out) + 3.0  # pad 3s at end
TOTAL = int(SR * DURATION)

t = np.arange(TOTAL) / SR

# --- Deep drone bass (root: D1 = 36.71 Hz) ---
bass = np.sin(2 * np.pi * 36.71 * t) * 0.3
bass += np.sin(2 * np.pi * 73.42 * t) * 0.15  # octave up

# --- Slow LFO on bass for breathing ---
lfo = np.sin(2 * np.pi * 0.15 * t)
bass = bass * (0.6 + 0.4 * lfo)

# --- Dark minor pad (D minor: D, F, A) ---
pad_freqs = [146.83, 174.61, 220.0]  # D3, F3, A3
pad = np.zeros_like(t)
for i, f in enumerate(pad_freqs):
    detune = f * (1 + 0.003 * np.sin(2 * np.pi * 0.1 * t + i))
    wave_s = np.sin(2 * np.pi * detune * t)
    wave_s += 0.3 * np.sin(2 * np.pi * detune * 2 * t)  # 2nd harmonic
    pad += wave_s * 0.08

# Slow attack envelope on pad
pad_env = np.minimum(t / 4.0, 1.0) * np.minimum((DURATION - t) / 4.0, 1.0)
pad = pad * np.clip(pad_env, 0, 1)

# --- Tension pulse (low heartbeat) ---
pulse_rate = 0.5  # 30 bpm
pulse_t = (t * pulse_rate) % 1.0
pulse_env = np.exp(-pulse_t * 15)
pulse = np.sin(2 * np.pi * 55 * t) * pulse_env * 0.12

# --- High shimmer (very subtle, like distant strings) ---
shimmer = np.sin(2 * np.pi * 587.33 * t) * 0.02  # D5
shimmer += np.sin(2 * np.pi * 880.0 * t) * 0.015  # A5
shim_env = np.minimum(t / 8.0, 1.0) * np.minimum((DURATION - t) / 6.0, 1.0)
shimmer = shimmer * np.clip(shim_env, 0, 1)

# --- Cinematic sub boom at key moments (0s, 30%, 60%, 90%) ---
boom_times = [0, DURATION * 0.3, DURATION * 0.6, DURATION * 0.9]
booms = np.zeros_like(t)
for bt in boom_times:
    idx = int(bt * SR)
    if idx < TOTAL:
        boom_len = int(2.0 * SR)
        end = min(idx + boom_len, TOTAL)
        bt_arr = np.arange(end - idx) / SR
        boom_env = np.exp(-bt_arr * 1.5)
        booms[idx:end] += np.sin(2 * np.pi * 27.5 * bt_arr) * boom_env * 0.25

# --- Mix ---
audio = bass + pad + pulse + shimmer + booms

# Soft clip
audio = np.tanh(audio * 1.3) * 0.7

# Normalize to 0.75 peak
peak = np.max(np.abs(audio))
if peak > 0:
    audio = audio * (0.75 / peak)

# Stereo with slight Haas
left = audio
right = np.roll(audio, int(0.015 * SR))
right[:int(0.015*SR)] = 0

stereo = np.column_stack([left, right])

# Write WAV (fast numpy method)
stereo_int = np.clip(stereo, -1, 1) * 32767
stereo_int = stereo_int.astype(np.int16)
with wave.open(OUT, 'w') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(stereo_int.tobytes())

print(f"Saved ambient track: {OUT}")
print(f"Duration: {DURATION:.1f}s, Samples: {TOTAL}")
