import json, subprocess, os, sys
P = "proto5"
J = json.load(open(f"{P}/assets/times.json")); T, TOTAL = J["T"], J["TOTAL"]
s = lambda k: T[k][0]
R = {}
for f in ["stock/results1.json","stock/results.json","stock/results3.json"]:
    for q,hits in json.load(open(f)).items():
        for h in hits: R[h["id"]] = h
SPEC = [  # name, id, start, end, offset, crop-x, blur
 ("v01", 82365, 0, s("L02"), 1.0, 0.5, 0),
 ("v02", 324825, s("L02"), s("L03"), 0.5, 0.55, 0),
 ("v03", 135141, s("L03"), s("L04"), 0.5, 0.5, 0),
 ("v04", 135167, s("L04"), s("L05"), 0.5, 0.5, 0),
 ("v05", 135164, s("L05"), s("L07"), 2.0, 0.5, 0),
 ("v06", 202987, s("L07"), s("L09"), 2.0, 0.5, 0),
 ("v07", 66410, s("L09"), s("L10"), 3.0, 0.5, 0),
 ("v08", 202740, s("L10"), s("L11"), 1.0, 0.5, 0),
 ("v09", 330502, s("L11"), s("L14"), 1.0, 0.42, 0),
 ("v10", 248447, s("L14"), TOTAL, 1.0, 0.5, 1),
]
os.makedirs("stock/raw", exist_ok=True); clips=[]
for name, vid, a, b, off, cx, blur in SPEC:
    raw=f"stock/raw/{vid}.mp4"
    if not os.path.exists(raw):
        v=R[vid]["videos"]; src=v["large"] if v["large"]["url"] else v["medium"]
        subprocess.run(["curl","-sS","-o",raw,src["url"]],check=True)
    pr=json.loads(subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height:format=duration","-of","json",raw],capture_output=True,text=True).stdout)
    W,H=pr["streams"][0]["width"],pr["streams"][0]["height"]; sd=float(pr["format"]["duration"]); off=min(off,max(0,sd-1))
    d=round(b-a+0.1,3)
    if W/H>9/16: cw=int(H*9/16)//2*2; ch=H; x=int(min(max(cx*W-cw/2,0),W-cw)); y=0
    else: cw=W; ch=int(W*16/9)//2*2; x=0; y=int((H-ch)/2)
    vf=f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos,fps=30"
    if blur: vf+=",boxblur=22:2,eq=brightness=-0.08"
    vf+=f",tpad=stop_mode=clone:stop_duration={d}"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",str(off),"-i",raw,"-t",str(d),"-vf",vf,"-an","-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",f"{P}/assets/v/{name}.mp4"],check=True)
    clips.append({"name":name,"start":round(a,3),"dur":round(b-a,3)}); print(name,vid,R[vid]["tags"][:50])
json.dump(clips,open(f"{P}/assets/clips.json","w"))
