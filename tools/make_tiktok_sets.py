"""Render 1080x1920 TikTok carousel slides for MoonCyclePlanner.

Product images are cropped from graphics already in this repo (which were built
from the real Etsy listing photos), so no outside downloads are needed.
Run from anywhere:  python3 tools/make_tiktok_sets.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "media/etsy/tiktok")
P = os.path.join(ROOT, "media/etsy/pins")
OUT = T
GF = "/usr/share/fonts/truetype/google-fonts/"
SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

W, H = 1080, 1920
CREAM = (234, 231, 225)
BLUSH = (244, 231, 228)
NAVY = (46, 51, 80)
SAGE = (79, 127, 114)
ROSE = (184, 124, 128)
SLATE = (104, 108, 134)
MOONDARK = (205, 208, 224)
WHITE = (255, 255, 255)


def lora(size, w="SemiBold"):
    f = ImageFont.truetype(GF + "Lora-Variable.ttf", size)
    f.set_variation_by_name(w)
    return f


def pop(size, weight="Regular"):
    return ImageFont.truetype(GF + f"Poppins-{weight}.ttf", size)


def wrap(d, text, font, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if d.textlength(t, font=font) <= maxw:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def tracked(d, cx, y, text, font, fill, track=6):
    ws = [d.textlength(c, font=font) for c in text]
    x = cx - (sum(ws) + track * (len(text) - 1)) / 2
    for c, w in zip(text, ws):
        d.text((x, y), c, font=font, fill=fill)
        x += w + track


def centered(d, y, text, font, fill, maxw=920, gap=1.18):
    lines = wrap(d, text, font, maxw)
    lh = font.size * gap
    for ln in lines:
        d.text(((W - d.textlength(ln, font=font)) / 2, y), ln, font=font, fill=fill)
        y += lh
    return y


def canvas(bg=CREAM):
    im = Image.new("RGB", (W, H), bg)
    return im, ImageDraw.Draw(im)


def top(d, kicker, title, sub=None, y=120, size=96, kcol=SAGE):
    tracked(d, W / 2, y, kicker, pop(34, "Medium"), kcol, 7)
    y = centered(d, y + 70, title, lora(size), NAVY, maxw=930, gap=1.1)
    if sub:
        y = centered(d, y + 18, sub, pop(38), SLATE, maxw=880, gap=1.4)
    return y


def pill(d, y=1770, text="MoonCyclePlanner on Etsy"):
    f = pop(38, "Medium")
    tw = d.textlength(text, font=f)
    x0, x1 = (W - tw) / 2 - 38, (W + tw) / 2 + 38
    d.rounded_rectangle((x0, y, x1, y + 68), radius=34, fill=ROSE)
    d.text(((W - tw) / 2, y + 9), text, font=f, fill=WHITE)


def paste_card(im, src, box, radius=28, shadow=True):
    """Paste src scaled to fit box (x0,y0,x1,y1) with rounded corners and soft shadow."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    s = src.copy()
    s.thumbnail((bw, bh), Image.LANCZOS)
    sw, sh = s.size
    px, py = x0 + (bw - sw) // 2, y0 + (bh - sh) // 2
    if shadow:
        sh_im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sh_im).rounded_rectangle((px, py + 14, px + sw, py + sh + 14), radius, fill=90)
        sh_im = sh_im.filter(ImageFilter.GaussianBlur(22))
        im.paste((150, 140, 130), (0, 0), sh_im)
    mask = Image.new("L", s.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw - 1, sh - 1), radius, fill=255)
    im.paste(s, (px, py), mask)
    return (px, py, px + sw, py + sh)


