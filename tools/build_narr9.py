"""Cut the ElevenLabs take into lines, speed up slightly, re-pack with tight gaps.
Writes assets/narr.wav and assets/times.js (window.T = {key: [start, end]}, window.TOTAL)."""
import json, subprocess, sys, numpy as np
from scipy.io import wavfile

SRC, OUTDIR = sys.argv[1], sys.argv[2]
SPEED = 1.0
SR = 48000
CH = [
    ("L01", 0.0, 4.42, 0.00), ("L02", 4.78, 8.21, 0.45),
    ("L03", 8.44, 12.45, 0.45), ("L04", 12.88, 15.12, 0.40),
    ("L05", 15.55, 20.80, 0.40), ("L06", 21.28, 25.69, 0.50),
    ("L07", 25.98, 30.43, 0.40), ("L08", 30.80, 38.51, 0.50),
    ("L09", 38.85, 44.11, 0.50),
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

total = round(t + 2.2, 2)
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
