#!/usr/bin/env python3
"""Generate Echonation-style synthwave/electronic track.
Driving beat, synth bass, arpeggios, atmospheric pads. All numpy-synthesized."""
import numpy as np, wave, os, subprocess

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "echonation.wav")

narr_path = os.path.join(os.path.dirname(__file__), "narration.mp3")
dur_out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", narr_path]).decode().strip()
DURATION = float(dur_out) + 4.0
TOTAL = int(SR * DURATION)
t = np.arange(TOTAL) / SR

BPM = 128
BEAT = 60.0 / BPM  # 0.469s per beat
SIXTEENTH = BEAT / 4

# --- Synth bass (driving, repetitive, A minor) ---
bass_notes = [55.0, 55.0, 82.41, 55.0]  # A1, A1, E2, A1 — driving pattern
bass = np.zeros_like(t)
for i in range(TOTAL):
    beat_idx = int((i / SR) / SIXTEENTH) % len(bass_notes)
    note_t = ((i / SR) % SIXTEENTH) / SIXTEENTH
    env = np.exp(-note_t * 8) * (1 - np.exp(-note_t * 200))
    bass[i] = np.sin(2 * np.pi * bass_notes[beat_idx] * (i / SR)) * env * 0.35
    bass[i] += 0.3 * np.sin(2 * np.pi * bass_notes[beat_idx] * 2 * (i / SR)) * env * 0.15

# --- Kick drum (four-on-the-floor) ---
kick = np.zeros_like(t)
for i in range(TOTAL):
    beat_t = (i / SR) % BEAT
    if beat_t < 0.05:
        freq = 80 * np.exp(-beat_t * 30) + 40
        kick[i] = np.sin(2 * np.pi * freq * beat_t) * np.exp(-beat_t * 15) * 0.5

# --- Snare on beats 2 and 4 ---
snare = np.zeros_like(t)
for i in range(TOTAL):
    beat_t = (i / SR) % (BEAT * 2)
    if beat_t < 0.03 or (beat_t > BEAT and beat_t < BEAT + 0.03):
        s_t = beat_t if beat_t < 0.03 else beat_t - BEAT
        noise = np.random.random() - 0.5
        snare[i] = (noise * np.exp(-s_t * 40) + np.sin(2*np.pi*200*s_t)*np.exp(-s_t*30)) * 0.2

# --- Hi-hats (16th notes, off-beat accent) ---
hats = np.zeros_like(t)
for i in range(TOTAL):
    sixteenth_t = (i / SR) % SIXTEENTH
    if sixteenth_t < 0.005:
        hat_idx = int((i / SR) / SIXTEENTH) % 4
        vol = 0.04 if hat_idx % 2 == 0 else 0.08
        noise = np.random.random() - 0.5
        hats[i] = noise * np.exp(-sixteenth_t * 80) * vol

# --- Arpeggio (A minor: A, C, E, A, E, C, A, C — octave up) ---
arp_notes = [220.0, 261.63, 329.63, 440.0, 329.63, 261.63, 220.0, 261.63]
arp = np.zeros_like(t)
for i in range(TOTAL):
    arp_idx = int((i / SR) / SIXTEENTH) % len(arp_notes)
    note_t = ((i / SR) % SIXTEENTH) / SIXTEENTH
    env = np.exp(-note_t * 6) * (1 - np.exp(-note_t * 300))
    freq = arp_notes[arp_idx]
    arp[i] = (np.sin(2*np.pi*freq*(i/SR)) + 0.3*np.sin(2*np.pi*freq*2*(i/SR))) * env * 0.08

# --- Pad (A minor triad, slow attack) ---
pad_freqs = [110.0, 130.81, 164.81]  # A2, C3, E3
pad = np.zeros_like(t)
for f in pad_freqs:
    detune = f * (1 + 0.002 * np.sin(2 * np.pi * 0.1 * t))
    pad += np.sin(2 * np.pi * detune * t) * 0.03
pad_env = np.minimum(t / 6.0, 1.0) * np.minimum((DURATION - t) / 6.0, 1.0)
pad = pad * np.clip(pad_env, 0, 1)

# --- Sub drop at 0 and at 60% ---
drops = np.zeros_like(t)
for drop_t in [0, DURATION * 0.6]:
    idx = int(drop_t * SR)
    if idx < TOTAL:
        drop_len = int(1.5 * SR)
        end = min(idx + drop_len, TOTAL)
        dt_arr = np.arange(end - idx) / SR
        freq = 80 * np.exp(-dt_arr * 2) + 25
        drops[idx:end] = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-dt_arr * 1.5) * 0.3

# --- Mix ---
audio = bass + kick + snare + hats + arp + pad + drops

# Sidechain compression (duck on kick)
sidechain = np.zeros_like(t)
for i in range(TOTAL):
    beat_t = (i / SR) % BEAT
    if beat_t < 0.15:
        sidechain[i] = 1.0 - 0.3 * np.exp(-beat_t * 20)
    else:
        sidechain[i] = 1.0
audio = audio * sidechain

# Soft clip + normalize
audio = np.tanh(audio * 1.2) * 0.75
peak = np.max(np.abs(audio))
if peak > 0:
    audio = audio * (0.8 / peak)

# Stereo
left = audio
right = np.roll(audio, int(0.01 * SR))
right[:int(0.01*SR)] = 0
stereo = np.column_stack([left, right])

stereo_int = np.clip(stereo, -1, 1) * 32767
stereo_int = stereo_int.astype(np.int16)

with wave.open(OUT, 'w') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(stereo_int.tobytes())

print(f"Saved Echonation track: {OUT}")
print(f"Duration: {DURATION:.1f}s, BPM: {BPM}")
