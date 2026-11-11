"""Cut Daniel's lines out of the owner's screen recordings and re-space them.
dikey: rec.wav (ScreenRecording 19-56-55), plisse: rec2.wav (19-57-48). Times are recording seconds,
from silencedetect (-38 dB, 0.25 s); each paragraph = list of voiced chunks.
build(name) -> (wav path, [(para_start, para_len), ...]) with paragraphs packed back to back (gap 0 between
paragraphs; the caller places them on the timeline with place()).
"""
import wave

import numpy as np

D = "/home/claude/reels/n11/vo"
SR = 48000
PARAS = {
    "dk": ("rec.wav", [
        [(5.29, 6.00), (6.54, 7.15), (7.72, 8.60)],          # Оқ тюль... четида — тўқ бархат.
        [(9.19, 10.19), (10.59, 12.09)],                     # Иккиси бирга — чиройли комбинация.
        [(13.37, 14.69), (14.96, 16.64)],                    # Оқ тюль хонага майин ёруғлик беради.
        [(17.29, 18.50), (19.07, 19.80)],                    # Очиқ ҳам чиройли... ёпиқ ҳам.
        [(20.25, 23.43), (24.24, 25.36), (25.73, 26.83)],    # Деразангизга ҳам ... керакми? Дераза расмини директга юборинг.
    ], 0.42),
    "pq": ("rec2.wav", [
        [(1.33, 2.66), (3.09, 3.52), (4.11, 4.65), (5.13, 5.95)],   # Қайси ранг сизга ёқди? Бир, икки ёки уч?
        [(6.83, 7.30), (7.62, 8.11), (8.92, 11.36)],                # Бир — крем. Хона илиқ ва ёруғ кўринади.
        [(12.18, 12.69), (13.16, 13.94), (14.57, 16.72)],           # Икки — капучино. Ёғоч ром билан жуда мос.
        [(17.73, 18.22), (18.84, 19.77), (20.48, 21.86)],           # Уч — оқ-кулранг. Тоза ва замонавий.
        [(22.97, 24.50), (24.97, 26.71)],                           # Рангини сиз танлайсиз — қолганини ўзимиз қиламиз.
        [(27.42, 29.93), (30.30, 30.96), (31.26, 33.51)],           # Ёққанининг рақамини изоҳга ёзинг! Ёки дераза ... юборинг.
    ], 0.30),
}
PRE, POST = 0.07, 0.12


def load(f):
    w = wave.open(f"{D}/{f}")
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767


def para_audio(a, chunks, cap):
    """one paragraph: chunks with the gaps between them capped at `cap` seconds (natural gap if shorter)."""
    out = []
    for k, (s, e) in enumerate(chunks):
        seg = a[int((s - PRE) * SR):int((e + POST) * SR)].copy()
        f = int(0.01 * SR)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        out.append(seg)
        if k + 1 < len(chunks):
            gap = min(cap, chunks[k + 1][0] - e) - PRE - POST
            if gap > 0:
                out.append(np.zeros(int(gap * SR), np.float32))
            else:                                   # overlap the padding a little instead of a hard butt-join
                out[-1] = out[-1][: len(out[-1]) + int(gap * SR)] if gap < 0 else out[-1]
    return np.concatenate(out)


def paragraphs(name):
    f, paras, cap = PARAS[name]
    a = load(f)
    return [para_audio(a, ch, cap) for ch in paras]


def place(name, starts, total, path):
    """write a mono 48 kHz wav with paragraph i starting at starts[i] (seconds)."""
    ps = paragraphs(name)
    buf = np.zeros(int((total + 1) * SR), np.float32)
    for p, t in zip(ps, starts):
        i = int(t * SR)
        buf[i:i + len(p)] += p[: len(buf) - i]
    buf = buf[: int(total * SR)]
    w = wave.open(path, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())
    w.close()


def lengths(name):
    return [len(p) / SR for p in paragraphs(name)]


if __name__ == "__main__":
    for n in PARAS:
        print(n, [round(x, 2) for x in lengths(n)], round(sum(lengths(n)), 2))
