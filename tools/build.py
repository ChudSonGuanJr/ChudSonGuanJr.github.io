"""Generates index.html and work/<slug>/index.html from content/projects.json.

Run from anywhere:  python tools/build.py
Needs Pillow (pip install pillow) to create thumbnails and read image sizes.
"""
import html
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
THUMB_WIDTH = 960
LATIN = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
LATIN_EXT = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"
FONT_STACK = "system-ui, sans-serif"
COLORS = {"bg": "#0b0a0c", "heading": "#f1ece6", "text": "#f1ece6", "muted": "#a59e98", "accent": "#ff7a2f"}

e = html.escape


def size(slug, name):
    with Image.open(ROOT / "assets/img" / slug / name) as im:
        return im.size


def thumb(slug, name):
    """Creates a small webp next to the full image and returns its filename."""
    source = ROOT / "assets/img" / slug / name
    target = source.parent / "thumbs" / (source.stem + ".webp")
    if not target.exists():
        target.parent.mkdir(exist_ok=True)
        with Image.open(source) as im:
            im = im.convert("RGB")
            if im.width > THUMB_WIDTH:
                im = im.resize((THUMB_WIDTH, round(im.height * THUMB_WIDTH / im.width)), Image.LANCZOS)
            im.save(target, "WEBP", quality=80, method=6)
    return target.name


def chosen_fonts(site):
    catalog = json.loads((ROOT / "assets/fonts/fonts.json").read_text(encoding="utf-8"))
    fonts = site.get("fonts", {})
    pick = lambda key: fonts.get(key) if fonts.get(key) in catalog else "Archivo"
    return pick("heading"), pick("body"), catalog


def theme(site, base):
    heading, body, catalog = chosen_fonts(site)
    faces = preloads = ""
    for name in dict.fromkeys([heading, body]):
        font = catalog[name]
        stretch = f"font-stretch: {font['stretch']};" if font.get("stretch") else ""
        for subset, ranges in (("latin", LATIN), ("latin-ext", LATIN_EXT)):
            href = f"{base}assets/fonts/{font['file']}-{subset}.woff2"
            preloads += f'<link rel="preload" href="{href}" as="font" type="font/woff2" crossorigin>\n'
            faces += (f'@font-face {{ font-family: "{name}"; src: url("{href}") format("woff2"); font-weight: 100 900; '
                      f"{stretch} font-display: block; unicode-range: {ranges}; }}\n")
    colors = {**COLORS, **site.get("colors", {})}
    values = "".join(f"--{k}: {v};" for k, v in colors.items() if re.fullmatch(r"#[0-9a-fA-F]{6}", v))
    values += f'--font: "{body}", {FONT_STACK};--font-heading: "{heading}", {FONT_STACK};'
    for key, percent in site.get("sizes", {}).items():
        if key in ("title", "heading", "body", "small"):
            values += f"--size-{key}: {min(max(int(percent), 50), 200) / 100};"
    return f"{preloads}<style>\n{faces}:root {{ {values} }}\n</style>"


def navigation(data, base, current):
    site, projects = data["site"], data["projects"]
    links = [("Environments", f"{base}environment/index.html")]
    links += [(p["title"], f"{base}work/{p['slug']}/index.html") for p in projects if p.get("nav")]
    html_links = ""
    for label, href in links:
        state = ' aria-current="page"' if label == current else ""
        html_links += f'<a href="{e(href)}" data-label="{e(label)}"{state}>{e(label)}</a>'
    return f'{html_links}<a href="{e(site["artstation"])}" rel="me noopener" data-label="ArtStation">ArtStation</a>'


def page(data, title, description, body, base, image=None, current=None):
    site = data["site"]
    meta_image = f'<meta property="og:image" content="{e(image)}">' if image else ""
    first, bracket, rest = site["name"].partition(" (")
    wordmark = e(first) + (f'<span class="wordmark-extra"> ({e(rest)}</span>' if bracket else "")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:type" content="website">
{meta_image}
<link rel="stylesheet" href="{base}assets/css/style.css">
{theme(site, base)}
<script src="{base}assets/js/main.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <a class="wordmark" href="{base}index.html">{wordmark}</a>
  <nav aria-label="Main">{navigation(data, base, current)}</nav>
