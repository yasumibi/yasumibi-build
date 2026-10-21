import numpy as np
from scipy.io import wavfile
import sys

SR = 48000
DUR = 60.0
N = int(SR * DUR)
out = np.zeros(N)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.002, d=0.2):
    x = np.arange(n) / SR
    e = np.exp(-x / d)
    att = np.clip(x / a, 0, 1)
    return e * att


rng = np.random.default_rng(7)


def place(sig, at, gain=1.0):
    i = int(at * SR)
    j = min(N, i + len(sig))
    out[i:j] += sig[: j - i] * gain


def impact(big=False):
    d = 0.9 if big else 0.6
    x = t(d)
    f = 120 * np.exp(-x * 8) + 45
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env(len(x), 0.001, 0.25 if big else 0.18)
    noise = rng.standard_normal(len(x)) * env(len(x), 0.001, 0.04)
    return (body * 0.9 + noise * 0.35) * (1.0 if big else 0.8)


def bonk():
    x = t(0.25)
    f = 700 * np.exp(-x * 18) + 160
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sign(np.sin(ph)) * env(len(x), 0.001, 0.07) * 0.35 + np.sin(ph) * env(len(x), 0.001, 0.1) * 0.4


def pop():
    x = t(0.15)
    f = 400 + 1400 * x / 0.15
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(len(x), 0.001, 0.04) * 0.5


def ding(freq=1568):
    x = t(0.9)
    s = np.sin(2 * np.pi * freq * x) + 0.4 * np.sin(2 * np.pi * freq * 2.76 * x)
    return s * env(len(x), 0.001, 0.25) * 0.3


def chime():
    return ding(2093) + np.concatenate([np.zeros(int(0.09 * SR)), ding(2637)])[: int(0.9 * SR)]


def tick():
    x = t(0.03)
    return rng.standard_normal(len(x)) * env(len(x), 0.0005, 0.006) * 0.35


def ticks(start, end, rate=22):
    k = start
    while k < end:
        place(tick(), k)
        k += 1.0 / rate


def drumroll(start, end):
    k = start
    i = 0
    while k < end:
        g = 0.15 + 0.35 * (k - start) / (end - start)
        x = t(0.05)
        place(rng.standard_normal(len(x)) * env(len(x), 0.0005, 0.02) * g, k)
        k += 0.035
        i += 1


def gong():
    x = t(2.5)
    s = sum(np.sin(2 * np.pi * f * x) * a for f, a in [(110, 1), (163, 0.6), (221, 0.5), (297, 0.3), (412, 0.2)])
    return s * env(len(x), 0.003, 0.9) * 0.28


def whoosh():
    x = t(0.45)
    n = rng.standard_normal(len(x))
    # simple moving-average lowpass with rising cutoff feel
    k = 12
    n = np.convolve(n, np.ones(k) / k, mode="same")
    e = np.sin(np.pi * x / 0.45) ** 2
    return n * e * 0.5


def buzzer():
    x = t(0.5)
    s = np.sign(np.sin(2 * np.pi * 110 * x)) * 0.15 + np.sign(np.sin(2 * np.pi * 116 * x)) * 0.15
    return s * np.clip(1 - x / 0.5, 0, 1)


def kick():
    x = t(0.3)
    f = 150 * np.exp(-x * 30) + 48
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(len(x), 0.001, 0.12)


def hat():
    x = t(0.05)
    n = rng.standard_normal(len(x))
    n = n - np.convolve(n, np.ones(4) / 4, mode="same")
    return n * env(len(x), 0.0005, 0.012)


def clap():
    x = t(0.18)
    n = rng.standard_normal(len(x))
    e = env(len(x), 0.001, 0.05)
    return n * e * 0.6


# ---- BGM bed: 120 BPM ----
bgm = np.zeros(N)


def bplace(sig, at, gain):
    i = int(at * SR)
    j = min(N, i + len(sig))
    bgm[i:j] += sig[: j - i] * gain


beat = 0.5
b = 0.0
idx = 0
while b < DUR - 0.5:
    muted = 13.0 <= b < 14.7 or 27.0 <= b < 30.5
    if not muted:
        bplace(kick(), b, 0.55)
        bplace(hat(), b + beat / 2, 0.18)
        if idx % 2 == 1:
            bplace(clap(), b, 0.22)
    b += beat
    idx += 1

# bass line on root notes (simple, loops every 4 beats)
notes = [55.0, 55.0, 65.41, 49.0]
b = 0.0
idx = 0
while b < DUR - 0.5:
    muted = 13.0 <= b < 14.7 or 27.0 <= b < 30.5
    if not muted:
        f = notes[(idx // 2) % 4]
        x = t(0.42)
        s = np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * f * 2 * x)
        bplace(s * env(len(x), 0.005, 0.25), b, 0.25)
    b += beat
    idx += 1

# ---- SFX timeline (seconds) ----
place(impact(), 0.05)
place(impact(True), 0.9, 1.0)
place(pop(), 2.0)
place(tick(), 3.2)
place(bonk(), 5.0)
place(pop(), 7.6)
for s in (8.0, 9.6, 11.2):
    place(ding(), s)
drumroll(13.0, 14.6)
place(impact(True), 14.7, 0.8)
place(ding(1760), 14.72)
place(whoosh(), 15.6)
ticks(16.3, 21.6)
place(buzzer(), 19.4, 0.8)
place(bonk(), 22.5)
place(whoosh(), 24.6)
ticks(27.0, 29.0, 30)
place(gong(), 29.2)
place(impact(True), 30.0, 0.9)
place(whoosh(), 33.2)
for s in (34.6, 36.8, 39.0):
    place(pop(), s)
place(impact(), 41.2)
place(whoosh(), 42.6)
ticks(44.0, 45.6, 30)
place(chime(), 45.7)
place(ding(1975), 47.0)
place(whoosh(), 49.2)
for i, s in enumerate(np.arange(50.4, 53.0, 0.18)):
    place(pop(), float(s), 0.5)
place(ding(), 53.5)
place(pop(), 56.2)
place(chime(), 58.0)

mix = out + bgm
peak = np.max(np.abs(mix))
mix = mix / peak * 0.89
stereo = np.stack([mix, mix], axis=1)
wavfile.write(sys.argv[1], SR, (stereo * 32767).astype(np.int16))
print("ok", peak)
