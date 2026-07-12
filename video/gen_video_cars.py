#!/usr/bin/env python3
"""Generate video frames with fast car backgrounds + text overlays.
Uses generated car images as backgrounds with Ken Burns zoom/pan effect.
Text overlays in synthwave style: neon glow, bold serif."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, subprocess, math

WIDTH, HEIGHT = 1280, 720
FPS = 30
FRAMES_DIR = os.path.join(os.path.dirname(__file__), "frames")
CAR_DIR = os.path.join(os.path.dirname(__file__), "car_images")

narr_path = os.path.join(os.path.dirname(__file__), "narration.mp3")
dur_out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                                   "-of", "csv=p=0", narr_path]).decode().strip()
DURATION = float(dur_out) + 4.0
TOTAL_FRAMES = int(DURATION * FPS)

# Colors
BLACK = (8, 8, 12)
RED = (255, 59, 59)
GOLD = (255, 182, 39)
WHITE = (255, 255, 255)
DIM = (120, 120, 160)
NEON_PINK = (255, 20, 147)
NEON_CYAN = (0, 255, 255)
NEON_PURPLE = (180, 80, 255)

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

# Load car images
car_images = []
for i in range(1, 5):
    p = os.path.join(CAR_DIR, f"car{i}.png")
    if os.path.exists(p):
        img = Image.open(p).convert("RGB")
        car_images.append(img)

# Segment definitions (fraction-based, scales to actual narration duration)
SEGMENT_DEFS = [
    (0.00, 0.03, "WHAT THEY\nTHREW AWAY", "title"),
    (0.03, 0.08, "My name is Paul Adcock.\nI am a software engineer.\nSelf-taught. Relentless.", "body"),
    (0.08, 0.14, "I worked at Syncreon.\nSwallowed by DP World.\nOne of the largest supply chain\noperations on the planet.", "body"),
    (0.14, 0.20, "I built systems there.\nReal systems.\nThe kind that move cars through factories.\nOne mistake costs a contract.", "body"),
    (0.20, 0.24, "I showed up every day.\nI delivered.\nI cared about the work\nmore than I was supposed to.", "body"),
    (0.24, 0.28, "And then they let me go.", "hit"),
    (0.28, 0.33, "No explanation that matched the work.\nNo recognition for what I built.\nJust gone.", "body"),
    (0.33, 0.37, "You can fire the person.\nBut you cannot fire what they built.", "quote"),
    (0.37, 0.44, "Here is what I found.\nDP World and Syncreon named in\n32+ federal lawsuits.", "stat"),
    (0.44, 0.50, "Wage theft.\nNLRB violations.\nUnion suppression.\nBribery convictions.", "stat"),
    (0.50, 0.55, "Not a bad day.\nA pattern.\nA business model built on\ntreating people as disposable.", "body"),
    (0.55, 0.61, "I was not the first.\nI will not be the last.\nBut I am the one who built\na platform to document it.", "body"),
    (0.61, 0.67, "I built AutoSeq.\n16 modules. 19 OEMs. SAP.\nI rebuilt it alone for free.", "card"),
    (0.67, 0.71, "I built OwlAI Studio.\nFully local AI. Zero cloud.\nZero API costs.", "card"),
    (0.71, 0.75, "I built RemixMii.\nMusic platform. DJ mixer.\nLive on GitHub Pages.", "card"),
    (0.75, 0.79, "I built OwlEmu.\nNES emulator. Original game.\n6502 assembly. From scratch.", "card"),
    (0.79, 0.87, "I built LegalPath.\nA Bad Company Index documenting\ncompanies with sourced records\nof labor violations.\nIncluding DP World.", "card"),
    (0.87, 0.93, "12,540 lines of code.\n28 views. 33 templates.\n400 keyword patterns.\nBuilt by one person.\nThe person they let go.", "stat"),
    (0.93, 0.97, "The company that fired me\nis worth $20 billion.\nThe engineer they discarded\nbuilt all of this alone.", "stat"),
    (0.97, 1.00, "They did not break me.\nThey freed me.", "quote"),
    (1.00, 1.02, "If you have been let go.\nIf you have been discarded.\nIf you have been made to feel worthless.", "body"),
    (1.02, 1.05, "You are not alone.\nYou are not done.\nBuild anyway.", "finale"),
]

SEGMENTS = [(s * DURATION, e * DURATION, txt, typ) for s, e, txt, typ in SEGMENT_DEFS]
os.makedirs(FRAMES_DIR, exist_ok=True)

def get_segment(t_val):
    for start, end, txt, typ in SEGMENTS:
        if start <= t_val < end:
            return start, end, txt, typ
    return SEGMENTS[-1]

def ease_in_out(t_val):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(t_val, 0), 1))

# Speed lines overlay
def draw_speed_lines(draw, frame_idx):
    np.random.seed(frame_idx // 5)
    for _ in range(15):
        y = np.random.randint(0, HEIGHT)
        x = np.random.randint(0, WIDTH)
        length = np.random.randint(50, 200)
        speed = 10
        x = (x + frame_idx * speed) % WIDTH
        alpha = np.random.random() * 0.15
        color = tuple(int(c * alpha) for c in (255, 255, 255))
        draw.line([x, y, x - length, y], fill=color, width=1)

# Ken Burns effect on car images
def get_car_bg(car_idx, frame_idx, seg_start, seg_end):
    if not car_images or car_idx >= len(car_images):
        return Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    img = car_images[car_idx].copy()
    seg_duration = max(seg_end - seg_start, 0.1)
    progress = (frame_idx / FPS - seg_start) / seg_duration
    progress = max(0, min(1, progress))
    # Zoom from 1.0 to 1.15
    zoom = 1.0 + 0.15 * progress
    new_w = int(WIDTH * zoom)
    new_h = int(HEIGHT * zoom)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Pan slightly
    pan_x = int((new_w - WIDTH) * (0.3 + 0.4 * progress))
    pan_y = int((new_h - HEIGHT) * (0.2 + 0.3 * progress))
    pan_x = max(0, min(pan_x, new_w - WIDTH))
    pan_y = max(0, min(pan_y, new_h - HEIGHT))
    img = img.crop((pan_x, pan_y, pan_x + WIDTH, pan_y + HEIGHT))
    # Darken for text readability
    overlay = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    img = Image.blend(img, overlay, 0.55)
    return img

# Precompute embers
np.random.seed(42)
EMBER_SEEDS = [(np.random.random(), np.random.random(), np.random.random(),
                 np.random.random(), np.random.random()) for _ in range(25)]

def draw_glow_text(draw, x, y, text, font, fill, glow_color=None, glow_radius=3):
    if glow_color is None:
        glow_color = fill
    # Draw glow layers
    for offset in range(glow_radius, 0, -1):
        alpha = 60 // offset
        glow = tuple(min(255, c + alpha) for c in glow_color) if glow_color != BLACK else glow_color
        for dx in range(-offset, offset+1, max(1, offset)):
            for dy in range(-offset, offset+1, max(1, offset)):
                if dx*dx + dy*dy <= offset*offset:
                    draw.text((x+dx, y+dy), text, fill=glow_color, font=font)
    draw.text((x, y), text, fill=fill, font=font)

def draw_frame(frame_idx):
    t_val = frame_idx / FPS
    start, end, text, typ = get_segment(t_val)
    local_t = t_val - start
    duration = max(end - start, 0.1)
    progress = local_t / duration

    # Pick car background based on segment index
    seg_idx = 0
    for i, (s, e, _, _) in enumerate(SEGMENTS):
        if s <= t_val < e:
            seg_idx = i
            break

    # Get car background with Ken Burns
    if car_images:
        car_idx = seg_idx % len(car_images)
        img = get_car_bg(car_idx, frame_idx, start, end)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), BLACK)

    draw = ImageDraw.Draw(img)

    # Speed lines
    draw_speed_lines(draw, frame_idx)

    # Embers
    for i, (sx, sy, ss, sp, sc) in enumerate(EMBER_SEEDS):
        px = (sx * WIDTH + t_val * 20 * sp) % WIDTH
        py = HEIGHT - ((t_val * (30 + i * 5) + i * 40) % (HEIGHT + 40))
        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
            sz = 1 + int(ss * 2)
            alpha = sc * 0.4 + 0.1
            color = GOLD if i % 3 == 0 else RED
            color = tuple(int(c * alpha) for c in color)
            draw.ellipse([px-sz, py-sz, px+sz, py+sz], fill=color)

    # Vignette
    for i in range(60):
        alpha = int(100 * (i / 60) ** 2)
        draw.rectangle([i, i, WIDTH-i, HEIGHT-i], outline=(0, 0, 0))

    # --- Type-specific rendering ---
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
            # Neon glow
            for off in range(4, 0, -1):
                draw.text((x+off, y+off), line, fill=(80, 20, 20), font=font)
                draw.text((x-off, y-off), line, fill=(80, 20, 20), font=font)
            color = tuple(int(RED[i] + (GOLD[i] - RED[i]) * fade) for i in range(3))
            draw.text((x, y), line, fill=color, font=font)
            y += 85
        sub_font = load_font(20)
        sub = "Paul Adcock / OwlLogics"
        bbox = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox[2] - bbox[0]
        draw.text(((WIDTH - sw) // 2, y + 30), sub, fill=DIM, font=sub_font)

    elif typ == "hit":
        # Hard cut — black overlay, white text
        fade = ease_in_out(min(progress * 5, 1))
        overlay_img = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
        img = Image.blend(img, overlay_img, fade)
        draw = ImageDraw.Draw(img)
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
            color = tuple(int(WHITE[i] * fade + BLACK[i] * (1 - fade)) for i in range(3))
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
                color = tuple(int(RED[j] * fade + BLACK[j] * (1 - fade)) for j in range(3))
                draw.text((x, y), line, fill=color, font=font_big)
                y += 60
            else:
                bbox = draw.textbbox((0, 0), line, font=font_body)
                w = bbox[2] - bbox[0]
                x = (WIDTH - w) // 2
                color = tuple(int(WHITE[j] * fade + BLACK[j] * (1 - fade)) for j in range(3))
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
                    color = tuple(int(RED[j] * line_fade + BLACK[j] * (1 - line_fade)) for j in range(3))
                else:
                    color = tuple(int(WHITE[j] * line_fade + BLACK[j] * (1 - line_fade)) for j in range(3))
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
            color = tuple(int(WHITE[j] * vis + BLACK[j] * (1 - vis)) for j in range(3))
            draw.text((x, y), line, fill=color, font=font)
            y += 45

    # Watermark
    wm_font = load_font(14)
    draw.text((20, HEIGHT - 25), "OWLLOGICS", fill=(40, 40, 56), font=wm_font)
    draw.text((WIDTH - 120, HEIGHT - 25), "turtle-pb.github.io/fu", fill=(40, 40, 56), font=wm_font)

    return img

print(f"Generating {TOTAL_FRAMES} frames at {FPS}fps (duration: {DURATION:.1f}s)...")
for i in range(TOTAL_FRAMES):
    img = draw_frame(i)
    img.save(os.path.join(FRAMES_DIR, f"frame_{i:05d}.png"))
    if i % 300 == 0:
        print(f"  Frame {i}/{TOTAL_FRAMES} ({100*i/TOTAL_FRAMES:.0f}%)")

print(f"Done. {TOTAL_FRAMES} frames written to {FRAMES_DIR}")
