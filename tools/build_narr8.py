"""Cut the ElevenLabs take into lines, speed up slightly, re-pack with tight gaps.
Writes assets/narr.wav and assets/times.js (window.T = {key: [start, end]}, window.TOTAL)."""
import json, subprocess, sys, numpy as np
from scipy.io import wavfile

SRC, OUTDIR = sys.argv[1], sys.argv[2]
SPEED = 1.0
SR = 48000
CH = [
    ("L01", 0.0, 5.48, 0.00), ("L02", 6.00, 7.34, 0.55),
    ("L03", 8.20, 14.11, 0.80), ("L04", 14.65, 17.96, 0.55),
    ("L05", 18.42, 23.22, 0.50), ("L06", 23.62, 28.36, 0.55),
    ("L07", 28.75, 31.75, 0.55), ("L08", 32.11, 36.64, 0.80),
    ("L09", 36.96, 40.14, 0.75), ("L10", 40.51, 44.40, 0.80),
]
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", SRC, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.float32)


def stretch(seg):
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", f"atempo={SPEED}", "-f", "f32le", "-"], input=seg.tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32)


pieces, T, t = [], {}, 0.0
for key, a, b, gap in CH:
    seg = x[int(a * SR):int(b * SR)].copy()
    fade = int(0.012 * SR)
    seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    seg = seg if SPEED == 1.0 else stretch(seg)
    t += gap
    T[key] = [round(t, 3), round(t + len(seg) / SR, 3)]
    pieces.append((t, seg))
    t += len(seg) / SR

total = round(t + 3.0, 2)
out = np.zeros(int(total * SR) + SR, dtype=np.float32)
for st, seg in pieces:
    i = int(st * SR); out[i:i + len(seg)] += seg
out = out[: int(total * SR)]
out = out / max(1e-6, np.max(np.abs(out))) * 0.95
wavfile.write(f"{OUTDIR}/narr.wav", SR, (out * 32767).astype(np.int16))
with open(f"{OUTDIR}/times.js", "w") as f:
    f.write("window.T = " + json.dumps(T) + ";\nwindow.TOTAL = " + str(total) + ";\n")
json.dump({"T": T, "TOTAL": total}, open(f"{OUTDIR}/times.json", "w"))
print("total", total)
for k, v in T.items():
    print(k, v)
