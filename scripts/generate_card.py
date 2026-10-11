#!/usr/bin/env python3
"""Generate Flyken271's animated neofetch profile card (GIF) with LIVE GitHub stats."""
import os, sys, math, datetime, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------- palette (GitHub dark / Andrew-style) ----------
BGc=(22,27,34); BASE=(201,209,217); KEYC=(255,166,87); VALC=(165,214,255)
CC=(97,110,127); ADD=(63,185,80); DEL=(248,81,73); NUC=(235,240,245)
CW,CH=10,24
FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BLD="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def dim(c,f): return tuple(int(v*f) for v in c)

# ---------- fetch live stats ----------
def fetch_stats(token, login):
    import requests
    q = """
    query($login:String!){
      user(login:$login){
        name login createdAt
        followers{totalCount}
        repositories(ownerAffiliations:OWNER, privacy:PUBLIC, first:100){
          totalCount nodes{ stargazerCount }
        }
        contributionsCollection{ totalCommitContributions restrictedContributionsCount }
      }
    }"""
    r = requests.post("https://api.github.com/graphql",
                      json={"query": q, "variables": {"login": login}},
                      headers={"Authorization": f"bearer {token}"}, timeout=30)
    r.raise_for_status()
    u = r.json()["data"]["user"]
    stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
    cc = u["contributionsCollection"]
    commits = cc["totalCommitContributions"] + cc.get("restrictedContributionsCount", 0)
    created = datetime.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    days = (now - created).days
    yrs = days // 365; rem = days % 365
    return {
        "login": u["login"],
        "uptime": f"{yrs} years, {rem} days",
        "repos": u["repositories"]["totalCount"],
        "stars": stars,
        "followers": u["followers"]["totalCount"],
        "commits": commits,
    }

def demo_stats():
    return {"login":"Flyken271","uptime":"5 years, 142 days","repos":55,"stars":40,"followers":7,"commits":214}

# ---------- render ----------
cols, rows = 112, 22
W, H = cols*CW+30, rows*CH+30
RX, VC = 40, 24
acx, acy = 17, 11
A, Bb = 13.0, 5.5

PROFILE = [
    ("Uptime", None),                      # filled from stats
    ("Focus", "systems • security"),
    ("Editor", "VS Code"),
    None,
    ("Languages.Programming", "C, C++, C#, Go, Python, Lua"),
    ("Languages.Web", "JavaScript, TypeScript, HTML, CSS"),
    ("Pursuing", "IT & security certifications"),
    None,
    ("Interests.Software", "reverse engineering, homebrew, gamedev"),
    ("Interests.Hardware", "console modding, electronics"),
    ("Disclosures", "1 [EMBARGOED]"),
]

def build_grid(stats):
    g=[[(' ',BASE)]*cols for _ in range(rows)]
    def seg(r,parts):
        x=RX
        for txt,col in parts:
            for ch in txt:
                if x<cols: g[r][x]=(ch,col); x+=1
    def kv(r,key,val):
        x=RX; g[r][x]=('.',CC); g[r][x+1]=(' ',CC); x+=2
        parts=key.split('.')
        for pi,part in enumerate(parts):
            for ch in part:
                if x<cols: g[r][x]=(ch,KEYC); x+=1
            if pi<len(parts)-1: g[r][x]=('.',CC); x+=1
        g[r][x]=(':',CC); x+=1
        while x<RX+VC-1: g[r][x]=('.',CC); x+=1
        x+=1
        for ch in val:
            c=VALC if ch.isdigit() else VALC
            if ch in "[]": c=DEL
            if x<cols: g[r][x]=(ch,c); x+=1
    def header(r,txt):
        x=RX
        for ch in txt: g[r][x]=(ch,BASE); x+=1
        g[r][x]=(' ',BASE); x+=1
        while x<cols-2: g[r][x]=('—',CC); x+=1
    header(0, f"{stats['login']}@github")
    r=1
    for spec in PROFILE:
        if spec is None: r+=1; continue
        key,val = spec
        if key=="Uptime": val=stats["uptime"]
        kv(r,key,val); r+=1
    header(r,"GitHub Stats"); r+=1
    seg(r,[(". ",CC),("Repos",KEYC),(": ",CC),(f"{stats['repos']}",VALC),
           ("  |  ",CC),("Stars",KEYC),(": ",CC),(f"{stats['stars']}",VALC)]); r+=1
    seg(r,[(". ",CC),("Commits (1y)",KEYC),(": ",CC),(f"{stats['commits']:,}",VALC),
           ("  |  ",CC),("Followers",KEYC),(": ",CC),(f"{stats['followers']}",VALC)])
    return g

ELECS=[(0.0,+1,0.0,1,KEYC),(math.pi/3,-1,1.6,2,VALC),(2*math.pi/3,+1,3.1,1,KEYC),(math.pi/2,-1,4.4,2,VALC)]
N=40
def pos(pl,t):
    ex,ey=A*math.cos(t),Bb*math.sin(t)
    rx=ex*math.cos(pl)-ey*math.sin(pl); ry=(ex*math.sin(pl)+ey*math.cos(pl))*0.5
    return acx+rx,acy+ry

def render(stats, out_path):
    base=build_grid(stats)
    F=ImageFont.truetype(FONT_REG,17); B=ImageFont.truetype(FONT_BLD,17)
    def frame(f):
        g=[row[:] for row in base]
        def put(x,y,c,col):
            xi,yi=int(round(x)),int(round(y))
            if 0<=yi<rows and 0<=xi<38: g[yi][xi]=(c,col)
        t0=2*math.pi*f/N
        for (pl,dr,ph,sp,col) in ELECS:
            for k in range(14):
                x,y=pos(pl,k*(2*math.pi/14)); put(x,y,'·',dim(CC,0.5))
        for (pl,dr,ph,sp,col) in ELECS:
            p=ph+dr*t0*sp
            for k in range(4,0,-1):
                x,y=pos(pl,p-dr*0.16*k); put(x,y,'.' if k>2 else '*',dim(col,0.35+0.13*(4-k)))
            x,y=pos(pl,p); put(x,y,'o',col)
        for dx,c,cl in [(-1,'(',dim(NUC,.6)),(0,'@',NUC),(1,')',dim(NUC,.6))]: put(acx+dx,acy,c,cl)
        img=Image.new("RGB",(W,H),(13,17,23)); d=ImageDraw.Draw(img)
        d.rounded_rectangle([8,8,W-8,H-8],radius=16,fill=BGc)
        for r in range(rows):
            for c in range(cols):
                ch,col=g[r][c]
                if ch!=' ':
                    fnt=B if (col in (KEYC,BASE) or ch in '@()') else F
                    d.text((18+c*CW,16+r*CH),ch,font=fnt,fill=col)
        return np.array(img)
    import imageio
    imageio.mimsave(out_path,[frame(f) for f in range(N)],fps=16,loop=0)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--demo",action="store_true")
    ap.add_argument("--out",default="dist/card.gif")
    a=ap.parse_args()
    os.makedirs(os.path.dirname(a.out),exist_ok=True)
    if a.demo:
        stats=demo_stats()
    else:
        token=os.environ["GH_TOKEN"]; login=os.environ.get("LOGIN","Flyken271")
        stats=fetch_stats(token,login)
    render(stats,a.out)
    print("wrote",a.out,"stats:",stats)
