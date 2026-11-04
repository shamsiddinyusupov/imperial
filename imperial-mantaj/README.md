# imperial mantaj — Imperial Jalyuzi Reels montaj to‘plami

Egasi «**imperial mantaj**» desa — shu uslub va shu dasturlar bilan ishlanadi (4.11.2026 dan).
Uslub qoidalari: `imperial-reels` skili va Project hujjati `claude/kontent-reja.md` («Uslub»).

Bu yerda faqat kod va vaqt jadvallari bor. Kliplar, rasmlar, ovoz va tayyor videolar saqlanmaydi
(egasi kliplarni chatga qayta yuboradi). Sayt bu papkani ko‘rsatmaydi: GitHub Pages faqat `docs/` dan ishlaydi.

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
| `common/` | `compact.py` — ixcham matn yordamchilari va `calm_bed` (fortepiano/elektropiano fon); `nylon_bed.py` — nylon gitara + torli fon (Fa); `bloom_bed.py` — ochiladigan torli fon + selesta (Mi-bemol) |
| `dikey_style/` | Hozirgi uslubning asosi: `grade.py` (oq rang + «Iliq krem»), `stab.py` (OpenCV barqarorlashtirish, rasmlarga sekin harakat), `faqat_qarang.py` (Didone/kursiv matn qatlamlari, 2 animatsiya), `style_test.py` (kadrdan palitra), `mix.sh` |
| `stereo/` | «Jalyuzi deganda…»: ovozli video, so‘zda kesish (`vo_sync.py`, `timing.json`), 4:3 ramka ochilishi, `stab.py`, `mix.sh` |
| `incoming/` | Chuqurlik effekti (`demo_depth.py`) va sarlavha qoliplari A/B/C (`layouts.py`) |
| `kombo4/`, `kombo_v3/` | Kombo variantlari (kulrang mato uchun neytral rang) |
| `ads/` | Reklama versiyalari (izoh chaqirig‘i o‘chiriladi, «Pastdagi tugmani bosing») |
| `faq/`, `tong*/`, `mato/`, `pl2/`, `rim/`, `setka/`, `narx/`, `ba/`, `scripts/` | Oldingi Reels va postlar (eski uslub — faqat namuna uchun) |

Har yangi video: oldin ishlatilmagan kliplar va oldin ishlatilmagan musiqa.
