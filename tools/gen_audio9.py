import sys, json, numpy as np
from scipy.io import wavfile

ASSETS = sys.argv[1]
J = json.load(open(f"{ASSETS}/times.json"))
T, TOTAL = J["T"], J["TOTAL"]
lib = open(__file__.replace("gen_audio9.py", "synth_lib.py"), encoding="utf-8").read().replace("DUR = 40.0", f"DUR = {TOTAL}")
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


# ---------- BGM 112 BPM (lighter) ----------
bgm = np.zeros(N); B = 60 / 112
def bp(sig, at, g):
    i = int(at * SR); j = min(N, i + len(sig))
    if 0 <= i < N: bgm[i:j] += sig[: j - i] * g
mutes = [(TOTAL - 0.6, TOTAL + 1)]
muted = lambda x: any(a <= x < b for a, b in mutes)
chords = [(261.6, 329.6, 392.0), (220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]
k, b = 0, 0.0
while b < TOTAL:
    if not muted(b):
        bp(kick(), b, 0.42 if k % 2 == 0 else 0.0)
        if k % 2 == 1: bp(clap(), b, 0.14)
        bp(hat(), b + B / 2, 0.1)
        if k % 2 == 0:
            ch = chords[(k // 8) % 4]; x = t(B * 1.9)
            pad = sum(np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x) for f in ch)
            bp(pad * env(len(x), 0.02, 0.6) * 0.06, b, 1)
            bx = t(B * 0.9); bf = ch[0] / 2
            bp(np.sin(2 * np.pi * bf * bx) * env(len(bx), 0.01, 0.25), b, 0.22)
    b += B; k += 1
fx = {"impact": impact, "pop": pop, "whoosh": whoosh, "chime": chime, "sparkle": sparkle, "tick": tick, "ding": ding, "bonk": bonk, "snip": snip}
EV = [("whoosh", 0.0), ("chime", 0.3), ("pop", 2.1), ("pop", s("L02")), ("impact", s("L02") + 1.7),
      ("whoosh", s("L03")), ("whoosh", s("L03") + 0.2), ("chime", s("L03") + 2.0),
      ("impact", s("L04") + 0.6), ("pop", s("L04") + 0.7), ("pop", s("L04") + 1.3), ("pop", s("L04") + 1.4),
      ("impact", s("L05") + 3.4), ("sparkle", s("L05") + 3.5), ("ding", s("L05") + 4.0), ("ding", s("L05") + 4.12), ("ding", s("L05") + 4.24), ("ding", s("L05") + 4.36),
      ("whoosh", s("L06")), ("pop", s("L06") + 1.7), ("pop", s("L07")), ("whoosh", s("L07") + 0.6), ("impact", s("L07") + 3.35), ("chime", s("L07") + 3.35),
      ("whoosh", s("L08")), ("chime", s("L08") + 1.4), ("pop", s("L08") + 2.8), ("pop", s("L08") + 3.4), ("pop", s("L08") + 4.8), ("impact", s("L08") + 5.5), ("sparkle", s("L08") + 5.6),
      ("whoosh", s("L09")), ("impact", s("L09") + 1.6), ("pop", s("L09") + 3.5), ("chime", s("L09") + 3.9)]
for n, a, b2 in [(x[0], x[1], 0) for x in EV]: place(fx[n](), a, 0.55)
for i in range(31): place(tick(), s("L03") + 0.7 + (i + 1) * 0.06, 0.35)
ticks(s("L03") + 0.6, s("L03") + 2.0, 24)
drumroll(s("L05") + 1.2, s("L05") + 3.4)
import os
voice = np.zeros(N)
if os.path.exists(f"{ASSETS}/narr.wav"):
    sr_n, nar = wavfile.read(f"{ASSETS}/narr.wav"); nar = nar.astype(np.float64) / 32767
    voice[: min(N, len(nar))] = nar[:N]
mix = voice + out * 0.45
mix = mix / np.max(np.abs(mix)) * 0.92
wavfile.write(f"{ASSETS}/audio.wav", SR, (np.stack([mix, mix], 1) * 32767).astype(np.int16))
print("ok", TOTAL)
