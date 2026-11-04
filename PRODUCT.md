# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary: homeowners in Tashkent** who are choosing blinds for their windows — typically after a renovation or when moving into a new home — and first want to know what it will cost (owner, 4.11.2026).
- **Visitors from Instagram Reels and Meta ads** (@imperial_jalyuzi_uz): they reach the site from the bio link page (`/link/`) or an ad, to check prices and the catalog before writing (owner, 4.11.2026). Most of this traffic arrives on phones (inferred from the source; not measured).
- Language: Uzbek (Latin) first, Russian second; both are full versions of the site.
- Not confirmed as audiences: offices/businesses, designers, builders — do not design for them unless the owner adds them.

## Product Purpose

The website of **Imperial Jalyuzi**, a blinds and mosquito-net company in Tashkent. It shows the product range with real prices, lets the visitor calculate a price for their own window, and moves them to contact the company.

**Success = the visitor writes to Telegram** (https://t.me/jalyuzi_imperial) to book a free measurement or ask a question (owner, 4.11.2026). Calling (+998 33 751 11 88) and Instagram Direct are secondary routes.

## Positioning

What the owner confirmed sets Imperial apart (4.11.2026):

1. **Open prices + calculator** — the price is on the site and the visitor can calculate it; many competitors hide prices.
2. **Free measuring, delivery and installation in Tashkent city; ready 3 days after measuring; 1-year warranty** on all products.
3. **Renewing old blinds** — replacing worn plisse and kombo fabric in a colour/style the customer chooses (paid as fabric + labour), or removing, washing and reinstalling them (paid). Competitors do not show this service.
4. **Fabric choice and quality** — 800+ fabrics from Turkey and China.

## Operating Context

- Service area: Tashkent city (measuring/delivery/installation free) and Tashkent region (the visitor uses the calculator, then writes personally via Telegram or Instagram Direct; the visit day is agreed by number of windows).
- Hours: Mon–Sat 9:30–20:00, Sun 10:00–18:00. Payment: Click, Payme, card transfer or cash.
- The single working phone is +998 33 751 11 88; Telegram is on the same number. Older numbers in old Instagram posts are not used.
- Instagram drives traffic: Reels, Meta ads, the bio link page (`src/link.html` → `/link/`), and a ChatPlace comment bot that replies to «NARX» (prices) and «YANGILASH» (renewal) in comments. The owner answers Direct messages personally.
- Hosting: GitHub Pages from `main:/docs`; Google Search Console verified (the verification meta in `src/build_site.py` must stay).
- No showroom or exact address published yet (service-area business).

## Capabilities and Constraints

- One editable source page `src/imperial-sayt.html` (all copy in the `T` dictionary, `uz` and `ru`), built by `src/build_site.py` into pre-rendered static pages for SEO. Sections today: hero, catalog, plisse catalog, mosquito nets, calculator, works, steps, FAQ, contacts.
- Products and pricing rules (owner, 28–29.10.2026):
  - Plisse — priced per sash of a standard home window by fabric: Screen 100 000, Lezbon 130 000 (calculator default), Roma 170 000, Blackout 200 000 so‘m; every blind billed at least 1 m².
  - Per m²: kombo (kun-tun) 110 000–230 000, rollo 140 000–240 000, dikey 240 000–340 000, vertikal 100 000, gorizontal (alyumin) 160 000, rimskiy shtora 250 000 so‘m.
  - Mosquito nets (standard, petlyali, Uni, surma; mesh anti-dust / anti-smog / anti-cat): **no prices yet** — shown as «Narxi so‘rov bo‘yicha».
- Open, not yet confirmed: rimskiy shtora lead time (not 3 days); mosquito-net prices; renewal and washing prices and lead time; prepayment; exact address.
- Content rules: only confirmed facts; never show competitor prices as Imperial’s; no mechanism or size details (explained in conversation); the workshop/production place is never shown; no watermarked or third-party marketing photos without the owner confirming rights.

## Brand Commitments

- Name: **Imperial Jalyuzi**. Logo: `src/img/logo.png` (confirmed main logo, 28.10.2026).
- Voice: premium and tasteful, calm and confident — not youthful, not cartoonish, no hype; Uzbek Latin first with a short Russian line.
- Claims stay factual: «bepul» only for Tashkent city; renewal is never called «arzon» or «mato narxida».

## Evidence on Hand

- Imperial’s own installation photos and videos (catalog/hero images `src/img/c_*.jpg`, works section, Reels footage).
- 5+ years of experience (owner, 28.10.2026).
- Customer reviews exist in the Instagram «Otzivi» highlight; screenshots have not been supplied — do not write or invent testimonials, customer names, counts or ratings.
- Mosquito-net card drawings are from the JALOUSIE brand (owner chose to keep them, 29.10.2026); each card also shows Imperial’s own installed photo.

## Product Principles

1. **Price first, honestly.** The visitor should see a real number fast and be able to calculate their own window; never hide or inflate.
2. **Every path ends in Telegram.** Each section should make writing for a free measurement the obvious next step.
3. **Only confirmed facts.** If the owner has not confirmed it (price, term, address, review), it does not appear.
4. **Own work is the proof.** Real Imperial installations over stock or brand imagery.
5. **Uzbek and Russian are equal.** Every change lands in both `T.uz` and `T.ru`.
