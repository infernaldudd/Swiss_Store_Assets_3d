"""Generate original illustration-based shelf-packaging textures for 88 fictional chips.

All brand graphics and food illustrations are custom-created for the game.
No scanned retail packages, copyrighted logos or photographs are embedded.
Run: /usr/bin/python3 tools/generate_chip_library_textures.py
"""
import os, json, math, random, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
DATA=json.load(open(os.path.join(ROOT,"catalog","chip_collection.json"),encoding="utf-8"))["entries"]
DEST=os.path.join(ROOT,"textures","chips")
os.makedirs(DEST,exist_ok=True)
W,H=672,1008
FONTS={
"heavy":["/usr/share/fonts/truetype/lato/Lato-Heavy.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
"black":["/usr/share/fonts/truetype/lato/Lato-Black.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
"regular":["/usr/share/fonts/truetype/lato/Lato-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
"italic":["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf"]}
def font(size,kind="heavy"):
    for p in FONTS[kind]:
        if os.path.isfile(p):
            return ImageFont.truetype(p,max(8,int(size)))
    return ImageFont.load_default()
def hx(s):
    return tuple(int(s[i:i+2],16) for i in (1,3,5))
def mix(a,b,t):
    return tuple(int(a[k]*(1-t)+b[k]*t) for k in range(3))
def label(d,text,x,y,w,maxh,color,kind="black",stroke=0,stroke_color=None):
    size=maxh
    while size>=12:
        f=font(size,kind)
        bb=d.textbbox((0,0),text,font=f,stroke_width=stroke)
        if bb[2]-bb[0]<=w:break
        size-=2
    d.text((int(x-bb[0]),int(y-bb[1])),text,font=f,
           fill=color,stroke_width=stroke,stroke_fill=stroke_color)
    return maxh
def centered(d,text,y,width,maxsize,color,kind="heavy",stroke=0,stroke_color=None):
    size=maxsize
    while size>=12:
        f=font(size,kind)
        bb=d.textbbox((0,0),text,font=f,stroke_width=stroke)
        if bb[2]-bb[0]<=width:break
        size-=2
    x=(W-(bb[2]-bb[0]))//2-bb[0]
    d.text((x,y-bb[1]),text,font=f,fill=color,
           stroke_width=stroke,stroke_fill=stroke_color)
def colorbg(accent,seed,style):
    base=hx(accent)
    rng=random.Random(seed)
    im=Image.new("RGB",(W,H))
    pix=im.load()
    tint=(230,226,207) if style in ("gourmet","legume") else base
    for y in range(H):
        yy=y/H
        for x in range(W):
            edge=abs(x-W/2)/(W/2)
            t=.10+.29*yy+.15*edge
            c=mix(tint,(35,28,21),t)
            streak=5*math.sin(y*.029+x*.009)+3*math.sin(x*.064+y*.032)
            g=rng.gauss(0,1.6)
            pix[x,y]=tuple(max(0,min(255,int(v+streak+g))) for v in c)
    return im
def chip_picture(img,seed,shape):
    # Original painterly chip illustrations, not retail package photos.
    rr=random.Random(seed)
    artist=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(artist,"RGBA")
    positions=[(225,703,148,92,-22),(417,686,139,105,23),(328,786,155,104,4)]
    if shape=="tortilla":
        positions=[(230,690,155,109,-17),(418,699,152,112,21),(322,784,152,111,0)]
    if shape=="puffed":
        positions=[(210,725,72,35,-25),(345,680,86,36,16),(450,751,80,36,29),(300,815,87,34,-15)]
    for idx,(cx,cy,rx,ry,rot) in enumerate(positions):
        a=math.radians(rot)
        pts=[]
        if shape=="tortilla":
            points=[(-1,-.72),(1,-.72),(0,1)]
            for xx,yy in points:pts.append((cx+xx*rx*math.cos(a)-yy*ry*math.sin(a),cy+xx*rx*math.sin(a)+yy*ry*math.cos(a)))
        elif shape=="puffed":
            for j in range(28):
                t=math.tau*j/28
                x=rx*math.cos(t);y=ry*math.sin(t)
                pts.append((cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a)))
        else:
            for j in range(46):
                t=math.tau*j/46
                noise=1+rr.uniform(-.035,.045)
                x=rx*noise*math.cos(t);y=ry*noise*math.sin(t)
                pts.append((cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a)))
        d.polygon([(x+13,y+15) for x,y in pts],fill=(41,21,6,96))
        d.polygon(pts,fill=(232,176,78,255))
        d.line(pts+[pts[0]],fill=(157,97,39,240),width=6,joint="curve")
        d.arc((cx-rx*.68,cy-ry*.68,cx+rx*.62,cy+ry*.64),184,314,fill=(255,230,147,160),width=11)
        for i in range(120):
            x=rr.uniform(cx-rx*.82,cx+rx*.82)
            y=rr.uniform(cy-ry*.77,cy+ry*.77)
            # Some flecks may land outside, but these are only artistic seasoning.
            if (x-cx)**2/(rx**2)+(y-cy)**2/(ry**2)>1:continue
            rad=rr.choice((1,1,2,3))
            col=rr.choice(((146,67,20,175),(255,249,194,168),(183,91,39,200)))
            d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=col)
    img.paste(artist,(0,0),artist)
