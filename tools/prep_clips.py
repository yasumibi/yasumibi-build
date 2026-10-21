import json, subprocess, sys
T = json.load(open("proto4/assets/times.json"))["T"]; TOTAL = json.load(open("proto4/assets/times.json"))["TOTAL"]
s = lambda k: T[k][0]
# name, src id, scene start, scene end, source offset, crop x center (0-1), blur
SPEC = [
 ("v01", 324825, 0, s("L02"), 0.0, 0.55, 0),
 ("v02", 266428, s("L02"), s("L04a"), 3.0, 0.5, 0),
 ("v03", 205231, s("L04a"), s("L04b"), 1.0, 0.5, 0),
 ("v04", 265606, s("L04b"), s("L04c"), 1.0, 0.5, 0),
 ("v05", 374892, s("L04c"), s("L05"), 0.5, 0.5, 0),
 ("v06", 36458, s("L05"), s("L12a"), 0.0, 0.5, 1),
 ("v07", 204278, s("L12a"), s("L13a"), 0.5, 0.5, 0),
 ("v08", 92545, s("L13a"), s("L13b"), 2.0, 0.4, 0),
 ("v09", 265606, s("L13b"), s("L13c"), 4.0, 0.75, 0),
 ("v10", 108259, s("L13c"), s("L14a"), 2.0, 0.5, 0),
 ("v11", 330502, s("L14a"), s("L16"), 2.0, 0.42, 0),
 ("v12", 335699, s("L16"), s("L17a"), 4.0, 0.62, 1),
 ("v13", 367168, s("L17a"), TOTAL, 0.0, 0.5, 0),
]
out = []
for name, vid, a, b, off, cx, blur in SPEC:
    d = round(b - a + 0.1, 3)
    probe = json.loads(subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height:format=duration","-of","json",f"stock/raw/{vid}.mp4"],capture_output=True,text=True).stdout)
    W, H = probe["streams"][0]["width"], probe["streams"][0]["height"]; srcdur = float(probe["format"]["duration"])
    off = min(off, max(0, srcdur - 0.5))
    if W / H > 9 / 16:
        cw = int(H * 9 / 16) // 2 * 2; ch = H
        x = int(min(max(cx * W - cw / 2, 0), W - cw)); y = 0
    else:
        cw = W; ch = int(W * 16 / 9) // 2 * 2; x = 0; y = int((H - ch) / 2)
    vf = f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos,fps=30"
    if blur: vf += ",boxblur=22:2,eq=brightness=-0.06"
    vf += f",tpad=stop_mode=clone:stop_duration={d}"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",str(off),"-i",f"stock/raw/{vid}.mp4","-t",str(d),"-vf",vf,"-an",
                    "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",f"proto4/assets/v/{name}.mp4"],check=True)
    out.append({"name":name,"start":round(a,3),"dur":round(b-a,3)})
    print(name, vid, round(b-a,2))
json.dump(out, open("proto4/assets/clips.json","w"))
