"""Hire Commons job explainer video: 1080x1350 (4:5), 30 fps, AI voice-over, burned-in captions.

Usage:
  python3 make_job_video.py job.json out.mp4            # full render
  python3 make_job_video.py job.json out.mp4 --preview  # contact sheet only (out.png) to check layout

job.json (see job-example.json):
  town_caps   badge text location, e.g. "SOMERS, CT"
  town        display town, e.g. "Somers, CT"
  title       job title
  employer    employer name
  pay         e.g. "$17.50–$23.80/hr", or "" if no pay listed
  chips       1-3 short facts shown under the pay, e.g. ["Full time", "Day shift"]
  highlights  2-4 rows: [{"t": "Benefits from day one", "s": "Medical, dental, vision"}, ...]
  voice_lines 5 lines in SPOKEN spelling (one per scene):
              [hook/town, employer+title, pay (or schedule if no pay), highlights, call to action]
  captions    the same 5 lines in normal spelling ($17.50, 40 hours, hirecommons.com)
  voice       "af_heart" (default, warm female) or "am_michael" (male)
Only use facts from the job page.
"""
import json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

W, H, FPS, M = 1080, 1350, 30, 90
GREEN, GREEN_DK = (31, 111, 74), (17, 70, 46)
BLUE, WHITE = (37, 99, 235), (255, 255, 255)
MINT, CARD, CAPBG = (205, 233, 217), (44, 130, 90), (10, 42, 28)
LEAD, GAP, TAIL = 0.45, 0.45, 2.6
INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(weight, size):
    try:
        return ImageFont.truetype(INTER.format(weight), size)
    except OSError:
        return ImageFont.truetype(FALLBACK, size)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = w
    out.append(cur)
    return out


def fit(d, text, weight, size, maxw, maxlines, minsize=48):
    while size > minsize:
        f = font(weight, size)
        ls = wrap(d, text, f, maxw)
        if len(ls) <= maxlines and all(d.textlength(l, font=f) <= maxw for l in ls):
            return f
        size -= 4
    return font(weight, minsize)


class Layer:
    def __init__(self):
        self.im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)


def put(base, L, a):
    if a <= 0:
        return
    a = ease(a)
    im = L.im
    if a < 1:
        r, g, b, al = im.split()
        im = Image.merge("RGBA", (r, g, b, al.point(lambda v: int(v * a))))
    base.alpha_composite(im, (0, int((1 - a) * 40)))


def text_block(L, x, y, text, f, fill, maxw=W - 2 * M, lh=None, anchor_center=False):
    lh = lh or int(f.size * 1.18)
    for line in wrap(L.d, text, f, maxw):
        if anchor_center:
            L.d.text((W // 2, y), line, font=f, fill=fill, anchor="ma")
        else:
            L.d.text((x, y), line, font=f, fill=fill)
        y += lh
    return y


def make_background(badge):
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(GREEN[i] + (GREEN_DK[i] - GREEN[i]) * k) for i in range(3)))
    # badge pill
    bf = font("Bold", 28)
    bw = d.textlength(badge, font=bf)
    d.rounded_rectangle([M, 80, M + bw + 64, 142], radius=31, fill=WHITE)
    d.text((M + 32, 111), badge, font=bf, fill=GREEN, anchor="lm")
    # footer: arch icon + wordmark + blue dot, tagline, url
    fy = H - 150
    d.line([(M, fy), (W - M, fy)], fill=(80, 150, 112), width=2)
    ix, iy = M, fy + 34
    d.arc([ix, iy, ix + 44, iy + 44], 180, 360, fill=WHITE, width=8)
    d.line([(ix + 4, iy + 22), (ix + 4, iy + 60)], fill=WHITE, width=8)
    d.line([(ix + 40, iy + 22), (ix + 40, iy + 60)], fill=WHITE, width=8)
    wf = font("ExtraBold", 38)
    d.text((ix + 62, iy - 2), "HireCommons", font=wf, fill=WHITE)
    ww = d.textlength("HireCommons", font=wf)
    d.rectangle([ix + 66 + ww, iy + 28, ix + 78 + ww, iy + 40], fill=BLUE)
    d.text((ix + 62, iy + 46), "Good work, close to home.", font=font("Medium", 24), fill=MINT)
    d.text((W - M, fy + 58), "hirecommons.com", font=font("Bold", 28), fill=WHITE, anchor="rm")
    return bg


CAPF = None


