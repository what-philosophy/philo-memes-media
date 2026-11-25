"""what_philosophy renderer v2.

Usage: python3 render2.py posts/2026-KW50.json OUTDIR
Each post is a sequence of items:
  {"type": "hook", "text": ...}                      white slide, Inter, "swipe ->"
  {"type": "meme", "text": ..., "size": 110}         white slide, Inter
  {"type": "short", "label": "nietzsche:"?, "text": ..., "src": ...}   paper, italic
  {"type": "passage", "src": ..., "shrink": false,
   "pieces": [{"file": ..., "start": ..., "end": ...}, ...]}  paper, justified,
        text is cut from sources/<file> verbatim from start to end (inclusive);
        several pieces are joined with "[...]"
  {"type": "payoff", "text": ...}                    white slide, Inter
Writes OUTDIR/<id>/ig/NN.png (1080x1350) and OUTDIR/<id>/tt/NN.png (1080x1920).
"""
import json, os, re, sys, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
G = "/usr/share/fonts/truetype/google-fonts/ofl/"
SERIF = G + "crimsontext/CrimsonText-Regular.ttf"
SERIF_I = G + "crimsontext/CrimsonText-Italic.ttf"
SERIF_SB = G + "crimsontext/CrimsonText-SemiBold.ttf"
GREEK = G + "cardo/Cardo-Regular.ttf"
SANS = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
SANS_B = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

FORMATS = {
    "ig": (1080, 1350, 96, 110, 96, 120),
    "tt": (1080, 1920, 96, 250, 150, 430),  # TikTok safe zone
}
PAPER = (241, 234, 218)
INK = (38, 33, 28)
MUTED = (122, 110, 95)
WHITE = (255, 255, 255)
BLACK = (15, 15, 15)


def font(path, size):
    return ImageFont.truetype(path, size)


def has_greek(s):
    return bool(re.search(r"[Ͱ-Ͽἀ-῿]", s))


# ---------- source extraction ----------

def clean(text):
    text = text.replace("\r", "")
    text = re.sub(r"\[Note[^\]]*\]", "", text)
    text = text.replace("--", "—")
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Gutenberg marks italics as CAPS; turn emphasised words back to lower case
    def low(m):
        w = m.group(0)
        return w.lower() if len(w) > 1 else w
    text = re.sub(r"\b[A-Z]{2,}\b", low, text)
    paras = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    paras = [p[0].upper() + p[1:] for p in paras if p]
    return "\n\n".join(paras)


def cut(piece):
    raw = open(os.path.join(HERE, "sources", piece["file"]), encoding="utf-8").read()
    flat = re.sub(r"[ \t]*\n[ \t]*", "\n", raw)
    # match start/end across line breaks
    def find(s, frm=0):
        pat = r"\s+".join(re.escape(w) for w in s.split())
        m = re.compile(pat).search(flat, frm)
        if not m:
            raise SystemExit(f"not found in {piece['file']}: {s!r}")
        return m
    a = find(piece["start"])
    b = find(piece["end"], a.start())
    seg = flat[a.start():b.end()]
    seg = seg.replace("\n\n", "\x00").replace("\n", " ").replace("\x00", "\n\n")
    seg = clean(seg)
    for a_, b_ in piece.get("fix", []):  # documented OCR corrections
        seg = seg.replace(a_, b_)
    return seg


def passage_text(item):
    return "\n\n[...]\n\n".join(cut(p) for p in item["pieces"])


# ---------- drawing ----------

