"""Build the hosted version of the Imperial Jalyuzi site.

docs/index.html     — Uzbek page, text pre-rendered into the HTML (readable without JS)
docs/ru/index.html  — Russian page, same
docs/img/…          — only the images the pages use
docs/favicon.png, apple-touch-icon.png, robots.txt, sitemap.xml, .nojekyll

Usage (from the repo root):  python3 src/build_site.py [https://your-domain.uz]
Default domain: https://shamsiddinyusupov.github.io/imperial
"""
import json
import os
import re
import shutil
import sys
import zipfile

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # repository root
SRC = os.path.join(ROOT, "src", "imperial-sayt.html")                 # editable source (same file as the claude.ai preview)
IMG = os.path.join(ROOT, "src", "img")                                # all images the source uses
DIST = os.path.join(ROOT, "docs")                                     # GitHub Pages publishes main:/docs
ZIP = os.environ.get("SITE_ZIP", "")                                   # optional: path for a zip of docs/
DOMAIN = (sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://shamsiddinyusupov.github.io/imperial")

META = {
    "uz": dict(
        html_lang="uz-Latn", og_locale="uz_UZ",
        title="Imperial Jalyuzi — jalyuzi va moskit setkalar Toshkentda | Plisse 100 000 so‘mdan",
        desc="Imperial Jalyuzi — plisse, kombo (kun-tun), rollo, dikey, gorizontal va vertikal jalyuzi hamda moskit setkalar. "
             "Toshkent shahri va viloyati. Toshkentda o‘lchov, yetkazish va o‘rnatish bepul. Plisse 1 m² — 100 000 so‘mdan.",
    ),
    "ru": dict(
        html_lang="ru", og_locale="ru_RU",
        title="Imperial Jalyuzi — жалюзи и москитные сетки в Ташкенте | Плиссе от 100 000 сум",
        desc="Imperial Jalyuzi — плиссе, зебра «день-ночь», рулонные, дикей, горизонтальные и вертикальные жалюзи и москитные сетки. "
             "Ташкент и Ташкентская область. По Ташкенту замер, доставка и установка бесплатно. Плиссе от 100 000 сум за м².",
    ),
}


def split_source():
    src = open(SRC, encoding="utf-8").read()
    i = src.index("<style>")
    prefix, rest = src[:i], src[i:]
    fonts = "\n".join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', prefix))
    biz = json.loads(re.search(r'<script type="application/ld\+json">(\{[^<]*HomeAndConstructionBusiness[^<]*\})</script>', prefix).group(1))
    return rest, fonts, biz


def render(rest, lang):
    page_html = ("<!doctype html><html><head><meta charset='utf-8'>"
                 "<meta name='viewport' content='width=device-width,initial-scale=1'></head><body>" + rest + "</body></html>")
    tmp = os.path.join(os.path.dirname(SRC), f"_build_{lang}.html")
    open(tmp, "w", encoding="utf-8").write(page_html)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.add_init_script(f"window.IMPERIAL_LANG = {json.dumps(lang)};")
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + tmp)
        pg.wait_for_timeout(700)
        body = pg.evaluate("document.body.innerHTML")
        faq = pg.evaluate("""[...document.querySelectorAll('#savollar details')].map(d => [d.querySelector('summary').textContent, d.querySelector('p').textContent])""")
        b.close()
    os.remove(tmp)
    if errs:
        raise SystemExit(f"page errors ({lang}): {errs}")
    return body, faq


