"""Christmas gift pins (1000x1500) for MoonCyclePlanner, same brand style plus holiday touches."""
import math, random, os
exec(open("/home/claude/pins/make_pins.py").read().split("# 1. Wall photo hero")[0])

NIGHT = (33, 43, 72)
GOLD = (205, 170, 104)
IVORY = (248, 242, 233)
MIST = (200, 206, 224)
BERRY = (168, 58, 72)
PINE = (54, 98, 82)
OUTX = "/home/claude/pins/out-xmas"
os.makedirs(OUTX, exist_ok=True)


SPK = {}
HB = [0]


def sparkles(c, n=60, seed=1, color=GOLD, area=(0, 0, W, H)):
    SPK.update(n=n, seed=seed, color=color)


def _draw_sparkles(c, n, seed, color):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(c)
    excl = [(70, 40, 930, HB[0] + 25), (45, HB[0] + 25, W - 45, H - 100)]
    placed = 0
    while placed < n:
        x = rnd.uniform(30, W - 30); y = rnd.uniform(30, H - 100)
        if any(a <= x <= b and c0 <= y <= e for a, c0, b, e in excl):
            continue
        placed += 1
        r = rnd.choice([2, 2, 3, 3, 4, 6, 9])
        if r <= 3:
            d.ellipse((x - r / 2, y - r / 2, x + r / 2, y + r / 2), fill=color)
        else:  # four-point star
            t = r * 0.28
            d.polygon([(x, y - r), (x + t, y - t), (x + r, y), (x + t, y + t),
                       (x, y + r), (x - t, y + t), (x - r, y), (x - t, y - t)], fill=color)


def holly(c, x, y, s=1.0):
    d = ImageDraw.Draw(c)
    for ang in (-35, 215):
        a = math.radians(ang)
        L, Wd = 70 * s, 26 * s
        cx, cy = x + math.cos(a) * L * 0.55, y + math.sin(a) * L * 0.55
        pts = []
        for i in range(21):
            t = i / 20
            px = -L / 2 + L * t
            py = Wd / 2 * math.sin(math.pi * t) * (1 + 0.18 * math.sin(t * math.pi * 6))
            pts.append((px, py))
        pts += [(p[0], -p[1]) for p in reversed(pts)]
        rot = [(cx + px * math.cos(a) - py * math.sin(a), cy + px * math.sin(a) + py * math.cos(a)) for px, py in pts]
        d.polygon(rot, fill=PINE)
    for dx, dy in ((-10, -6), (10, -6), (0, 10)):
        r = 12 * s
        d.ellipse((x + dx * s - r, y + dy * s - r, x + dx * s + r, y + dy * s + r), fill=BERRY)
        d.ellipse((x + dx * s - r * 0.35 - 3, y + dy * s - r * 0.5, x + dx * s - r * 0.35 + 2, y + dy * s - r * 0.5 + 5), fill=(220, 150, 160))


