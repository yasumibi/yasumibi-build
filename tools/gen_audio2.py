import sys, numpy as np
exec(open(__file__.replace('gen_audio2.py','synth_lib.py'),encoding='utf-8').read())
from scipy.io import wavfile

def wahwah():
    seq=[(392,0.28),(370,0.28),(349,0.28),(330,0.8)]
    res=[]
    for f,d in seq:
        x=t(d); vib=1+0.012*np.sin(2*np.pi*6*x)*(x>0.15)
        ph=2*np.pi*np.cumsum(f*vib)/SR
        s=sum(np.sin(k*ph)/k for k in range(1,8))
        e=np.clip(x/0.02,0,1)*np.clip((d-x)/0.05,0,1)
        res.append(s*e*0.22)
    return np.concatenate(res)

def deflate():
    x=t(0.45); n=rng.standard_normal(len(x)); n=np.convolve(n,np.ones(6)/6,mode='same')
    f=900*np.exp(-x*5)+120; ph=2*np.pi*np.cumsum(f)/SR
    return (n*0.5+np.sin(ph)*0.4)*np.clip(1-x/0.45,0,1)*0.7

def scratch():
    x=t(0.35); f=np.where(x<0.17, 300+3000*x, 900-2500*(x-0.17)); f=np.maximum(f,80)
    ph=2*np.pi*np.cumsum(f)/SR; n=rng.standard_normal(len(x))
    return (np.sign(np.sin(ph))*0.25+n*0.25)*np.clip(1-x/0.35,0,1)

def sparkle():
    x=t(0.5); f=1500+2500*x/0.5; ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*(0.5+0.5*np.sin(2*np.pi*30*x))*env(len(x),0.005,0.2)*0.25

# ---- 150 BPM beat ----
bgm=np.zeros(N); B=60/150
def bp(sig,at,g):
    i=int(at*SR); j=min(N,i+len(sig)); bgm[i:j]+=sig[:j-i]*g
mutes=[(10.3,12.0),(13.55,14.4),(16.3,17.15),(39.4,40)]
def muted(x): return any(a<=x<b for a,b in mutes)
bass=[55.0,55.0,65.41,73.42, 55.0,55.0,49.0,49.0]
k=0; b=0.0
while b<DUR:
    if not muted(b):
        bp(kick(),b,0.6)
        if k%2==1: bp(clap(),b,0.28)
        for s in range(4):
            if not muted(b+s*B/4): bp(hat(),b+s*B/4,0.16 if s%2 else 0.09)
        # offbeat pumping bass
        x=t(B/2*0.9); f=bass[(k//2)%8]
        sq=np.sign(np.sin(2*np.pi*f*x))*0.5+np.sin(2*np.pi*f*x)
        bp(sq*env(len(x),0.004,0.12),b+B/2,0.22)
    b+=B; k+=1
# risers before slams
def riser(start,end):
    d=end-start; x=t(d); n=rng.standard_normal(len(x)); n=n-np.convolve(n,np.ones(3)/3,mode='same')
    bp(n*(x/d)**2*0.25,start,1)
riser(24.2,24.95); riser(35.8,36.5)

E=[('impact',0.02),('impact_big',1.2),('pop',2.45),('pop',2.6),('impact',3.6),('deflate',4.3),('whoosh',4.32),('wahwah',4.55),
   ('impact',5.68),('impact',6.13),('impact',6.58),('impact_big',7.6),('buzzer',7.7),('whoosh',9.4),('pop',10.1),
   ('impact_big',12.1),('chime',12.12),('sparkle',12.3),('scratch',13.55),('gong',16.4),('impact_big',16.45),
   ('whoosh',17.2),('pop',17.45),('pop',18.62),('pop',19.82),('whoosh',21.0),('impact_big',22.05),('pop',23.15),('tick',24.2),
   ('impact_big',25.06),('whoosh',25.75),('chime',28.12),('sparkle',28.2),('impact',29.05),('ding',29.1),('whoosh',30.5),
   ('ding',35.2),('pop',33.8),('pop',34.6),('impact',36.55),('impact',36.9),('chime',38.0),('impact',38.25)]
fn={'impact':impact,'impact_big':lambda:impact(True),'pop':pop,'deflate':deflate,'whoosh':whoosh,'wahwah':wahwah,'buzzer':buzzer,
    'chime':chime,'sparkle':sparkle,'scratch':scratch,'gong':gong,'tick':tick,'ding':ding}
for n,a in E: place(fn[n](),a)
drumroll(10.4,11.95)
ticks(15.1,16.3,30); ticks(26.9,28.1,30)
for i,s in enumerate(np.arange(31.4,33.0,0.12)): place(pop(),float(s),0.35)
mix=out+bgm*0.8
mix=mix/np.max(np.abs(mix))*0.89
wavfile.write(sys.argv[1],SR,(np.stack([mix,mix],1)*32767).astype(np.int16))
print('ok')