</header>
<main id="main">
{body}
</main>
<footer class="footer">
  <span>© {e(site['name'])}</span>
  <a href="{e(site['artstation'])}" rel="me noopener">{e(site['artstation'].split('//')[-1].removeprefix('www.'))}</a>
</footer>
</body>
</html>
"""


def card(p, base):
    name = p.get("thumbnail") or p["cover"]
    w, h = size(p["slug"], name)
    src = f"{base}assets/img/{p['slug']}/{name}"
    if w > THUMB_WIDTH and not name.endswith(".gif"):
        src = f"{base}assets/img/{p['slug']}/thumbs/{thumb(p['slug'], name)}"
    return f"""<li class="card">
  <a href="{base}work/{p['slug']}/index.html">
    <span class="card-image"><img src="{src}" width="{w}" height="{h}" alt="{e(p['title'])}" loading="lazy"></span>
    <span class="card-text">
      <span class="card-title">{e(p['title'])}</span>
    </span>
  </a>
</li>"""


def door(site, key, label, href, fallback):
    """A large image button on the home page, using the chosen image or the fallback's banner."""
    pick = site.get("doors", {}).get(key, {})
    slug, name = pick.get("project"), pick.get("image")
    if not slug or not name or not (ROOT / "assets/img" / slug / name).exists():
        slug, name = fallback["slug"], fallback["cover"]
    src = f"assets/img/{slug}/{name}"
    if size(slug, name)[0] > THUMB_WIDTH and not name.endswith(".gif"):
        src = f"assets/img/{slug}/thumbs/{thumb(slug, name)}"
    return f"""<a class="door" href="{href}">
  <img src="{src}" alt="" loading="lazy">
  <span>{e(label)}</span>
</a>"""


def contact(site):
    if site.get("email"):
        return f'<a class="cta" href="mailto:{e(site["email"])}">{e(site["email"])}</a>'
    return ""


def index(data):
    site, projects = data["site"], data["projects"]
    by_slug = {p["slug"]: p for p in projects}

    slides = []
    for i, h in enumerate(site["hero"]):
        p = by_slug[h["project"]]
        w, _ = size(p["slug"], h["image"])
        loading = 'fetchpriority="high"' if i == 0 else 'loading="lazy"'
        slides.append(
            f'<figure class="slide{" is-active" if i == 0 else ""}">'
            f'<img src="assets/img/{p["slug"]}/{h["image"]}" alt="{e(p["title"])}" {loading}>'
            f'<figcaption><a href="work/{p["slug"]}/index.html">{e(p["title"])}</a></figcaption></figure>'
        )

    environment = [p for p in projects if not p.get("nav")]
    doors = door(site, "environment", "Environments", "environment/index.html", environment[0]) if environment else ""
    doors += "".join(door(site, p["slug"], p["title"], f"work/{p['slug']}/index.html", p) for p in projects if p.get("nav"))

    experience = ""
    for x in site["experience"]:
        years = f'<small>{e(x["years"])}</small>' if x.get("years") else ""
        experience += f"<li><strong>{e(x['name'])}</strong>{years}<span>{e(x.get('detail', ''))}</span></li>"
    tools = "".join(f"<li>{e(t)}</li>" for t in site["tools"])
    about = "".join(f"<p>{e(t)}</p>" for t in site["about"])

    statement = f'<p class="hero-statement">{e(site["statement"])}</p>' if site.get("statement") else ""

    body = f"""<section class="hero">
  <div class="slides">{''.join(slides)}</div>
  <div class="hero-text">
    <h1>{e(site['name'])}</h1>
    <p class="hero-role">{e(site['title'])}</p>
    {statement}
  </div>
</section>
<section id="about" class="about">
  <div class="about-body"><h2>About me</h2>{about}{contact(site)}</div>
  <div class="about-side">
    <h3>Experience</h3>
    <ul class="experience">{experience}</ul>
  </div>
</section>
<section class="doors">{doors}</section>
<section class="tool-line"><ul class="tools">{tools}</ul></section>"""
    description = f"{site['name']}, {site['title']}. {site.get('statement', '')}".strip()
    first = by_slug[site["hero"][0]["project"]]
    (ROOT / "index.html").write_text(
        page(data, f"{site['name']} | {site['title']}", description, body, "",
             f"assets/img/{first['slug']}/{site['hero'][0]['image']}"),
        encoding="utf-8",
    )