def gift_tag(c, cx, cy, lines, angle=-12, bg=IVORY, border=GOLD, ink=NAVY):
    tw, th = 360, 150
    tag = Image.new("RGBA", (tw + 80, th + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(tag)
    ox, oy = 40, 40
    notch = 45
    poly = [(ox + notch, oy), (ox + tw, oy), (ox + tw, oy + th), (ox + notch, oy + th), (ox, oy + th / 2)]
    d.polygon(poly, fill=bg, outline=border, width=4)
    d.ellipse((ox + 22, oy + th / 2 - 10, ox + 42, oy + th / 2 + 10), outline=border, width=4)
    y = oy + th / 2 - (len(lines) * 44) / 2 + 4
    for i, (txt, f) in enumerate(lines):
        while d.textlength(txt, font=f) > tw - notch - 34 and f.size > 14:
            f = f.font_variant(size=f.size - 2)
        d.text((ox + notch + (tw - notch) / 2, y + i * 46), txt, font=f, fill=ink, anchor="ma")
    tag = tag.rotate(angle, resample=Image.BICUBIC, expand=True)
    sh = tag.split()[3].point(lambda a: int(a * 0.35)).filter(ImageFilter.GaussianBlur(10))
    shadow = Image.new("RGBA", tag.size, (30, 20, 10, 0)); shadow.putalpha(sh)
    c.alpha_composite(shadow, (int(cx - tag.width / 2) + 6, int(cy - tag.height / 2) + 10))
    c.alpha_composite(tag, (int(cx - tag.width / 2), int(cy - tag.height / 2)))
    # string to the left


def headline(draw, y, text, maxw=860, size=88, fill=NAVY, **k):
    f = lora(size)
    words = text.split()
    if draw.textlength(text, font=f) <= maxw:
        lines = [text]
    else:
        best = None
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            m = max(draw.textlength(a, font=f), draw.textlength(b, font=f))
            if m <= maxw and (best is None or m < best[0]):
                best = (m, [a, b])
        lines = best[1] if best else wrap(draw, text, f, maxw)
    lh = int(size * 1.12)
    for i, ln in enumerate(lines):
        draw.text((W / 2, y + i * lh), ln, font=f, fill=fill, anchor="ma")
    return y + len(lines) * lh


def header2(c, label, title, sub, dark):
    d = ImageDraw.Draw(c)
    tracked(d, W / 2, 62, label, pop(27, "Medium"), GOLD if dark else BERRY, 7)
    y = headline(d, 120, title, size=88, fill=IVORY if dark else NAVY)
    if sub:
        d.text((W / 2, y + 14), sub, font=pop(33, "Light"), fill=MIST if dark else SLATE, anchor="ma")
        y += 60
    HB[0] = y
    return y


def gold_frame(c, inset=22):
    ImageDraw.Draw(c).rectangle((inset, inset, W - inset, H - inset), outline=GOLD, width=3)


def foot(c, dark, bg):
    d = ImageDraw.Draw(c)
    d.rectangle((0, H - 92, W, H), fill=bg)
    tracked(d, W / 2, H - 64, "MOONCYCLEPLANNER  ·  ON ETSY", pop(24, "Medium"), GOLD if dark else TEAL, 5)


def savex(c, name):
    _draw_sparkles(c, max(12, SPK["n"] // 3), SPK["seed"], SPK["color"])
    gold_frame(c)
    p = os.path.join(OUTX, name)
    c.convert("RGB").save(p, "JPEG", quality=90, optimize=True, progressive=True)
    print("saved", p, os.path.getsize(p) // 1024, "KB")


tagf_big = lambda: lora(40)
tagf_small = lambda: pop(22, "Medium")

# X1 night sky: for the moon lover
c = new(NIGHT); sparkles(c, 90, 3)
y = header2(c, "CHRISTMAS GIFT IDEA", "For the moon lover in your life", "A 2027 calendar she'll use all year", True)
top = y + 40
c.paste(cover(Image.open(f"{U}/photos/11-on-the-wall-photo.jpg").convert("RGB"), W - 100, H - 92 - top - 40, fx=0.25, fy=0.4), (50, top))
gift_tag(c, 770, top + 110, [("Gift for her", tagf_big()), ("INSTANT DOWNLOAD", tagf_small())])
holly(c, 120, top + 20, 1.1)
foot(c, True, NIGHT)
savex(c, "xmas-01-gift-for-the-moon-lover.jpg")

# X2 cream: stocking stuffer
c = new(CREAM); sparkles(c, 45, 7, color=(214, 190, 140))
y = header2(c, "STOCKING STUFFER FOR HER", "A whole year of moon magic", "Moon phases · Zodiac · Period tracker", False)
pg = Image.open(f"{SRC}/cb-03.jpg").convert("RGB")
crop = pg.crop((60, 150, pg.width - 60, 150 + (pg.width - 120))).resize((840, 840), Image.LANCZOS)
shadow_paste(c, crop, 80, y + 60)
gift_tag(c, 760, y + 860, [("Stocking stuffer", lora(34)), ("PRINTABLE PDF", tagf_small())], angle=8)
holly(c, 150, y + 70, 1.1)
foot(c, False, CREAM)
savex(c, "xmas-02-stocking-stuffer-for-her.jpg")

# X3 night: last-minute gift
c = new(NIGHT); sparkles(c, 90, 11)
y = header2(c, "LAST-MINUTE CHRISTMAS GIFT", "Print it tonight, gift it tomorrow", "Instant download · US Letter + A4", True)
top = y + 40
c.paste(cover(Image.open(f"{U}/photos/10-on-the-wall.jpg").convert("RGB"), W - 100, H - 92 - top - 40, fx=0.3, fy=0.45), (50, top))
gift_tag(c, 760, top + 120, [("No shipping", lora(38)), ("NEEDED", tagf_small())])
holly(c, 860, H - 240, 1.0)
foot(c, True, NIGHT)
savex(c, "xmas-03-last-minute-gift.jpg")

# X4 cream: astrology-loving friend
c = new(CREAM); sparkles(c, 45, 19, color=(214, 190, 140))
y = header2(c, "FOR YOUR ASTROLOGY-LOVING FRIEND", "The gift she'll use all year", "Every moon sign, eclipse & full moon of 2027", False)
page_card(c, f"{SRC}/cb-02.jpg", 110, y + 50, 780, crop_h=H - 92 - (y + 50) - 40)
gift_tag(c, 770, y + 150, [("For her", lora(42)), ("2027 MOON CALENDAR", tagf_small())], angle=-10)
holly(c, 140, H - 260, 1.1)
foot(c, False, CREAM)
savex(c, "xmas-04-astrology-gift-for-her.jpg")

# X5 blush: pink gift
c = new(BLUSH); sparkles(c, 45, 23, color=(214, 170, 160))
y = header2(c, "A PINK GIFT FOR HER", "Rose Quartz 2027 moon planner", "Soft pinks · moon phases · cycle tracker", False)
page_card(c, f"{SRC}/rq-02.jpg", 110, y + 50, 780, crop_h=H - 92 - (y + 50) - 40)
gift_tag(c, 770, y + 160, [("Made for her", lora(38)), ("INSTANT DOWNLOAD", tagf_small())], angle=-10, border=ROSE_DK)
holly(c, 140, H - 260, 1.1)
foot(c, False, BLUSH)
savex(c, "xmas-05-pink-gift-for-her-rose-quartz.jpg")

# X6 night: gift for her year ahead
c = new(NIGHT); sparkles(c, 90, 31)
y = header2(c, "A GIFT FOR HER YEAR AHEAD", "Plan 2027 with the moon", "15 printable pages · instant download", True)
pg = Image.open(f"{SRC}/cb-15.jpg").convert("RGB")
crop = pg.crop((60, 150, pg.width - 60, 150 + (pg.width - 120))).resize((800, 800), Image.LANCZOS)
year = Image.open(f"{SRC}/cb-02.jpg").convert("RGB")
ycrop = year.crop((60, 150, year.width - 60, 150 + (year.width - 120))).resize((800, 800), Image.LANCZOS)
shadow_paste(c, ycrop, 100, y + 60)
gift_tag(c, 760, y + 820, [("Merry & bright", lora(36)), ("MOON CYCLE CALENDAR", tagf_small())], angle=8)
holly(c, 150, y + 80, 1.1)
foot(c, True, NIGHT)
savex(c, "xmas-06-gift-for-her-year-ahead.jpg")
