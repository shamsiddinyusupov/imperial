# imperial mantaj — Imperial Jalyuzi Reels montaj to‘plami

Egasi «**imperial mantaj**» desa — shu uslub va shu dasturlar bilan ishlanadi (4.11.2026 dan).
Uslub qoidalari: `imperial-reels` skili va Project hujjati `claude/kontent-reja.md` («Uslub»).

Bu yerda faqat kod va vaqt jadvallari bor. Kliplar, rasmlar, ovoz va tayyor videolar saqlanmaydi
(egasi kliplarni chatga qayta yuboradi). Sayt bu papkani ko‘rsatmaydi: GitHub Pages faqat `docs/` dan ishlaydi.

## Baza — egasining kompyuteri
`C:\Users\shams\Videos\Imperial` (chat kompyuterga ulangan bo‘lsa, papkaga ruxsat so‘raladi):
`01_Kliplar` (RAW, `sana_mahsulot` papkalari) · `02_Rasmlar` · `03_Ovoz` · `04_Musiqa` (ishlatilganlar) ·
`05_Tayyor_Reels` (video + muqova + izoh) · `06_Reklama` · `07_Resolve` · `08_Referens`.
Yangi kliplar shu yerdan olinadi, tayyor video shu yerga yoziladi (25 MB dan katta fayl — avval SendUserFile, keyin fileUuid bilan).
DaVinci Resolve: bepul 21.0.3 (21.1+ ga yangilanmasin), ko‘prik — Workspace → Scripts → resolve_bridge.

## Tiklash (yangi sessiyada)

Skriptlardagi yo‘llar `/home/claude/reels/...` ga yozilgan, shuning uchun o‘sha joyga ko‘chiriladi:

```bash
[ -d /home/claude/imperial/.git ] && git -C /home/claude/imperial pull -q \
  || git clone -q https://github.com/shamsiddinyusupov/imperial /home/claude/imperial
mkdir -p /home/claude/reels && cp -rn /home/claude/imperial/imperial-mantaj/. /home/claude/reels/
```

Kerak: python3 + numpy, scipy, opencv (cv2), Pillow; ffmpeg (`zscale` bilan). Shriftlar tizimda:
Latin Modern Roman 17, TeX Gyre Pagella Italic, Inter Display, Lora Italic.

## Nima qayerda

| Papka | Nima |
| --- | --- |
| `common/` | `compact.py` — ixcham matn yordamchilari va `calm_bed` (fortepiano/elektropiano fon); `nylon_bed.py` — nylon gitara + torli fon (Fa); `bloom_bed.py` — ochiladigan torli fon + selesta (Mi-bemol); `vibe_bed.py` — vibrafon + violonchel (La major, 70 BPM) |
| `dikey_style/` | Hozirgi uslubning asosi: `grade.py` (oq rang + «Iliq krem»), `stab.py` (OpenCV barqarorlashtirish, rasmlarga sekin harakat), `faqat_qarang.py` (Didone/kursiv matn qatlamlari, 2 animatsiya), `style_test.py` (kadrdan palitra), `mix.sh` |
| `stereo/` | «Jalyuzi deganda…»: ovozli video, so‘zda kesish (`vo_sync.py`, `timing.json`), 4:3 ramka ochilishi, `stab.py`, `mix.sh` |
| `ikki_xona/` | «Ikki xona» (4.11.2026): ikki xona — kombo neytral rang, plisse iliq krem; bo‘lingan ekran ilmog‘i; qatlamlar alohida (V1 sahnalar 0,5 s zaxira bilan, V2 matn ProRes 4444 alfa, A1 musiqa) va `resolve_build.py` — DaVinci Resolve konsolida (Py3) timeline yig‘adi |
| `incoming/` | Chuqurlik effekti (`demo_depth.py`) va sarlavha qoliplari A/B/C (`layouts.py`) |
| `kombo4/`, `kombo_v3/` | Kombo variantlari (kulrang mato uchun neytral rang) |
| `ads/` | Reklama versiyalari (izoh chaqirig‘i o‘chiriladi, «Pastdagi tugmani bosing») |
| `faq/`, `tong*/`, `mato/`, `pl2/`, `rim/`, `setka/`, `narx/`, `ba/`, `scripts/` | Oldingi Reels va postlar (eski uslub — faqat namuna uchun) |

Har yangi video: oldin ishlatilmagan kliplar va oldin ishlatilmagan musiqa.