def caption(base, text, t, dur):
    d = ImageDraw.Draw(base)
    lines = wrap(d, text, CAPF, W - 2 * M - 60)
    chunks = [" ".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]
    tot = sum(map(len, chunks)) or 1
    acc, cur = 0, chunks[-1]
    for c in chunks:
        if t < dur * (acc + len(c)) / tot:
            cur = c
            break
        acc += len(c)
    cl = wrap(d, cur, CAPF, W - 2 * M - 60)
    boxh = 48 * len(cl) + 36
    y0 = H - 190 - boxh
    d.rounded_rectangle([M, y0, W - M, y0 + boxh], radius=18, fill=CAPBG)
    for i, line in enumerate(cl):
        d.text((W // 2, y0 + 18 + 48 * i + 24), line, font=CAPF, fill=WHITE, anchor="mm")


# ---------- scenes: each returns [(Layer, appear_time_in_scene)] ----------
TOP = 330  # content starts here (well below the badge, centered in the space above captions)
CAP_TOP = H - 190 - 132  # keep content above a 2-line caption box


def scene_hook(job, s, dur):
    a = Layer()
    a.d.text((M, TOP + 120), "NOW HIRING IN", font=font("Bold", 40), fill=MINT)
    b = Layer()
    tf = fit(b.d, job["town"], "Black", 150, W - 2 * M, 2, 80)
    y = text_block(b, M, TOP + 180, job["town"], tf, WHITE)
    b.d.rectangle([M, y + 24, M + 160, y + 32], fill=BLUE)
    c = Layer()
    c.d.text((M, y + 70), "Good work, close to home.", font=font("SemiBold", 40), fill=MINT)
    return [(a, s[0]), (b, s[0] + 0.3), (c, s[0] + 1.2)]


def scene_job(job, s, dur):
    a = Layer()
    a.d.text((M, TOP + 60), job["employer"].upper(), font=fit(a.d, job["employer"].upper(), "Bold", 40, W - 2 * M, 1, 28), fill=MINT)
    b = Layer()
    tf = fit(b.d, job["title"], "Black", 120, W - 2 * M, 3, 64)
    y = text_block(b, M, TOP + 130, job["title"], tf, WHITE)
    b.d.rectangle([M, y + 24, M + 160, y + 32], fill=BLUE)
    c = Layer()
    c.d.text((M, y + 70), job["town"], font=font("SemiBold", 42), fill=MINT)
    return [(a, s[0]), (b, s[0] + 0.25), (c, s[0] + 0.9)]


def chip_row(L, x, y, chips):
    f = font("Bold", 34)
    for ch in chips[:3]:
        w = L.d.textlength(ch, font=f) + 56
        L.d.rounded_rectangle([x, y, x + w, y + 70], radius=35, outline=WHITE, width=3)
        L.d.text((x + w / 2, y + 35), ch, font=f, fill=WHITE, anchor="mm")
        x += w + 20


def scene_pay(job, s, dur):
    a = Layer()
    big = job.get("pay") or (job.get("chips") or [""])[0]
    a.d.text((M, TOP + 120), "THE PAY" if job.get("pay") else "THE SCHEDULE", font=font("Bold", 40), fill=MINT)
    b = Layer()
    pf = fit(b.d, big, "Black", 140, W - 2 * M - 80, 2, 56)
    lines = wrap(b.d, big, pf, W - 2 * M - 80)
    lh = int(pf.size * 1.15)
    boxh = lh * len(lines) + 70
    b.d.rounded_rectangle([M, TOP + 190, W - M, TOP + 190 + boxh], radius=36, fill=WHITE)
    y = TOP + 190 + 35
    for line in lines:
        b.d.text((W // 2, y), line, font=pf, fill=GREEN, anchor="ma")
        y += lh
    c = Layer()
    chips = job.get("chips", []) if job.get("pay") else job.get("chips", [])[1:]
    chip_row(c, M, TOP + 190 + boxh + 50, chips)
    return [(a, s[0]), (b, s[0] + 0.3), (c, s[0] + 1.0)]


def scene_highlights(job, s, dur):
    rows = job.get("highlights", [])[:4]
    out = []
    head = Layer()
    head.d.text((M, TOP - 60), "WHY IT'S WORTH A LOOK", font=font("Bold", 40), fill=MINT)
    out.append((head, s[0]))
    rowh, gap = 170, 26
    total = len(rows) * rowh + (len(rows) - 1) * gap
    y = TOP + 10
    if y + total > CAP_TOP:
        rowh = (CAP_TOP - y - (len(rows) - 1) * gap) // max(1, len(rows))
    for i, r in enumerate(rows):
        L = Layer()
        L.d.rounded_rectangle([M, y, W - M, y + rowh], radius=24, fill=CARD)
        cx, cy = M + 60, y + rowh // 2
        L.d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=WHITE)
        L.d.line([(cx - 14, cy + 1), (cx - 4, cy + 12), (cx + 16, cy - 12)], fill=GREEN, width=8)
        tf = fit(L.d, r["t"], "Bold", 40, W - 2 * M - 150, 1, 28)
        if r.get("s"):
            L.d.text((M + 120, cy - 8), r["t"], font=tf, fill=WHITE, anchor="ls")
            L.d.text((M + 120, cy + 10), r["s"], font=fit(L.d, r["s"], "Medium", 30, W - 2 * M - 150, 1, 22), fill=MINT, anchor="lt")
        else:
            L.d.text((M + 120, cy), r["t"], font=tf, fill=WHITE, anchor="lm")
        out.append((L, s[0] + 0.15 + dur * 0.8 * i / max(1, len(rows))))
        y += rowh + gap
    return out


def scene_cta(job, s, dur):
    a = Layer()
    a.d.text((W // 2, TOP + 110), "APPLY TODAY", font=font("Bold", 44), fill=MINT, anchor="ma")
    b = Layer()
    tf = fit(b.d, job["title"], "Black", 84, W - 2 * M, 2, 56)
    y = text_block(b, M, TOP + 180, job["title"], tf, WHITE, anchor_center=True)
    c = Layer()
    bf = font("ExtraBold", 54)
    bw = c.d.textlength("hirecommons.com", font=bf) + 100
    x0 = (W - bw) / 2
    c.d.rounded_rectangle([x0, y + 50, x0 + bw, y + 160], radius=55, fill=WHITE)
    c.d.text((W // 2, y + 105), "hirecommons.com", font=bf, fill=GREEN, anchor="mm")
    d2 = Layer()
    d2.d.text((W // 2, y + 210), "Good work, close to home.", font=font("SemiBold", 44), fill=MINT, anchor="ma")
    return [(a, s[0]), (b, s[0] + 0.25), (c, s[0] + 0.8), (d2, s[0] + 1.6)]


SCENES = [scene_hook, scene_job, scene_pay, scene_highlights, scene_cta]


def main():
    global CAPF
    cfg_path, out = sys.argv[1], sys.argv[2]
    preview = "--preview" in sys.argv
    job = json.load(open(cfg_path))
    assert len(job["voice_lines"]) == 5 and len(job["captions"]) == 5, "need exactly 5 voice_lines and 5 captions"
    CAPF = font("SemiBold", 36)
    work = tempfile.mkdtemp(prefix="hcvid_")
    json.dump(job["voice_lines"], open(f"{work}/lines.json", "w"))
    subprocess.run(["python3", os.path.expanduser("~/tts/tts.py"), job.get("voice", "af_heart"), f"{work}/lines.json", f"{work}/vo"], check=True)
    durs = json.load(open(f"{work}/vo/durs.json"))

    # timeline: one scene per voice line
    plan, t = [], 0.0
    for i, fn in enumerate(SCENES):
        lead = LEAD if i == 0 else 0.15
        dur = lead + durs[i] + GAP + (TAIL if i == len(SCENES) - 1 else 0)
        plan.append((fn, t, dur, lead))
        t += dur
    total = t
    bg = make_background(f"NOW HIRING  •  {job['town_caps']}")
    built = [(fn(job, [lead], dur), t0, dur, lead, i) for i, (fn, t0, dur, lead) in enumerate(plan)]

    def frame(T):
        for layers, t0, dur, lead, i in built:
            if T < t0 + dur or i == len(built) - 1:
                break
        st = T - t0
        base = bg.copy().convert("RGBA")
        for L, at in layers:
            put(base, L, (st - at) / 0.45)
        if st >= lead - 0.05:
            caption(base, job["captions"][i], st - lead, durs[i])
        im = base.convert("RGB")
        a = 1.0
        if i > 0:
            a = min(a, st / 0.3)
        if i < len(built) - 1:
            a = min(a, (dur - st) / 0.3)
        return im if a >= 1 else Image.blend(bg, im, max(0.0, a))

    if preview:
        shots = [frame(t0 + min(dur - 0.4, lead + durs[i] * 0.95)) for layers, t0, dur, lead, i in built]
        sheet = Image.new("RGB", (540 * 5, 675), WHITE)
        for k, im in enumerate(shots):
            sheet.paste(im.resize((540, 675)), (540 * k, 0))
        sheet.save(out[:-4] + ".png")
        print("preview", out[:-4] + ".png", "total", round(total, 1))
        return

    # voice track
    sr = 24000
    audio = np.zeros(int((total + 0.5) * sr), dtype=np.float32)
    for (layers, t0, dur, lead, i) in built:
        _, w = wavfile.read(f"{work}/vo/line{i:02d}.wav")
        w = w.astype(np.float32) / 32767
        st = int((t0 + lead) * sr)
        audio[st:st + len(w)] += w[: len(audio) - st]
    peak = np.abs(audio).max() or 1
    audio = audio / peak * 0.89
    wavfile.write(f"{work}/voice.wav", sr, (audio * 32767).astype(np.int16))

    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", f"{work}/voice.wav", "-map", "0:v", "-map", "1:a",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for n in range(int(round(total * FPS))):
        p.stdin.write(frame(n / FPS).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg failed")
    # cover image for the post thumbnail (pay scene)
    layers, t0, dur, lead, i = built[2]
    frame(t0 + lead + durs[2]).save(out[:-4] + "-cover.jpg", quality=90)
    print("done", out, round(total, 1), "sec")


if __name__ == "__main__":
    main()
