#!/usr/bin/env python3
"""Generate animated cinematic frames for the FU video.
Dark, minimal, text-driven. No external assets."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os, subprocess, math

WIDTH, HEIGHT = 1280, 720
FPS = 30
FRAMES_DIR = os.path.join(os.path.dirname(__file__), "frames")

# Get narration duration
narr_path = os.path.join(os.path.dirname(__file__), "narration.mp3")
dur_out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", narr_path]).decode().strip()
DURATION = float(dur_out) + 3.0
TOTAL_FRAMES = int(DURATION * FPS)

# Colors
BG = (8, 8, 12)
RED = (255, 59, 59)
GOLD = (255, 182, 39)
WHITE = (255, 255, 255)
DIM = (120, 120, 160)

# Font paths (Linux/WSL)
FONT_PATHS = [
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]
FONT_SERIF_PATHS = [
    "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSerif-Bold.ttf",
]

def load_font(size, serif=False):
    paths = FONT_SERIF_PATHS if serif else FONT_PATHS
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

# Build segments dynamically based on narration duration
# Each entry: (fraction_start, fraction_end, text, type)
SEGMENT_DEFS = [
    (0.00, 0.03, "WHAT THEY\nTHREW AWAY", "title"),
    (0.03, 0.08, "My name is Paul Adcock.\nI am a software engineer.\nSelf-taught. Relentless.", "body"),
    (0.08, 0.14, "I worked at Syncreon.\nA logistics company swallowed by DP World.\nOne of the largest supply chain\noperations on the planet.", "body"),
    (0.14, 0.20, "I built systems there.\nReal systems.\nThe kind that move cars through factories.\nThe kind where one mistake costs a contract.", "body"),
    (0.20, 0.24, "I showed up every day.\nI delivered.\nI cared about the work\nmore than I was supposed to.", "body"),
    (0.24, 0.28, "And then they let me go.", "hit"),
    (0.28, 0.33, "No explanation that matched the work.\nNo recognition for what I built.\nJust gone.", "body"),
    (0.33, 0.37, "You can fire the person.\nBut you cannot fire what they built.", "quote"),
    (0.37, 0.44, "Here is what I found after.\nDP World and Syncreon have been named\nin 32+ federal lawsuits.", "stat"),
    (0.44, 0.50, "Wage theft.\nNLRB violations.\nUnion suppression.\nBribery convictions.", "stat"),
    (0.50, 0.55, "This is not a bad day.\nThis is a pattern.\nThis is a business model\nbuilt on treating people as disposable.", "body"),
    (0.55, 0.61, "I was not the first engineer\nthey threw away.\nI will not be the last.\nBut I am the one who built a platform\nto document it.", "body"),
    (0.61, 0.67, "After they showed me the door\nI built AutoSeq.\n16 modules. 19 OEMs. SAP integration.\nThe kind of system they paid me to build.\nI rebuilt it alone for free.", "card"),
    (0.67, 0.71, "I built OwlAI Studio.\nFully local AI. Zero cloud.\nZero API costs.", "card"),
    (0.71, 0.75, "I built RemixMii.\nA music platform with a DJ mixer.\nLive on GitHub Pages.", "card"),
    (0.75, 0.79, "I built OwlEmu.\nAn NES emulator and an original game\nin 6502 assembly. From scratch.", "card"),
    (0.79, 0.87, "I built LegalPath.\nA legal case builder with a Bad Company Index\ndocumenting companies with publicly sourced\nrecords of labor violations.\nIncluding DP World. Including Syncreon.", "card"),
    (0.87, 0.93, "12,540 lines of code.\n28 views. 33 templates.\nA document analysis engine\nwith 400 keyword patterns.\nBuilt by one person.\nThe person they let go.", "stat"),
    (0.93, 0.97, "The company that fired me\nis worth over $20 billion.\nThe engineer they discarded\nbuilt all of this alone. For free.", "stat"),
    (0.97, 1.00, "They did not break me.\nThey freed me.", "quote"),
    (1.00, 1.02, "If you have been let go.\nIf you have been discarded.\nIf you have been made to feel worthless.", "body"),
    (1.02, 1.05, "You are not alone.\nYou are not done.\nBuild anyway.", "finale"),
]

SEGMENTS = [(s * DURATION, e * DURATION, t, typ) for s, e, t, typ in SEGMENT_DEFS]

os.makedirs(FRAMES_DIR, exist_ok=True)

def get_segment(t):
    for start, end, text, typ in SEGMENTS:
        if start <= t < end:
            return start, end, text, typ
    return SEGMENTS[-1]

def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(t, 0), 1))

# Precompute ember seeds
np.random.seed(42)
EMBER_SEEDS = [(np.random.random(), np.random.random(), np.random.random(),
                 np.random.random(), np.random.random()) for _ in range(30)]

def draw_frame(frame_idx):
    t = frame_idx / FPS
    img = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    start, end, text, typ = get_segment(t)
    local_t = t - start
    duration = max(end - start, 0.1)
    progress = local_t / duration

    # Particle embers
    for i, (sx, sy, ss, sp, sc) in enumerate(EMBER_SEEDS):
        px = (sx * WIDTH + t * 20 * sp) % WIDTH
        py = HEIGHT - ((t * (30 + i * 5) + i * 40) % (HEIGHT + 40))
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            sz = 1 + int(ss * 2)
            alpha = sc * 0.4 + 0.1
            color = GOLD if i % 3 == 0 else RED
            color = tuple(int(c * alpha) for c in color)
            draw.ellipse([px-sz, py-sz, px+sz, py+sz], fill=color)

    # Vignette
    for i in range(60):
        alpha = int(80 * (i / 60) ** 2)
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0))

    if typ == "title":
        fade = ease_in_out(min(progress * 3, 1))
        font = load_font(72, serif=True)
        lines = text.split('\n')
        total_h = len(lines) * 85
        y = (HEIGHT - total_h) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            x = (WIDTH - w) // 2
            color = tuple(int(RED[i] + (GOLD[i] - RED[i]) * fade) for i in range(3))
            draw.text((x, y), line, fill=color, font=font)
            y += 85
        sub_font = load_font(20)
        sub = "Paul Adcock / OwlLogics"
        bbox = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox[2] - bbox[0]
        draw.text(((WIDTH - sw) // 2, y + 30), sub, fill=DIM, font=sub_font)

    elif typ == "hit":
        font = load_font(56, serif=True)
        lines = text.split('\n')
        y = (HEIGHT - len(lines) * 65) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            x = (WIDTH - w) // 2
            draw.text((x, y), line, fill=WHITE, font=font)
            y += 65

    elif typ == "quote":
        fade = ease_in_out(min(progress * 2, 1))
        font = load_font(40, serif=True)
        lines = text.split('\n')
        total_h = len(lines) * 55
        y = (HEIGHT - total_h) // 2
        draw.line([WIDTH//2 - 200, y - 20, WIDTH//2 - 200, y + total_h + 10], fill=RED, width=3)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            x = (WIDTH - w) // 2 + 20
            color = tuple(int(WHITE[i] * fade + BG[i] * (1 - fade)) for i in range(3))
            draw.text((x, y), line, fill=color, font=font)
            y += 55

    elif typ == "stat":
        fade = ease_in_out(min(progress * 2.5, 1))
        font_big = load_font(48, serif=True)
        font_body = load_font(26)
        lines = text.split('\n')
        total_h = len(lines) * 50
        y = (HEIGHT - total_h) // 2
        for i, line in enumerate(lines):
            if i == 0:
                bbox = draw.textbbox((0, 0), line, font=font_big)
                w = bbox[2] - bbox[0]
                x = (WIDTH - w) // 2
                color = tuple(int(RED[j] * fade + BG[j] * (1 - fade)) for j in range(3))
                draw.text((x, y), line, fill=color, font=font_big)
                y += 60
            else:
                bbox = draw.textbbox((0, 0), line, font=font_body)
                w = bbox[2] - bbox[0]
                x = (WIDTH - w) // 2
                color = tuple(int(WHITE[j] * fade + BG[j] * (1 - fade)) for j in range(3))
                draw.text((x, y), line, fill=color, font=font_body)
                y += 38

    elif typ == "card":
        fade = ease_in_out(min(progress * 2.5, 1))
        card_w, card_h = 700, 400
        cx = (WIDTH - card_w) // 2
        cy = (HEIGHT - card_h) // 2
        draw.rectangle([cx, cy, cx + card_w, cy + card_h], fill=(24, 24, 34))
        border_w = int(card_w * fade)
        draw.rectangle([cx, cy, cx + border_w, cy + 3], fill=RED)
        draw.rectangle([cx, cy + card_h - 1, cx + card_w, cy + card_h], fill=(40, 40, 56))
        font_title = load_font(34, serif=True)
        font_body = load_font(22)
        lines = text.split('\n')
        y = cy + 30
        for i, line in enumerate(lines):
            if i == 0:
                bbox = draw.textbbox((0, 0), line, font=font_title)
                w = bbox[2] - bbox[0]
                x = cx + (card_w - w) // 2
                color = tuple(int(WHITE[j] * fade + (24,24,34)[j] * (1-fade)) for j in range(3))
                draw.text((x, y), line, fill=color, font=font_title)
                y += 50
            else:
                bbox = draw.textbbox((0, 0), line, font=font_body)
                w = bbox[2] - bbox[0]
                x = cx + (card_w - w) // 2
                color = tuple(int(DIM[j] * fade + (24,24,34)[j] * (1-fade)) for j in range(3))
                draw.text((x, y), line, fill=color, font=font_body)
                y += 32

    elif typ == "finale":
        font_big = load_font(52, serif=True)
        lines = text.split('\n')
        line_dur = duration / len(lines)
        y = (HEIGHT - len(lines) * 70) // 2
        for i, line in enumerate(lines):
            line_start = i * line_dur
            line_fade = ease_in_out(min((local_t - line_start) / 1.0, 1))
            if line_fade > 0:
                bbox = draw.textbbox((0, 0), line, font=font_big)
                w = bbox[2] - bbox[0]
                x = (WIDTH - w) // 2
                if "Build anyway" in line:
                    color = tuple(int(RED[j] * line_fade + BG[j] * (1 - line_fade)) for j in range(3))
                else:
                    color = tuple(int(WHITE[j] * line_fade + BG[j] * (1 - line_fade)) for j in range(3))
                draw.text((x, y), line, fill=color, font=font_big)
            y += 70

    else:  # body
        fade = ease_in_out(min(progress * 2.5, 1))
        out_fade = ease_in_out(max(1.0 - (progress - 0.8) * 5, 0))
        vis = fade * out_fade
        font = load_font(30)
        lines = text.split('\n')
        total_h = len(lines) * 45
        y = (HEIGHT - total_h) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            x = (WIDTH - w) // 2
            color = tuple(int(WHITE[j] * vis + BG[j] * (1 - vis)) for j in range(3))
            draw.text((x, y), line, fill=color, font=font)
            y += 45

    # Watermark
    wm_font = load_font(14)
    draw.text((20, HEIGHT - 25), "OWLLOGICS", fill=(40, 40, 56), font=wm_font)
    draw.text((WIDTH - 120, HEIGHT - 25), "turtle-pb.github.io/fu", fill=(40, 40, 56), font=wm_font)

    return img

# Generate all frames
print(f"Generating {TOTAL_FRAMES} frames at {FPS}fps (duration: {DURATION:.1f}s)...")
for i in range(TOTAL_FRAMES):
    img = draw_frame(i)
    img.save(os.path.join(FRAMES_DIR, f"frame_{i:05d}.png"))
    if i % 300 == 0:
        print(f"  Frame {i}/{TOTAL_FRAMES} ({100*i/TOTAL_FRAMES:.0f}%)")

print(f"Done. {TOTAL_FRAMES} frames written to {FRAMES_DIR}")
