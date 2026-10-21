import numpy as np
from scipy.io import wavfile
import sys

SR = 48000
DUR = 40.0
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