def paste_circle(im, src, cx, cy, r, ring=None):
    s = src.resize((2 * r, 2 * r), Image.LANCZOS)
    sh_im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh_im).ellipse((cx - r, cy - r + 12, cx + r, cy + r + 12), fill=80)
    im.paste((150, 140, 130), (0, 0), sh_im.filter(ImageFilter.GaussianBlur(20)))
    mask = Image.new("L", s.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    im.paste(s, (cx - r, cy - r), mask)
    if ring:
        ImageDraw.Draw(im).ellipse((cx - r, cy - r, cx + r, cy + r), outline=ring, width=4)


def moon(d, cx, cy, r, phase):
    """Moon icon in the calendar's convention: lit part white, dark part grey-blue."""
    box = (cx - r, cy - r, cx + r, cy + r)
    if phase == "new":
        d.ellipse(box, fill=MOONDARK)
    elif phase == "full":
        d.ellipse(box, fill=WHITE)
    elif phase == "waxing":  # first quarter: right side lit
        d.ellipse(box, fill=WHITE)
        d.pieslice(box, 90, 270, fill=MOONDARK)
    elif phase == "waning":  # last quarter: left side lit
        d.ellipse(box, fill=WHITE)
        d.pieslice(box, 270, 450, fill=MOONDARK)
    d.ellipse(box, outline=NAVY, width=4)


def prompt_card(d, chunk, start, fill):
    """Card of numbered prompts, sized to its content and centred between y=330 and y=1720."""
    qf, hf = lora(70), pop(42)
    blocks = []
    for q, hint in chunk:
        ql, hl = wrap(d, q, qf, 740), wrap(d, hint, hf, 730)
        blocks.append((ql, hl, len(ql) * 86 + 14 + len(hl) * 58))
    gap = 90
    inner = sum(b[2] for b in blocks) + gap * (len(blocks) - 1)
    pad = 80
    y0 = 330 + (1720 - 330 - inner - 2 * pad) // 2
    d.rounded_rectangle((60, y0, 1020, y0 + inner + 2 * pad), radius=36, fill=fill)
    yy = y0 + pad
    for n, (ql, hl, h) in enumerate(blocks, start=start):
        d.text((105, yy - 2), f"{n:02d}", font=lora(72), fill=ROSE)
        y2 = yy
        for ln in ql:
            d.text((225, y2), ln, font=qf, fill=NAVY)
            y2 += 86
        y2 += 14
        for ln in hl:
            d.text((227, y2), ln, font=hf, fill=SLATE)
            y2 += 58
        yy += h + gap


def save(im, name):
    im.save(os.path.join(OUT, name), quality=90, optimize=True)
    print("wrote", name)


# ---------- source crops (all from real listing-photo graphics in this repo) ----------
def load_sources():
    o = Image.open
    src = {}
    src["binder"] = o(f"{T}/howto-01-cover.jpg").crop((62, 690, 1018, 1643))      # sage binder on desk
    src["wheel_cb"] = o(f"{T}/howto-07-intention.jpg").crop((72, 681, 1008, 1617))  # Jan wheel, Celestial Bloom
    rq = o(f"{P}/pin-05-pink-2027-moon-planner-rose-quartz.jpg")
    src["wheel_rq"] = rq.crop((500 - 362, 865 - 362, 500 + 362, 865 + 362))        # Jan wheel, Rose Quartz (circle)
    src["page_rq"] = rq.crop((100, 640, 900, 1345))                                  # lower pink page
    src["frame"] = o(f"{P}/pin-01-plan-your-year-with-the-moon.jpg").crop((0, 560, 700, 1408))  # framed on wall
    src["year"] = o(f"{T}/howto-03-year.jpg")
    return src


def cover_photo(im, src, y0=None, y1=1690):
    return paste_card(im, src, (60, y0, 1020, y1))


# ---------- SET A: New moon journal prompts ----------
def set_newmoon(S):
    im, d = canvas()
    y = top(d, "NEW MOON JOURNAL PROMPTS", "6 questions to ask at the new moon", "Save this for your next new moon")
    moon(d, W // 2, int(y) + 70, 34, "new")
    cover_photo(im, S["binder"], int(y) + 140)
    pill(d)
    save(im, "newmoon-prompts-01-cover.jpg")

    prompts = [
        ("What do I want to begin this month?", "One thing. Write it in the centre of the wheel."),
        ("What would make this month feel good?", "Think feelings, not just tasks."),
        ("What am I ready to say yes to?", "A plan, a habit, a person, a place."),
        ("What's one small step I can take this week?", "Book it, start it, put it in the wheel."),
        ("What do I need more of right now?", "Rest, fun, focus, quiet, time outside."),
        ("Who do I want to be by the full moon?", "Come back and check in two weeks."),
    ]
    for i, chunk in enumerate((prompts[:3], prompts[3:])):
        im, d = canvas()
        tracked(d, W / 2, 120, f"NEW MOON PROMPTS  {i + 1} OF 2", pop(34, "Medium"), SAGE, 7)
        moon(d, W // 2, 250, 40, "new")
        prompt_card(d, chunk, 1 + 3 * i, WHITE)
        pill(d)
        save(im, f"newmoon-prompts-0{i + 2}.jpg")

    im, d = canvas()
    y = top(d, "THE 2027 MOON CYCLE CALENDAR", "Every new moon is already marked for you",
            "Write your intention in the centre of each month's wheel")
    paste_card(im, S["wheel_cb"], (110, int(y) + 60, 970, 1700))
    pill(d)
    save(im, "newmoon-prompts-04-cta.jpg")


# ---------- SET B: Full moon journal prompts ----------
def set_fullmoon(S):
    im, d = canvas(NAVY)
    tracked(d, W / 2, 120, "FULL MOON JOURNAL PROMPTS", pop(34, "Medium"), (214, 190, 150), 7)
    y = centered(d, 190, "6 questions to ask at the full moon", lora(96), WHITE, maxw=930, gap=1.1)
    y = centered(d, y + 18, "Reflect, celebrate, let go", pop(38), (200, 204, 222))
    moon(d, W // 2, int(y) + 70, 34, "full")
    paste_card(im, S["frame"], (60, int(y) + 140, 1020, 1690))
    pill(d)
    save(im, "fullmoon-prompts-01-cover.jpg")

    prompts = [
        ("What am I proud of since the new moon?", "Big or small, write it down."),
        ("What actually happened with my intention?", "No judging. Just notice."),
        ("What's ready to come off my list?", "Some things can simply go."),
        ("What drained me this month?", "Name it so you can plan around it."),
        ("What lit me up?", "Do more of that next cycle."),
        ("What do I want to carry into next month?", "Circle it on the next wheel."),
    ]
    for i, chunk in enumerate((prompts[:3], prompts[3:])):
        im, d = canvas(NAVY)
        tracked(d, W / 2, 120, f"FULL MOON PROMPTS  {i + 1} OF 2", pop(34, "Medium"), (214, 190, 150), 7)
        moon(d, W // 2, 250, 40, "full")
        prompt_card(d, chunk, 1 + 3 * i, CREAM)
        pill(d)
        save(im, f"fullmoon-prompts-0{i + 2}.jpg")

    im, d = canvas()
    y = top(d, "THE 2027 MOON CYCLE CALENDAR", "Every full moon of 2027, on one page",
            "Plus eclipses and Mercury retrograde")
    paste_card(im, S["year"].crop((130, 650, 936, 1694)), (80, int(y) + 50, 1000, 1700))
    pill(d)
    save(im, "fullmoon-prompts-04-cta.jpg")


# ---------- SET C: Plan by the moon sign ----------
ELEMENTS = [
    ("FIRE", "Aries · Leo · Sagittarius", "♈ ♌ ♐", (196, 120, 96),
     "Start things", ["Kick off a new project", "Workouts and moving your body", "Bold asks and big decisions"]),
    ("EARTH", "Taurus · Virgo · Capricorn", "♉ ♍ ♑", SAGE,
     "Get practical", ["Budgets, bills and admin", "Meal prep and home projects", "Finish what you started"]),
    ("AIR", "Gemini · Libra · Aquarius", "♊ ♎ ♒", (110, 140, 180),
     "Talk it out", ["Emails, calls and catch-ups", "Brainstorms and learning", "Plans with friends"]),
    ("WATER", "Cancer · Scorpio · Pisces", "♋ ♏ ♓", (120, 110, 170),
     "Turn inward", ["Rest and cozy nights in", "Journaling and creative time", "Quality time at home"]),
]


def set_moonsign(S):
    im, d = canvas()
    y = top(d, "ASTROLOGY PLANNING", "Plan by the moon sign",
            "The moon changes sign every 2–3 days. Here's what each one is good for.")
    paste_card(im, S["wheel_cb"], (150, int(y) + 50, 930, 1700))
    pill(d)
    save(im, "moonsign-01-cover.jpg")

    for i, (el, signs, glyphs, col, verb, items) in enumerate(ELEMENTS, start=2):
        im, d = canvas()
        tracked(d, W / 2, 130, f"MOON IN {el} SIGNS", pop(36, "Medium"), col, 8)
        gf = ImageFont.truetype(SYM, 110)
        gw = d.textlength(glyphs, font=gf)
        d.text(((W - gw) / 2, 210), glyphs, font=gf, fill=col)
        centered(d, 370, signs, pop(40), SLATE)
        centered(d, 470, verb, lora(130), NAVY)
        itf = lora(66, "Medium")
        rows = [wrap(d, it, itf, 700) for it in items]
        inner = sum(len(r) * 84 for r in rows) + 100 * (len(rows) - 1)
        y0 = 700 + (1560 - 700 - inner - 180) // 2
        d.rounded_rectangle((80, y0, 1000, y0 + inner + 180), radius=36, fill=WHITE)
        yy = y0 + 90
        for r in rows:
            d.ellipse((145, yy + 28, 179, yy + 62), fill=col)
            for ln in r:
                d.text((220, yy), ln, font=itf, fill=NAVY)
                yy += 84
            yy += 100
        centered(d, 1615, "Moon signs (with times) are printed on every day of the wheel", pop(36), SLATE, maxw=900)
        pill(d)
        save(im, f"moonsign-0{i}-{el.lower()}.jpg")

    im, d = canvas()
    y = top(d, "THE 2027 MOON CYCLE CALENDAR", "No app needed: it's all on the wheel",
            "Moon phase, moon sign and time for every day of 2027")
    paste_card(im, S["binder"], (60, int(y) + 60, 1020, 1700))
    pill(d)
    save(im, "moonsign-06-cta.jpg")


# ---------- SET D: Which one are you? (colorways) ----------
def set_colorways(S):
    im, d = canvas()
    y = top(d, "THIS OR THAT", "Which 2027 moon calendar are you?", "Same calendar, two colorways. Tell me in the comments!")
    r = 300
    cy1 = int(y) + 60 + r
    cy2 = cy1 + 510
    paste_circle(im, S["wheel_cb"].crop((39, 0, 897, 858)), 340, cy1, r)
    paste_circle(im, S["wheel_rq"], 740, cy2, r)
    f = lora(56)
    d.text((690, cy1 - 70), "Celestial", font=f, fill=NAVY)
    d.text((690, cy1 - 4), "Bloom", font=f, fill=NAVY)
    d.text((90, cy2 - 40), "Rose", font=f, fill=NAVY)
    d.text((90, cy2 + 26), "Quartz", font=f, fill=NAVY)
    d.text((880, cy1 + 150), "or", font=lora(70, "Regular"), fill=ROSE)
    pill(d)
    save(im, "colorway-01-cover.jpg")

    im, d = canvas()
    y = top(d, "CELESTIAL BLOOM", "For the girl who loves every color of the sky",
            "Patina blue, copper, dusty rose, sage and gold")
    paste_card(im, S["wheel_cb"], (110, int(y) + 60, 970, 1700))
    pill(d)
    save(im, "colorway-02-celestial-bloom.jpg")

    im, d = canvas(BLUSH)
    y = top(d, "ROSE QUARTZ", "For the girl whose whole aesthetic is pink",
            "Soft pinks on every page", kcol=ROSE)
    paste_card(im, S["page_rq"], (80, int(y) + 60, 1000, 1700))
    pill(d)
    save(im, "colorway-03-rose-quartz.jpg")


# ---------- SET E: 3 ways to use it ----------
def set_ways(S):
    im, d = canvas()
    y = top(d, "PRINTABLE MOON CALENDAR", "3 ways to use your 2027 moon calendar", "Print at home. Use it your way.")
    paste_card(im, S["frame"], (110, int(y) + 60, 970, 1700))
    pill(d)
    save(im, "ways-01-cover.jpg")

    ways = [
        ("1", "In a binder", "Hole-punch the pages and keep your whole year in one place.", S["binder"], "ways-02-binder.jpg"),
        ("2", "Framed on the wall", "Frame the year page or this month's wheel and swap it monthly.", S["frame"], "ways-03-frame.jpg"),
        ("3", "One month at a time", "Print just this month's wheel and add plans as they come.", S["wheel_cb"], "ways-04-month.jpg"),
    ]
    for n, title, body, img, name in ways:
        im, d = canvas()
        tracked(d, W / 2, 120, f"WAY {n} OF 3", pop(34, "Medium"), SAGE, 7)
        y = centered(d, 190, title, lora(100), NAVY)
        y = centered(d, y + 18, body, pop(38), SLATE, maxw=860, gap=1.4)
        paste_card(im, img, (80, int(y) + 60, 1000, 1700))
        pill(d)
        save(im, name)


if __name__ == "__main__":
    S = load_sources()
    set_newmoon(S)
    set_fullmoon(S)
    set_moonsign(S)
    set_colorways(S)
    set_ways(S)