def paper_bg(w, h, seed):
    random.seed(seed)
    img = Image.new("RGB", (w, h), PAPER)
    noise = Image.effect_noise((w, h), 18).convert("L")
    tint = Image.new("RGB", (w, h), (205, 192, 165))
    img = Image.composite(img, tint, noise.point(lambda v: 255 - max(0, v - 120) // 3))
    vig = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(vig)
    d.rectangle([0, 0, w, h], outline=60, width=int(w * 0.06))
    vig = vig.filter(ImageFilter.GaussianBlur(w * 0.06))
    dark = Image.new("RGB", (w, h), (170, 155, 125))
    return Image.composite(dark, img, vig)


def wrap_words(draw, text, f, maxw):
    lines, cur = [], []
    for wd in text.split():
        trial = " ".join(cur + [wd])
        if draw.textlength(trial, font=f) <= maxw or not cur:
            cur.append(wd)
        else:
            lines.append(cur)
            cur = [wd]
    if cur:
        lines.append(cur)
    return lines


def draw_justified(draw, x, y, words, f, maxw, last):
    if last or len(words) == 1:
        draw.text((x, y), " ".join(words), font=f, fill=INK)
        return
    total = sum(draw.textlength(w, font=f) for w in words)
    gap = (maxw - total) / (len(words) - 1)
    cx = x
    for w in words:
        draw.text((cx, y), w, font=f, fill=INK)
        cx += draw.textlength(w, font=f) + gap


def body_font(text, size):
    return font(GREEK if has_greek(text) else SERIF, size)


def paginate(text, fmt, sizes):
    w, h, l, t, r, b = FORMATS[fmt]
    maxw = w - l - r
    avail = h - t - b - 120 - 70
    dummy = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    queue = [(p.strip(), True) for p in text.split("\n\n")]
    pages, pi = [], 0
    while queue:
        size = sizes(pi)
        lh = int(size * 1.32)
        pgap = int(size * 0.55)
        used, page = 0, []
        while queue:
            ptxt, newp = queue[0]
            f = body_font(ptxt, size)
            if page and newp:
                if used + pgap + lh > avail:
                    break
                used += pgap
            lines = wrap_words(dummy, ptxt, f, maxw)
            fit = max(0, (avail - used) // lh)
            if fit == 0:
                break
            take = lines[:fit]
            page.append((take, len(take) == len(lines), has_greek(ptxt)))
            used += len(take) * lh
            if len(take) == len(lines):
                queue.pop(0)
            else:
                queue[0] = (" ".join(" ".join(ws) for ws in lines[fit:]), False)
                break
        pages.append((size, page))
        pi += 1
    return pages


def text_slide(fmt, size, page, src, tag, idx, total, seed):
    w, h, l, t, r, b = FORMATS[fmt]
    img = paper_bg(w, h, seed)
    d = ImageDraw.Draw(img)
    maxw = w - l - r
    d.text((l, t), tag, font=font(SERIF_I, 38), fill=MUTED)
    d.text((l, t + 52), src.upper(), font=font(SERIF_SB, 22), fill=MUTED)
    d.line([l, t + 96, w - r, t + 96], fill=(180, 166, 140), width=2)
    lh = int(size * 1.32)
    pgap = int(size * 0.55)
    y = t + 130
    for n, (lines, ends, greek) in enumerate(page):
        if n:
            y += pgap
        f = font(GREEK if greek else SERIF, size)
        for i, ws in enumerate(lines):
            last = ends and i == len(lines) - 1
            if " ".join(ws) == "[...]":
                d.text((l, y), "[...]", font=f, fill=MUTED)
            else:
                draw_justified(d, l, y, ws, f, maxw, last)
            y += lh
    d.text((w - r, h - b + 20), f"{idx}/{total}", font=font(SERIF_I, 30), fill=MUTED, anchor="ra")
    return img


def white_slide(fmt, text, size, sub=None):
    w, h, l, t, r, b = FORMATS[fmt]
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    f = font(SANS, size)
    maxw = w - l - r
    blocks = [[" ".join(ws) for ws in wrap_words(d, p, f, maxw)] for p in text.split("\n\n")]
    lh, gap = int(size * 1.25), int(size * 0.7)
    th = sum(len(bl) * lh for bl in blocks) + gap * (len(blocks) - 1)
    y = t + (h - t - b - th) // 2
    for bl in blocks:
        for line in bl:
            d.text((l, y), line, font=f, fill=BLACK)
            y += lh
        y += gap
    if sub:
        d.text((l, h - b + 10), sub, font=font(SANS, 30), fill=(150, 150, 150))
    return img


def short_slide(fmt, label, text, src, seed):
    w, h, l, t, r, b = FORMATS[fmt]
    img = paper_bg(w, h, seed)
    d = ImageDraw.Draw(img)
    maxw = w - l - r
    if label:
        d.text((l, t), label, font=font(SANS_B, 56), fill=BLACK)
    f = font(SERIF_I, 64)
    lines = [" ".join(ws) for ws in wrap_words(d, text, f, maxw)]
    lh = 84
    y = t + (h - t - b - len(lines) * lh) // 2
    for line in lines:
        d.text((l, y), line, font=f, fill=INK)
        y += lh
    d.text((l, h - b - 10), src.upper(), font=font(SERIF_SB, 22), fill=MUTED)
    return img


SHRINK = [48, 38, 30, 24, 20]


def build(post, fmt, outdir):
    slides = []
    for k, it in enumerate(post["items"]):
        ty = it["type"]
        if ty == "hook":
            slides.append(white_slide(fmt, it["text"], it.get("size", 74), sub="swipe →"))
        elif ty in ("meme", "payoff"):
            slides.append(white_slide(fmt, it["text"], it.get("size", 110 if ty == "meme" else 72)))
        elif ty == "short":
            slides.append(short_slide(fmt, it.get("label"), it["text"], it["src"], seed=k))
        elif ty == "passage":
            text = passage_text(it)
            sizes = (lambda i: SHRINK[min(i, 4)]) if it.get("shrink") else (lambda i: it.get("size", 44))
            pages = paginate(text, fmt, sizes)
            for i, (size, page) in enumerate(pages):
                slides.append(text_slide(fmt, size, page, it["src"], post["tag"], i + 1, len(pages), seed=i))
    if len(slides) > 10:
        raise SystemExit(f"{post['id']}: {len(slides)} slides, max 10")
    d = os.path.join(outdir, post["id"], fmt)
    os.makedirs(d, exist_ok=True)
    for i, s in enumerate(slides, 1):
        s.save(os.path.join(d, f"{i:02d}.png"))
    return len(slides)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    only = sys.argv[3:]
    for p in spec["posts"]:
        if only and p["id"] not in only:
            continue
        for fmt in FORMATS:
            print(p["id"], fmt, build(p, fmt, out), "slides")
