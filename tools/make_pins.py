"""Render 1000x1500 Pinterest pins for MoonCyclePlanner from the shop's own artwork."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

U = "/mnt/user-data/uploads/MoonCyclePlanner-Etsy"
SRC = "/home/claude/pins/src"
OUT = "/home/claude/pins/out"
os.makedirs(OUT, exist_ok=True)
GF = "/usr/share/fonts/truetype/google-fonts/"

W, H = 1000, 1500
CREAM = (239, 233, 227)
BLUSH = (244, 231, 228)
TEAL = (62, 127, 122)
NAVY = (43, 56, 88)
SLATE = (107, 115, 144)
ROSE = (201, 131, 138)
ROSE_DK = (178, 104, 114)


def lora(size, bold=False):
    f = ImageFont.truetype(GF + "Lora-Variable.ttf", size)
    try:
        f.set_variation_by_name("Bold" if bold else "Medium")
    except Exception:
        pass
    return f


def pop(size, weight="Regular"):
    return ImageFont.truetype(GF + f"Poppins-{weight}.ttf", size)


def tracked(draw, cx, y, text, font, fill, track):
    widths = [draw.textlength(c, font=font) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x = cx - total / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=font, fill=fill)
        x += w + track


def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def headline(draw, y, text, maxw=880, size=92, fill=NAVY, min_size=60, max_lines=3):
    while True:
        f = lora(size)
        lines = wrap(draw, text, f, maxw)
        if len(lines) <= max_lines or size <= min_size:
            break
        size -= 4
    lh = int(size * 1.12)
    for i, ln in enumerate(lines):
        draw.text((W / 2, y + i * lh), ln, font=f, fill=fill, anchor="ma")
    return y + len(lines) * lh


def cover(img, box_w, box_h, fx=0.5, fy=0.5):
    iw, ih = img.size
    s = max(box_w / iw, box_h / ih)
    img = img.resize((int(iw * s + 0.5), int(ih * s + 0.5)), Image.LANCZOS)
    iw, ih = img.size
    x = int((iw - box_w) * fx)
    y = int((ih - box_h) * fy)
    return img.crop((x, y, x + box_w, y + box_h))


def shadow_paste(canvas, img, x, y, radius=18, offset=10, alpha=70):
    sh = Image.new("RGBA", (img.width + radius * 4, img.height + radius * 4), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle(
        (radius * 2, radius * 2, radius * 2 + img.width, radius * 2 + img.height), fill=(60, 50, 40, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    canvas.alpha_composite(sh, (x - radius * 2, y - radius * 2 + offset))
    canvas.alpha_composite(img.convert("RGBA"), (x, y))


def badge(canvas, cx, cy, r, top, mid, bot, color=ROSE):
    d = ImageDraw.Draw(canvas)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    tracked(d, cx, cy - r * 0.52, top, pop(int(r * 0.2), "Medium"), "white", 3)
    d.text((cx, cy - r * 0.27), mid, font=lora(int(r * 0.48)), fill="white", anchor="ma")
    tracked(d, cx, cy + r * 0.3, bot, pop(int(r * 0.2), "Medium"), "white", 3)


def footer(canvas, bg, text="MoonCyclePlanner  ·  on Etsy", color=TEAL):
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, H - 92, W, H), fill=bg)
    tracked(d, W / 2, H - 64, text.upper(), pop(24, "Medium"), color, 5)


def header(canvas, label, title, sub, label_color=TEAL, top=62, title_size=92):
    d = ImageDraw.Draw(canvas)
    tracked(d, W / 2, top, label, pop(27, "Medium"), label_color, 7)
    y = headline(d, top + 58, title, size=title_size)
    if sub:
        d.text((W / 2, y + 14), sub, font=pop(33, "Light"), fill=SLATE, anchor="ma")
        y += 14 + 46
    return y


def page_card(canvas, page_path, x, y, w, crop_h=None):
    pg = Image.open(page_path).convert("RGB")
    s = w / pg.width
    pg = pg.resize((w, int(pg.height * s)), Image.LANCZOS)
    if crop_h:
        pg = pg.crop((0, 0, w, crop_h))
    shadow_paste(canvas, pg, x, y)


def save(canvas, name):
    p = os.path.join(OUT, name)
    canvas.convert("RGB").save(p, "JPEG", quality=90, optimize=True, progressive=True)
    print("saved", p, os.path.getsize(p) // 1024, "KB")


def new(bg=CREAM):
    return Image.new("RGBA", (W, H), bg + (255,))


# 1. Wall photo hero
c = new()
y = header(c, "2027 MOON CYCLE CALENDAR", "Plan your year with the moon", "Moon phases · Zodiac · Period tracker")
ph = Image.open(f"{U}/photos/11-on-the-wall-photo.jpg").convert("RGB")
top = y + 40
c.paste(cover(ph, W, H - 92 - top, fx=0.25, fy=0.35), (0, top))
badge(c, 850, top + 120, 105, "PRINTABLE", "PDF", "15 PAGES")
footer(c, CREAM)
save(c, "pin-01-plan-your-year-with-the-moon.jpg")

# 2. Everything on one wheel (January page, zoomed wheel)
c = new()
y = header(c, "MOON PHASE CALENDAR + PERIOD TRACKER", "Everything on one wheel", "Plans · moon phase · moon sign · cycle")
pg = Image.open(f"{SRC}/cb-03.jpg").convert("RGB")
crop = pg.crop((60, 150, pg.width - 60, 150 + (pg.width - 120)))  # square around the wheel
cw = 880
crop = crop.resize((cw, cw), Image.LANCZOS)
shadow_paste(c, crop, (W - cw) // 2, y + 50)
footer(c, CREAM)
save(c, "pin-02-everything-on-one-wheel.jpg")

# 3. Year at a glance
c = new()
y = header(c, "ALL OF 2027 AT A GLANCE", "Every full moon, eclipse & Mercury retrograde", None, title_size=84)
page_card(c, f"{SRC}/cb-02.jpg", 110, y + 40, 780, crop_h=H - 92 - (y + 40) - 30)
badge(c, 860, H - 300, 95, "TIMES IN", "EST", "W. ZODIAC")
footer(c, CREAM)
save(c, "pin-03-full-moons-eclipses-mercury-retrograde-2027.jpg")

# 4. Cycle wheel
c = new()
y = header(c, "UNDATED CYCLE WHEEL", "Track your cycle with the moon", "Print a fresh wheel every cycle")
pg = Image.open(f"{SRC}/cb-15.jpg").convert("RGB")
crop = pg.crop((60, 150, pg.width - 60, 150 + (pg.width - 120)))
cw = 880
shadow_paste(c, crop.resize((cw, cw), Image.LANCZOS), (W - cw) // 2, y + 50)
footer(c, CREAM)
save(c, "pin-04-track-your-cycle-with-the-moon.jpg")

# 5. Rose Quartz
c = new(BLUSH)
y = header(c, "ROSE QUARTZ EDITION", "The pretty pink 2027 moon planner", "Moon phases · Zodiac · Period tracker", label_color=ROSE_DK)
page_card(c, f"{SRC}/rq-03.jpg", 100, y + 40, 800, crop_h=H - 92 - (y + 40) - 30)
badge(c, 860, y + 120, 100, "PRINTABLE", "PDF", "LETTER + A4", color=ROSE_DK)
footer(c, BLUSH, color=ROSE_DK)
save(c, "pin-05-pink-2027-moon-planner-rose-quartz.jpg")

# 6. 15 pages
c = new()
y = header(c, "INSTANT DOWNLOAD", "15 printable pages for your whole year", "Year wheel · 12 months · cycle wheel · guide", title_size=84)
ph = Image.open(f"{U}/photos/06-twelve-months.jpg").convert("RGB")
top = y + 36
c.paste(cover(ph, W, H - 92 - top, fx=0.5, fy=0.75), (0, top))
footer(c, CREAM)
save(c, "pin-06-15-printable-pages.jpg")

# 7. Gift
c = new()
y = header(c, "GIFT IDEA FOR HER", "For the woman who plans with the moon", "Instant download · print at home", title_size=84)
ph = Image.open(f"{U}/photos/12-february-bathroom-photo.jpg").convert("RGB")
top = y + 36
c.paste(cover(ph, W, H - 92 - top, fx=0.5, fy=0.4), (0, top))
footer(c, CREAM)
save(c, "pin-07-gift-for-her-moon-calendar.jpg")

# 8. How-to guide
c = new()
y = header(c, "BEGINNER FRIENDLY", "How to plan with the moon", "Easy how-to guide included")
page_card(c, f"{SRC}/cb-01.jpg", 110, y + 40, 780, crop_h=H - 92 - (y + 40) - 30)
footer(c, CREAM)
save(c, "pin-08-how-to-plan-with-the-moon.jpg")