def head(lang, fonts, biz, faq, prefix_path):
    m = META[lang]
    links = {"uz": "./", "ru": "ru/"} if lang == "uz" else {"uz": "../", "ru": "./"}
    biz = dict(biz, description=m["desc"])
    if DOMAIN:
        biz["url"] = DOMAIN + ("/" if lang == "uz" else "/ru/")
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    canon = ""
    if DOMAIN:
        here = DOMAIN + ("/" if lang == "uz" else "/ru/")
        canon = (f'<link rel="canonical" href="{here}">\n'
                 f'<link rel="alternate" hreflang="uz" href="{DOMAIN}/">\n'
                 f'<link rel="alternate" hreflang="ru" href="{DOMAIN}/ru/">\n'
                 f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}/">\n'
                 f'<meta property="og:url" content="{here}">\n'
                 f'<meta property="og:image" content="{DOMAIN}/img/c_plisse.jpg">\n')
    esc = lambda t: t.replace("&", "&amp;").replace('"', "&quot;")
    return f"""<!doctype html>
<html lang="{m['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="google-site-verification" content="8vWDjGmRq9Fx1DPi-ihoXKtanp9MGnJ2DnvILczSgY4">
<title>{esc(m['title'])}</title>
<meta name="description" content="{esc(m['desc'])}">
{canon}<meta property="og:type" content="website">
<meta property="og:site_name" content="Imperial Jalyuzi">
<meta property="og:title" content="{esc(m['title'])}">
<meta property="og:description" content="{esc(m['desc'])}">
<meta property="og:locale" content="{m['og_locale']}">
<meta name="theme-color" content="#F1F1EE">
<link rel="icon" type="image/png" sizes="32x32" href="{prefix_path}favicon.png">
<link rel="apple-touch-icon" href="{prefix_path}apple-touch-icon.png">
{fonts}
<style>html, body {{ margin: 0; }} [hidden] {{ display: none !important; }}</style>
<script type="application/ld+json">{json.dumps(biz, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
<script>window.IMPERIAL_LANG = "{lang}"; window.IMPERIAL_LINKS = {json.dumps(links)};</script>
</head>
<body>
"""


def icons():
    lg = Image.open(f"{IMG}/logo.png").convert("RGBA")
    h = lg.height
    emb = lg.crop((0, 0, h, h))                    # round emblem on the left of the logo
    bb = emb.getbbox()
    emb = emb.crop(bb)
    side = max(emb.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(emb, ((side - emb.width) // 2, (side - emb.height) // 2), emb)
    sq.resize((64, 64), Image.LANCZOS).save(f"{DIST}/favicon.png")
    bg = Image.new("RGBA", (180, 180), (241, 241, 238, 255))
    ic = sq.resize((140, 140), Image.LANCZOS)
    bg.alpha_composite(ic, (20, 20))
    bg.convert("RGB").save(f"{DIST}/apple-touch-icon.png")


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(f"{DIST}/ru")
    os.makedirs(f"{DIST}/img")
    rest, fonts, biz = split_source()
    used = set()
    for lang in ("uz", "ru"):
        body, faq = render(rest, lang)
        used |= set(re.findall(r'img/([\w.\-]+\.(?:jpg|png|mp4))', body))
        prefix = "" if lang == "uz" else "../"
        if lang == "ru":
            body = body.replace('src="img/', 'src="../img/').replace('poster="img/', 'poster="../img/').replace('"img/', '"../img/')
        html = head(lang, fonts, biz, faq, prefix) + body + "\n</body>\n</html>\n"
        out = f"{DIST}/index.html" if lang == "uz" else f"{DIST}/ru/index.html"
        open(out, "w", encoding="utf-8").write(html)
        print(lang, "->", out, len(html) // 1024, "KB")
    for f in sorted(used):
        shutil.copy2(f"{IMG}/{f}", f"{DIST}/img/{f}")
    icons()
    robots = "User-agent: *\nAllow: /\n"
    if DOMAIN:
        robots += f"\nSitemap: {DOMAIN}/sitemap.xml\n"
        sm = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url><loc>{DOMAIN}/</loc>
    <xhtml:link rel="alternate" hreflang="uz" href="{DOMAIN}/"/><xhtml:link rel="alternate" hreflang="ru" href="{DOMAIN}/ru/"/></url>
  <url><loc>{DOMAIN}/ru/</loc>
    <xhtml:link rel="alternate" hreflang="uz" href="{DOMAIN}/"/><xhtml:link rel="alternate" hreflang="ru" href="{DOMAIN}/ru/"/></url>
</urlset>
"""
        open(f"{DIST}/sitemap.xml", "w").write(sm)
    open(f"{DIST}/robots.txt", "w").write(robots)
    open(f"{DIST}/.nojekyll", "w").close()
    if not ZIP:
        print("images", len(used), "| domain:", DOMAIN or "(none yet)")
        return
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(DIST):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, DIST))
    print("images", len(used), "| zip", os.path.getsize(ZIP) // 1024, "KB", "| domain:", DOMAIN or "(none yet)")


if __name__ == "__main__":
    main()