def environment_page(data):
    site, projects = data["site"], data["projects"]
    base = "../"
    hero = site["hero"][0]
    cards = "".join(card(p, base) for p in projects if not p.get("nav"))
    body = f"""<header class="project-hero">
  <img src="{base}assets/img/{hero['project']}/{hero['image']}" alt="" fetchpriority="high">
  <div class="project-hero-text"><h1>Environments</h1></div>
</header>
<section class="work"><ul class="grid">{cards}</ul></section>"""
    out = ROOT / "environment/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(data, f"Environments | {site['name']}", f"Environment art by {site['name']}", body, base,
                        None, "Environments"), encoding="utf-8")


def background_rows(sheet, count):
    """Reads the backdrop colour of each row from the gaps between the columns of a sheet."""
    width, height = sheet.size
    columns = [min(width // count * i + 3, width - 4) for i in range(count)] + [width - 4]
    rows = []
    for y in range(height):
        samples = sorted(sheet.getpixel((x, y)) for x in columns)
        rows.append(samples[len(samples) // 2])
    return rows


def backdrop(rows, width):
    image = Image.new("RGB", (width, len(rows)))
    draw = ImageDraw.Draw(image)
    for y, colour in enumerate(rows):
        draw.line([(0, y), (width, y)], fill=colour)
    return image


def content_box(cell, rows, top, bottom):
    """Returns the box around whatever differs from the backdrop between two heights."""
    difference = ImageChops.difference(cell, backdrop(rows, cell.width)).convert("L")
    mask = difference.point(lambda value: 255 if value > 28 else 0).filter(ImageFilter.MedianFilter(5))
    box = mask.crop((0, top, cell.width, bottom)).getbbox()
    return box and (box[0], box[1] + top, box[2], box[3] + top)


def corner_text(sheet, rows, from_left):
    """Finds the tight box around the logo or name in a bottom corner, stopping at the gap before the label."""
    top = round(sheet.height * .9)
    limit = round(sheet.width * .103) if from_left else round(sheet.width * .135)
    strip = (0, top, limit, sheet.height) if from_left else (sheet.width - limit, top, sheet.width, sheet.height)
    area = sheet.crop(strip)
    difference = ImageChops.difference(area, backdrop(rows[top:], area.width)).convert("L")
    mask = difference.point(lambda value: 255 if value > 30 else 0)
    pixels = mask.load()
    # Only the block of text at the very bottom counts, not a label sitting above it.
    filled = [y for y in range(mask.height) if any(pixels[x, y] for x in range(mask.width))]
    if not filled:
        return None
    first = filled[-1]
    for y in reversed(filled):
        if first - y > 7:
            break
        first = y
    used = [any(pixels[x, y] for y in range(first, mask.height)) for x in range(mask.width)]
    order = range(mask.width) if from_left else range(mask.width - 1, -1, -1)
    columns, gap = [], 0
    for x in order:
        if used[x]:
            columns.append(x)
            gap = 0
        elif columns:
            gap += 1
            if gap > 16:
                break
    if not columns:
        return None
    left, right = min(columns), max(columns) + 1
    box = mask.crop((left, first, right, mask.height)).getbbox()
    return strip[0] + left, top + first + box[1], strip[0] + right, top + first + box[3]


def label_box(cell, rows, top):
    """Finds the label, which is the lowest block of text once the corners are cleared."""
    area = cell.crop((0, top, cell.width, cell.height))
    difference = ImageChops.difference(area, backdrop(rows[top:], area.width)).convert("L")
    mask = difference.point(lambda value: 255 if value > 40 else 0)
    pixels = mask.load()
    filled = [y for y in range(mask.height) if sum(1 for x in range(mask.width) if pixels[x, y]) > 2]
    if not filled:
        return None
    last = first = filled[-1]
    for y in reversed(filled):
        if first - y > 5:
            break
        first = y
    box = mask.crop((0, first, mask.width, last + 1)).getbbox()
    return box and (box[0], top + first, box[2], top + last + 1)


def compose_parts(source, count):
    """Rebuilds a sheet into single images with centred items, plus a sheet with titles centred under their items."""
    with Image.open(source) as image:
        sheet = image.convert("RGB")
    width, height = sheet.width // count, sheet.height
    rows = background_rows(sheet, count)
    clean = sheet.copy()
    corners = []
    for from_left in (True, False):
        box = corner_text(sheet, rows, from_left)
        if not box:
            continue
        text = sheet.crop(box)
        corners.append((text.resize((round(text.width * .72), round(text.height * .72)), Image.LANCZOS), text, box, from_left))
        clean.paste(backdrop(rows[box[1]:box[3]], text.width), box[:2])

    # A soft edge hides the join between the moved column and the backdrop.
    fade = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(fade)
    for x in range(24):
        draw.line([(x, 0), (x, height)], fill=x * 255 // 24)
        draw.line([(width - 1 - x, 0), (width - 1 - x, height)], fill=x * 255 // 24)

    parts = []
    whole = backdrop(rows, sheet.width)
    for i in range(count):
        cell = clean.crop((i * width, 0, (i + 1) * width, height))
        item = content_box(cell, rows, 0, round(height * .86))
        shift = (width - item[0] - item[2]) // 2 if item else 0
        part = backdrop(rows, width)
        part.paste(cell, (shift, 0), fade)
        whole.paste(cell, (i * width + shift, 0), fade)

        # The label is centred on its own, as it does not always sit under the middle of the item.
        cut = round(height * .865)
        label = label_box(cell, rows, cut)
        if label:
            cut = max(cut, label[1] - 4)
            label_shift = (width - label[0] - label[2]) // 2
            part.paste(backdrop(rows[cut:], width), (0, cut))
            part.paste(cell.crop((0, cut, width, height)), (label_shift, cut), fade.crop((0, cut, width, height)))
            sheet_shift = label_shift
            for _, _, box, from_left in corners:
                if from_left and i == 0:
                    sheet_shift = max(sheet_shift, box[2] + 18 - label[0])
                elif not from_left and i == count - 1:
                    sheet_shift = min(sheet_shift, box[0] - 18 - i * width - label[2])
            whole.paste(backdrop(rows[cut:], width), (i * width, cut))
            whole.paste(cell.crop((0, cut, width, height)), (i * width + sheet_shift, cut), fade.crop((0, cut, width, height)))
        for text, _, box, from_left in corners:
            x = 10 if from_left else width - text.width - 10
            part.paste(text, (x, height - 12 - text.height))
        parts.append(part)
    for _, text, box, _ in corners:
        whole.paste(text, box[:2])
    return parts, whole


def sheet_parts(p, section, img, n, base):
    """Shows a sheet of materials one item at a time on phones."""
    slug, name, count = p["slug"], img["file"], img["split"]
    source = ROOT / "assets/img" / slug / name
    label = section.get("title") or p["title"]
    targets = [source.parent / "thumbs" / f"{source.stem}-part{i + 1}.webp" for i in range(count)]
    sheet = source.parent / "thumbs" / f"{source.stem}-sheet.webp"
    if not sheet.exists() or not all(target.exists() for target in targets):
        targets[0].parent.mkdir(exist_ok=True)
        parts, whole = compose_parts(source, count)
        for target, part in zip(targets, parts):
            part.save(target, "WEBP", quality=88, method=6)
        whole.save(sheet, "WEBP", quality=90, method=6)
    spots, html_parts = "", ""
    for i, target in enumerate(targets):
        width, height = size(slug, f"thumbs/{target.name}")
        src = f"{base}assets/img/{slug}/thumbs/{target.name}"
        html_parts += (f'<figure class="shot"><a href="{src}" data-lightbox><img src="{src}" width="{width}" height="{height}" '
                       f'alt="{e(label)}, image {n}, part {i + 1}" loading="lazy"></a></figure>')
        spots += (f'<a class="sheet-spot" href="{src}" data-lightbox data-alt="{e(label)}, image {n}, part {i + 1}" '
                  f'aria-label="Open item {i + 1} of {count}"></a>')
    width, height = size(slug, f"thumbs/{sheet.name}")
    src = f"{base}assets/img/{slug}/thumbs/{sheet.name}"
    desktop = (f'<figure class="shot"><div class="sheet-image"><img src="{src}" width="{width}" height="{height}" '
               f'alt="{e(label)}, image {n}" loading="lazy">{spots}</div></figure>')
    return f'<div class="sheet-whole">{desktop}</div><div class="sheet-parts">{html_parts}</div>'


def figure(p, section, img, n, base):
    if img.get("split"):
        return sheet_parts(p, section, img, n, base)
    slug, name = p["slug"], img["file"]
    w, h = size(slug, name)
    full = f"{base}assets/img/{slug}/{name}"
    label = section.get("title") or p["title"]
    alt = img.get("caption") or f"{label}, image {n}"
    caption = f"<figcaption>{e(img['caption'])}</figcaption>" if img.get("caption") else ""
    if img.get("compare"):
        top, bottom = img.get("labels", ["", ""])
        other = f"{base}assets/img/{slug}/{img['compare']}"
        return (
            f'<figure class="shot"><div class="img-compare{" compare-fill" if img.get("phone_fill") else ""}" style="aspect-ratio: {w} / {h}">'
            f'<img src="{other}" alt="{e(bottom or alt)}" loading="lazy">'
            f'<div class="compare-top"><img src="{full}" alt="{e(top or alt)}" loading="lazy"></div>'
            f'<input type="range" min="0" max="100" value="60" aria-label="Compare {e(top or "image one")} and {e(bottom or "image two")}">'
            f'<div class="divider"></div></div>{caption}</figure>'
        )
    # Animated gifs lose their motion as thumbnails, so they are served as they are.
    if name.endswith(".gif"):
        attrs = f'src="{full}"'
    else:
        src = f"{base}assets/img/{slug}/thumbs/{thumb(slug, name)}"
        attrs = f'src="{src}" srcset="{src} 960w, {full} {w}w" sizes="(max-width: 1680px) 100vw, 1600px"'
    return (
        f'<figure class="shot{" shot-gif" if name.endswith(".gif") else " shot-small" if w < 1200 or h >= w else ""}"><a href="{full}" data-lightbox>'
        f'<img {attrs} width="{w}" height="{h}" alt="{e(alt)}" loading="lazy"></a>{caption}</figure>'
    )


def section_shots(p, s, base):
    shots = ""
    images = list(enumerate(s["images"], 1))
    while images:
        n, img = images.pop(0)
        if img.get("beside") and images:
            other_n, other = images.pop(0)
            shots += f'<div class="shot-row">{figure(p, s, img, n, base)}{figure(p, s, other, other_n, base)}</div>'
        else:
            shots += figure(p, s, img, n, base)
    return shots


def paged_sections(p):
    """The (slug, section) pairs that get their own page, or nothing if the project is one long page."""
    if not p.get("section_pages"):
        return []
    pages, seen = [], set()
    for i, s in enumerate(p["sections"]):
        if not s["images"]:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", (s.get("title") or "").lower()).strip("-") or f"section-{i + 1}"
        if slug in seen:
            slug = f"{slug}-{i + 1}"
        seen.add(slug)
        pages.append((slug, s))
    return pages if len(pages) > 1 else []


def section_image(p, s):
    name = s.get("thumbnail")
    return name if name and (ROOT / "assets/img" / p["slug"] / name).exists() else s["images"][0]["file"]


def section_cards(p, pages, base):
    cards = ""
    for slug, s in pages:
        name = section_image(p, s)
        src = f"{base}assets/img/{p['slug']}/{name}"
        if size(p["slug"], name)[0] > THUMB_WIDTH and not name.endswith(".gif"):
            src = f"{base}assets/img/{p['slug']}/thumbs/{thumb(p['slug'], name)}"
        title = s.get("title") or p["title"]
        cards += f"""<li class="card">
  <a href="{slug}/index.html">
    <span class="card-image"><img src="{src}" alt="{e(title)}" loading="lazy"></span>
    <span class="card-text"><span class="card-title">{e(title)}</span></span>
  </a>
</li>"""
    return f'<section class="work section-grid"><ul class="grid">{cards}</ul></section>'


def section_page(data, p, pages, i):
    site = data["site"]
    base = "../../../"
    slug, s = pages[i]
    previous, following = pages[i - 1], pages[(i + 1) % len(pages)]
    title = s.get("title") or p["title"]
    name = section_image(p, s)
    label = lambda section: section.get("title") or p["title"]
    text = f'<div class="section-intro"><p>{e(s["text"])}</p></div>' if s.get("text") else ""
    shots = section_shots(p, s, base)
    source = f'<p class="source"><a href="{e(s["source"])}" rel="noopener">View on ArtStation</a></p>' if s.get("source") else ""
    body = f"""<article>
<header class="project-hero">
  <img src="{base}assets/img/{p['slug']}/{name}" alt="" fetchpriority="high">
  <a class="hero-arrow arrow-left" data-section-prev href="../{previous[0]}/index.html" aria-label="Previous: {e(label(previous[1]))}">‹</a>
  <div class="project-hero-text"><a class="crumb" href="../index.html">{e(p['title'])}</a><h1>{e(title)}</h1></div>
  <a class="hero-arrow arrow-right" data-section-next href="../{following[0]}/index.html" aria-label="Next: {e(label(following[1]))}">›</a>
</header>
{text}
<div class="shots">{shots}</div>
{source}
<nav class="section-nav" aria-label="Sections">
  <a href="../{previous[0]}/index.html" aria-label="Previous: {e(label(previous[1]))}"><span>Previous</span><strong>{e(label(previous[1]))}</strong></a>
  <a href="../{following[0]}/index.html" aria-label="Next: {e(label(following[1]))}"><span>Next</span><strong>{e(label(following[1]))}</strong></a>
</nav>
</article>"""
    out = ROOT / "work" / p["slug"] / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        page(data, f"{title} | {p['title']} | {site['name']}", s.get("text") or title, body, base,
             f"{base}assets/img/{p['slug']}/{name}", p["title"] if p.get("nav") else "Environments"),
        encoding="utf-8",
    )


def project_page(data, i):
    site, projects = data["site"], data["projects"]
    p = projects[i]
    base = "../../"

    facts = [("Role", p.get("role")), ("Context", p.get("studio")), ("Tools", ", ".join(p.get("software", [])))]
    fact_html = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in facts if v)

    credits = ""
    for c in p.get("credits", []):
        name = f'<a href="{e(c["url"])}" rel="noopener">{e(c["name"])}</a>' if c.get("url") else e(c["name"])
        role = c.get("role", "")
        # A sentence such as "Based on X by" reads as one line, not role and name columns.
        if role.endswith(" by"):
            credits += f'<li class="credit-line">{e(role)} {name}</li>'
            continue
        credits += (f'<li><span class="credit-role">{e(role)}</span><span class="credit-join">{":" if role else ""}</span>'
                    f'<span class="credit-name">{name}</span></li>')
    credits = f'<div class="credits"><h2>Credits</h2><ul>{credits}</ul></div>' if credits else ""

    links = "".join(f'<a class="cta" href="{e(l["url"])}" rel="noopener">{e(l.get("label") or "Visit")}</a>' for l in p.get("links", []))

    video = ""
    if p.get("video"):
        video = (
            f'<figure class="video"><iframe src="https://www.youtube-nocookie.com/embed/{p["video"]}?rel=0" '
            f'title="{e(p.get("video_title") or p["title"])}" loading="lazy" allowfullscreen '
            f'allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"></iframe></figure>'
        )

    sections = ""
    for s in p["sections"]:
        head = ""
        if s.get("title"):
            text = f"<p>{e(s['text'])}</p>" if s.get("text") else ""
            head = f'<div class="section-intro"><h2>{e(s["title"])}</h2>{text}</div>'
        shots = section_shots(p, s, base)
        sections += f"<section>{head}<div class=\"shots\">{shots}</div></section>"

    pages = paged_sections(p)
    if pages:
        sections = section_cards(p, pages, base)

    sources = list({s["source"]: s for s in p["sections"] if s.get("source")}.values())
    if len(sources) == 1:
        source = f'<a href="{e(sources[0]["source"])}" rel="noopener">View on ArtStation</a>'
    elif sources:
        source = "View on ArtStation: " + ", ".join(
            f'<a href="{e(s["source"])}" rel="noopener">{e(s.get("title") or p["title"])}</a>' for s in sources
        )
    else:
        source = ""

    prv = projects[i - 1]
    nxt = projects[(i + 1) % len(projects)]
    w, _ = size(p["slug"], p["cover"])
    summary = "".join(f"<p>{e(t)}</p>" for t in p["summary"])
    for link in p.get("detail_links", []):
        fact_html += (f'<div><dt>{e(link.get("label", "Link"))}</dt><dd><a href="{e(link["url"])}" rel="noopener">'
                      f'{e(link.get("text") or link["url"])}</a></dd></div>')
    facts_list = f'<dl class="facts">{fact_html}</dl>' if fact_html else ""
    aside = f"<div>{facts_list}{credits}</div>" if facts_list or credits else ""

    heading = f"<h1>{e(p['title'])}</h1>"

    # A cover too small to fill the screen would look soft, so the page opens on the text.
    hero = ""
    if w >= 1200:
        hero = f"""<header class="project-hero">
  <img src="{base}assets/img/{p['slug']}/{p['cover']}" alt="" fetchpriority="high">
  <div class="project-hero-text">{heading}</div>
</header>"""

    words = f'<div class="summary">{summary}{links}</div>' if summary or links else ""
    left = words if hero else heading + words
    # The video fills the column beside the facts, with the text running full width below.
    wide = ""
    if video and aside:
        left = video if hero else heading + video
        wide = words.replace('class="summary"', 'class="summary summary-wide"', 1)
        video = ""
    intro = ""
    if left or aside:
        classes = f"project-intro{'' if hero else ' no-hero'}{'' if aside else ' solo'}"
        intro = f'<div class="{classes}"><div>{left}</div>{aside}{wide}</div>'

    body = f"""<article>
{hero}
{intro}
{video}
{sections}
<p class="source">{source}</p>
<nav class="section-nav" aria-label="Projects">
  <a href="{base}work/{prv['slug']}/index.html" aria-label="Previous project: {e(prv['title'])}"><span>Previous</span><strong>{e(prv['title'])}</strong></a>
  <a href="{base}work/{nxt['slug']}/index.html" aria-label="Next project: {e(nxt['title'])}"><span>Next</span><strong>{e(nxt['title'])}</strong></a>
</nav>
</article>"""

    for number in range(len(pages)):
        section_page(data, p, pages, number)

    out = ROOT / "work" / p["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        page(data, f"{p['title']} | {site['name']}", p.get("tagline") or p["title"], body, base,
             f"{base}assets/img/{p['slug']}/{p['cover']}", p["title"] if p.get("nav") else "Environments"),
        encoding="utf-8",
    )


def main():
    data = json.loads((ROOT / "content/projects.json").read_text(encoding="utf-8"))
    shutil.rmtree(ROOT / "work", ignore_errors=True)
    shutil.rmtree(ROOT / "environment", ignore_errors=True)
    index(data)
    environment_page(data)
    for i in range(len(data["projects"])):
        project_page(data, i)
    print(f"Built index.html and {len(data['projects'])} project pages")


if __name__ == "__main__":
    main()