def motif(img,style,accent,seed):
    rr=random.Random(seed)
    d=ImageDraw.Draw(img,"RGBA")
    if style=="original":
        d.polygon([(0,375),(672,519),(672,620),(0,491)],fill=(250,246,225,230))
        d.line((0,376,672,519),fill=(255,245,215,215),width=16)
        d.polygon([(0,603),(672,521),(672,650),(0,719)],fill=(240,173,59,55))
    elif style=="supermarket":
        for j in range(7):
            x=50+j*95
            d.polygon([(x,460),(x+60,438),(x+30,530)],fill=(243,242,219,45))
        d.rounded_rectangle((38,493,633,604),radius=20,fill=(27,37,43,190))
    elif style=="tortilla":
        d.polygon([(0,545),(672,425),(672,584),(0,684)],fill=(255,211,64,155))
        for j in range(10):
            x=rr.randint(0,670);y=rr.randint(575,876)
            d.polygon([(x,y-22),(x+20,y+18),(x-20,y+18)],fill=(255,244,185,45))
    elif style=="stacked":
        for j in range(9):
            cx=rr.randint(0,672);cy=rr.randint(550,900);r=rr.randrange(18,90)
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(255,240,194,100),width=5)
        d.rounded_rectangle((58,422,613,569),35,fill=(255,242,204,235))
    elif style=="puffed":
        for j in range(14):
            cx=rr.randint(0,672);cy=rr.randint(480,900);r=rr.randint(20,75)
            d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,240,188,39))
        d.polygon([(58,473),(555,451),(608,580),(85,628)],fill=(255,253,225,225))
    elif style=="gourmet":
        d.line((54,400,617,400),fill=(34,34,30,175),width=6)
        d.line((54,609,617,609),fill=(34,34,30,175),width=6)
        d.rounded_rectangle((60,435,613,575),radius=5,fill=(34,38,33,210))
    elif style=="legume":
        d.polygon([(0,501),(672,418),(672,594),(0,668)],fill=(224,250,207,140))
        for j in range(11):
            x=rr.randint(0,672);y=rr.randint(650,840)
            d.ellipse((x-10,y-16,x+10,y+16),fill=(86,143,82,100))
def brand_art(img,entry,seed):
    d=ImageDraw.Draw(img,"RGBA")
    b=entry["brand"];style=entry["style"];col=hx(entry["accent"])
    onwhite=(250,246,226,255)
    dark=(31,35,30,255)
    if b=="SCHWEFEL":
        d.rounded_rectangle((252,62,422,205),24,fill=(207,41,30,255),outline=(250,248,239,250),width=7)
        centered(d,"S",75,152,130,onwhite,"italic")
        centered(d,"SCHWEFEL",223,610,77,(167,21,23,255),"black")
    elif b=="AMIGOS":
        d.polygon([(0,0),(672,0),(672,235),(0,278)],fill=(239,118,32,230))
        centered(d,"AMIGOS",87,604,109,onwhite,"black")
        centered(d,"MARKT-KLASSIKER",224,605,31,dark)
    elif b=="LOOP":
        d.rounded_rectangle((78,78,593,238),radius=68,fill=(19,78,102,245))
        centered(d,"LOOP",105,497,104,(254,249,230,255),"black")
    elif b=="KERNELL":
        d.polygon([(62,58),(610,58),(558,258),(112,259)],fill=(47,39,24,235))
        centered(d,"KERNELL",91,535,91,onwhite,"black")
        centered(d,"CORN CRUNCH",203,520,30,(241,210,117,255))
    elif b=="STAXO":
        d.rounded_rectangle((75,85,597,273),55,fill=(30,45,139,245),outline=(250,246,218,240),width=8)
        centered(d,"STAXO",105,494,116,onwhite,"black")
    elif b=="POMPO":
        d.ellipse((133,60,537,278),fill=(244,224,91,250),outline=(255,247,201,200),width=6)
        centered(d,"POMPO",106,415,93,(85,28,51,255),"black")
    elif b=="ALPCRAFT":
        d.rounded_rectangle((58,61,614,253),8,fill=(26,32,29,240))
        centered(d,"ALPCRAFT",94,525,76,onwhite,"heavy")
        centered(d,"SWISS-STYLE POTATO CRISPS",203,515,24,(221,221,201,255))
    elif b=="ROOTIX":
        d.rounded_rectangle((90,66,582,257),70,fill=(46,93,67,245))
        centered(d,"ROOTIX",103,478,102,onwhite,"black")
        centered(d,"PLANT-BASED CRUNCH",217,454,25,onwhite)
    else:
        centered(d,b,90,580,91,onwhite)
    motif(img,style,col,seed)
    # Different packaging families use different flavour placement and text.
    flavor=entry["flavour"].upper()
    if style=="gourmet":
        centered(d,flavor,472,516,75,onwhite,kind="heavy")
    elif style=="stacked":
        centered(d,flavor,453,509,82,dark,kind="heavy")
    elif style=="puffed":
        centered(d,flavor,485,506,85,(79,32,42,255),kind="black")
    else:
        centered(d,flavor,469,580,82,(254,251,222,255),"black",
                 stroke=2,stroke_color=(43,42,34,240))
    chip_picture(img,seed+77, "tortilla" if entry["shape"]=="tortilla" else ("puffed" if style=="puffed" else "potato"))
    d=ImageDraw.Draw(img,"RGBA")
    d.rounded_rectangle((35,915,636,992),18,fill=(24,34,32,189))
    label(d,"FIKTIVE SPIELMARKE",55,936,375,26,(250,246,219,255),"regular")
    label(d,str(entry["weight_g"])+" g",507,931,110,42,(254,248,224,255))
    d.rectangle((0,0,W,19),fill=(211,170,68,130))
    d.rectangle((0,H-19,W,H),fill=(70,37,18,100))
    for y in list(range(6,44,8))+list(range(H-50,H-4,8)):
        d.line((0,y,672,y),fill=(254,250,222,45),width=2)
