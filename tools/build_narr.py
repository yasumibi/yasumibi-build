"""Cut the ElevenLabs take into lines, speed up slightly, re-pack with tight gaps.
Writes assets/narr.wav and assets/times.js (window.T = {key: [start, end]}, window.TOTAL)."""
import json, subprocess, sys, numpy as np
from scipy.io import wavfile

SRC, OUTDIR = sys.argv[1], sys.argv[2]
SPEED = 1.06
SR = 48000

# (key, src_start, src_end, gap_before_in_output)
CH = [
    ("L01a", 0.10, 1.98, 0.00), ("L01b", 2.74, 5.19, 0.12),
    ("L02", 5.95, 7.79, 0.25), ("L03", 8.34, 9.64, 0.12),
    ("L04a", 10.09, 10.94, 0.18), ("L04b", 11.29, 12.01, 0.10), ("L04c", 12.38, 13.31, 0.10),
    ("L05", 13.75, 16.45, 0.18),
    ("L06", 16.89, 20.99, 0.25),
    ("L07", 21.37, 22.56, 1.00),
    ("L08", 22.97, 25.04, 0.20), ("L09", 25.52, 27.40, 0.15),
    ("L10a", 27.91, 29.84, 0.25), ("L10b", 30.47, 31.68, 1.15), ("L10c", 32.05, 32.34, 0.12),
    ("L11", 32.68, 33.42, 0.42),
    ("L12a", 33.79, 35.45, 0.22), ("L12b", 35.61, 36.28, 0.08),
    ("L13a", 36.63, 37.62, 0.22), ("L13b", 37.90, 38.53, 0.08), ("L13c", 38.94, 40.48, 0.08),
    ("L14a", 40.78, 41.34, 0.25), ("L14b", 41.55, 44.58, 0.12),
    ("L15", 44.83, 46.39, 0.18),
    ("L16", 46.82, 50.03, 0.25),
    ("L17a", 50.48, 52.00, 0.25), ("L17b", 52.63, 54.11, 0.45),
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
    seg = stretch(seg)
    t += gap
    T[key] = [round(t, 3), round(t + len(seg) / SR, 3)]
    pieces.append((t, seg))
    t += len(seg) / SR

total = round(t + 0.9, 2)
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
