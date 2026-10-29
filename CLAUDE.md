# Imperial Jalyuzi — website repo

The owner (media manager of Imperial Jalyuzi, Tashkent blinds company) writes in Uzbek; reply in Uzbek unless they write in another language.
When they say **"imperial website"**, this repo is the site. Full business facts, Google/Maps texts and open items live in the claude.ai Project doc `claude/imperial-website.md`.

## Live
- Uzbek: https://shamsiddinyusupov.github.io/imperial/
- Russian: https://shamsiddinyusupov.github.io/imperial/ru/
- GitHub Pages source: branch `main`, folder `/docs` (set in repo Settings → Pages).
- Preview artifact (same source file): https://claude.ai/artifact/STsMarGjKbz8DxVsEh4Ci1

## Layout
- `src/imperial-sayt.html` — the only file to edit. One page: hero collage, catalog, plisse catalog, mosquito nets, calculator, works, steps, FAQ, contacts. All text lives in the `T` dictionary (`uz` and `ru`) inside the script; elements use `data-i`, `data-i-alt`, `data-i-aria` keys.
- `src/img/` — every image the source uses.
- `src/build_site.py` — renders both languages with Playwright and writes `docs/` (pre-rendered text for SEO, head meta, canonical/hreflang, JSON-LD, favicon, robots.txt, sitemap.xml, .nojekyll).
- `docs/` — generated output. Never edit by hand.

## Change → publish
1. Edit `src/imperial-sayt.html` (and add images to `src/img/`).
2. `python3 src/build_site.py` (needs Pillow + Playwright/Chromium; Google Fonts may be blocked in the sandbox — harmless).
3. Check pages locally (`python3 -m http.server` in `docs/`), then commit and push `main`. GitHub Pages redeploys in 1–2 min; check with `gh api repos/shamsiddinyusupov/imperial/actions/runs?per_page=1`.
4. Republish the preview artifact from the same source if the owner uses it.

## Rules that must hold
- Keep `<meta name="google-site-verification" content="8vWDjGmRq9Fx1DPi-ihoXKtanp9MGnJ2DnvILczSgY4">` in the build head (Search Console verification for /imperial/ and /imperial/ru/).
- Prices are Imperial's own (owner, 28.10.2026). Plisse is priced per sash of a standard home window (= per m², billed at least 1 m²) by fabric: Screen 100 000, Lezbon 130 000, Roma 170 000, Blackout 200 000; default fabric Lezbon. All other types per m²: kombo 110 000–230 000, rollo 140 000–240 000, dikey 240 000–340 000, vertikal 100 000, gorizontal 160 000, rimskiy shtora 250 000 (owner, 29.10.2026; its lead time is not 3 days — exact term pending). `PRICES[type] = null` means "Narxi so‘rov bo‘yicha" (use only for types without an owner price, e.g. mosquito nets). Never show competitor prices as theirs.
- Plisse only: each blind is billed at least 1 m² (`MIN_AREA`).
- Warranty: 1 year from Imperial on all products (owner, 28.10.2026).
- Payment: any method — Click, Payme, card transfer, cash (owner, 28.10.2026).
- Free measuring/delivery/installation only in Tashkent city; Tashkent region → calculator, then the customer writes personally via Telegram or Instagram Direct (owner, 28.10.2026). Ready 3 days after measuring.
- Contacts (owner, 28.10.2026: the only working number; Telegram is on the same number): Telegram https://t.me/jalyuzi_imperial, phone +998 33 751 11 88, Instagram @imperial_jalyuzi_uz, hours Mon–Sat 9:30–20:00, Sun 10:00–18:00. Exact address not given yet (service-area business).
- Do not use watermarked or third-party marketing photos without the owner confirming rights; prefer their own installation photos. Catalog/hero images are uniform 4:5 (800×1000, `c_*.jpg`); mosquito-net images are 600×1000 (`st_*.jpg`).
