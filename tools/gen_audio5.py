import sys, json, numpy as np
from scipy.io import wavfile

ASSETS = sys.argv[1]
J = json.load(open(f"{ASSETS}/times.json"))
T, TOTAL = J["T"], J["TOTAL"]
lib = open(__file__.replace("gen_audio5.py", "synth_lib.py"), encoding="utf-8").read().replace("DUR = 40.0", f"DUR = {TOTAL}")
exec(lib)
s = lambda k: T[k][0]
e = lambda k: T[k][1]


def wahwah(short=False):
    seq = [(392, 0.2), (370, 0.2), (349, 0.2), (330, 0.55)] if short else [(392, 0.28), (370, 0.28), (349, 0.28), (330, 0.8)]
    res = []
    for f, d in seq:
        x = t(d); vib = 1 + 0.012 * np.sin(2 * np.pi * 6 * x) * (x > 0.12)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        sig = sum(np.sin(k * ph) / k for k in range(1, 8))
        res.append(sig * np.clip(x / 0.02, 0, 1) * np.clip((d - x) / 0.05, 0, 1) * 0.22)
    return np.concatenate(res)


def scratch():
    x = t(0.3); f = np.where(x < 0.15, 300 + 3200 * x, 780 - 2600 * (x - 0.15)); f = np.maximum(f, 80)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sign(np.sin(ph)) * 0.3 + rng.standard_normal(len(x)) * 0.3) * np.clip(1 - x / 0.3, 0, 1)


def sparkle():
    x = t(0.5); ph = 2 * np.pi * np.cumsum(1500 + 2500 * x / 0.5) / SR
    return np.sin(ph) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * x)) * env(len(x), 0.005, 0.2) * 0.25


def snip():
    x = t(0.08)
    return rng.standard_normal(len(x)) * env(len(x), 0.0005, 0.01) * 0.6 + np.sin(2 * np.pi * 2400 * x) * env(len(x), 0.0005, 0.02) * 0.3


# ---------- BGM 150 BPM ----------
bgm = np.zeros(N); B = 60 / 150
def bp(sig, at, g):
    i = int(at * SR); j = min(N, i + len(sig))
    if 0 <= i < N: bgm[i:j] += sig[: j - i] * g
mutes = [(s("L11") - 0.05, s("L11") + 1.15), (TOTAL - 0.5, TOTAL + 1)]
muted = lambda x: any(a <= x < b for a, b in mutes)
bass = [55.0, 55.0, 65.41, 73.42, 55.0, 55.0, 49.0, 49.0]
k, b = 0, 0.0
while b < TOTAL:
    if not muted(b):
        bp(kick(), b, 0.6)
        if k % 2 == 1: bp(clap(), b, 0.28)
        for q in range(4):
            if not muted(b + q * B / 4): bp(hat(), b + q * B / 4, 0.16 if q % 2 else 0.09)
        x = t(B / 2 * 0.9); f = bass[(k // 2) % 8]
        bp((np.sign(np.sin(2 * np.pi * f * x)) * 0.5 + np.sin(2 * np.pi * f * x)) * env(len(x), 0.004, 0.12), b + B / 2, 0.22)
    b += B; k += 1
def riser(a, z):
    d = z - a; x = t(d); n = rng.standard_normal(len(x)); n = n - np.convolve(n, np.ones(3) / 3, mode="same")
    bp(n * (x / d) ** 2 * 0.3, a, 1)
riser(s("L11") - 0.7, s("L11"))
fx = {"impact": impact, "big": lambda: impact(True), "pop": pop, "whoosh": whoosh, "chime": chime, "sparkle": sparkle,
      "scratch": scratch, "tick": tick, "ding": ding, "bonk": bonk, "snip": snip}
EV = [("impact", 0.02), ("whoosh", s("L02")), ("big", s("L02") + 0.45), ("pop", s("L02") + 0.9)]
for k2 in ["L03", "L05", "L07", "L09"]:
    EV += [("whoosh", s(k2) - 0.05), ("big", s(k2) + 0.02), ("pop", s(k2) + 0.45)]
EV += [("pop", s("L04") - 0.2), ("sparkle", s("L04") + 0.6), ("big", s("L06") + 0.05), ("pop", s("L06") + 0.4),
       ("pop", s("L07") + 0.9), ("chime", s("L08") + 1.3), ("bonk", s("L10") + 0.1), ("big", s("L10") + 1.02),
       ("big", s("L11") + 0.02), ("scratch", s("L11") + 0.8), ("big", s("L11") + 1.1), ("whoosh", s("L12") + 0.15), ("chime", s("L12") + 1.6),
       ("impact", s("L13") + 0.08), ("sparkle", s("L13") + 0.3), ("whoosh", s("L14")), ("chime", s("L14") + 1.0)]
for n, a in EV: place(fx[n](), a, 0.75)
for i in range(6): place(pop(), s("L08") + i * 0.2, 0.5)
for i in range(5): place(tick(), s("L14") + 0.45 + i * 0.12, 1.0)
import os
voice = np.zeros(N)
if os.path.exists(f"{ASSETS}/narr.wav"):
    sr_n, nar = wavfile.read(f"{ASSETS}/narr.wav"); nar = nar.astype(np.float64) / 32767
    voice[: min(N, len(nar))] = nar[:N]
mix = voice + out * 0.55 + bgm * 0.3
mix = mix / np.max(np.abs(mix)) * 0.92
wavfile.write(f"{ASSETS}/audio.wav", SR, (np.stack([mix, mix], 1) * 32767).astype(np.int16))
print("ok", TOTAL)