def make_back(entry,seed):
    im=colorbg(entry["accent"],seed+99,entry["style"])
    d=ImageDraw.Draw(im,"RGBA")
    b=entry["brand"]
    d.rounded_rectangle((65,77,607,277),radius=25,fill=(255,248,228,221))
    centered(d,b,113,505,83,(36,39,37,255))
    centered(d,entry["flavour"].upper(),210,478,38,(71,76,67,255))
    d.rounded_rectangle((55,333,619,477),radius=26,fill=(27,43,38,190))
    centered(d,"KNUSPRIG & FEIN",355,542,49,(250,246,222,255))
    centered(d,"FIKTIVES SPIELPRODUKT",427,535,22,(245,243,212,255))
    for j,t in enumerate([
        "Originalverpackung fuer ein Videospiel.",
        "Keine echte Zutaten- oder Naehrwertangabe.",
        "Gestaltung und Marke: fiktiv.",
        "Kann nach Belieben editiert werden.",
        "Swiss-themed game environment prop.",
    ]):
        label(d,t,62,530+j*49,540,26,(45,41,36,255),"regular")
    d.rounded_rectangle((53,818,619,948),radius=12,fill=(255,247,224,240))
    for j in range(34):
        x=75+j*14
        height=(65 if j%5==0 else 91 if j%3==0 else 75)
        if j%4!=0:d.rectangle((x,833,x+random.Random(seed*13+j).randint(2,7),833+height),fill=(32,34,31,255))
    label(d,"NOT A REAL BARCODE",91,926,420,17,(82,70,45,255),"regular")
    centered(d,str(entry["weight_g"])+" g",756,540,44,(48,42,35,255))
    return im
def make_normalmaps():
    # One shared, compact foil microdetail texture referenced by all GLBs.
    w=h=256
    img=Image.new("RGB",(w,h))
    p=img.load()
    rr=random.Random(2444)
    for y in range(h):
        for x in range(w):
            a=0.10*math.sin(x*.29+y*.18)+.07*math.sin(y*.47-x*.22)
            b=.11*math.cos(x*.37-y*.13)+.05*math.sin(y*.28)
            n=rr.randrange(-10,11)
            p[x,y]=(int(127+45*a+n*.25),int(127+45*b+n*.25),250)
    img.save(os.path.join(DEST,"_shared_foil_normal.png"),optimize=True)
    rough=Image.new("L",(w,h))
    p=rough.load()
    for y in range(h):
        for x in range(w):
            p[x,y]=max(35,min(230,int(80+16*math.sin(x*.08)+14*math.cos(y*.13)+rr.gauss(0,7))))
    rough.save(os.path.join(DEST,"_shared_foil_rough.png"),optimize=True)
def main():
    make_normalmaps()
    for i,entry in enumerate(DATA):
        seed=int(hashlib.sha256(entry["id"].encode()).hexdigest()[:8],16)
        im=colorbg(entry["accent"],seed,entry["style"])
        brand_art(im,entry,seed)
        front=os.path.join(DEST,entry["id"]+"_front.jpg")
        im.save(front,quality=87,subsampling=0,optimize=True)
        back=make_back(entry,seed)
        back.save(os.path.join(DEST,entry["id"]+"_back.jpg"),quality=83,subsampling=0,optimize=True)
        if i%10==0: print("TEXTURE",i+1,"/",len(DATA),entry["id"],flush=True)
    assert len(DATA)==88
    print("DONE",len(DATA),"custom front & back printed artworks",flush=True)
if __name__=="__main__":main()
