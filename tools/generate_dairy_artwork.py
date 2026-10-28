"""Original, fictional Swiss dairy SKU artwork for all 100 distinct products.
No trademarked third-party logo or packaging art. Each product gets a unique
1024x768 printed label, UV mapped onto its individual 3D package.
Requires Pillow + NumPy: /usr/bin/python3 tools/generate_dairy_artwork.py
"""
import os,json,math,hashlib,random
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
CAT=json.load(open(os.path.join(ROOT,"catalog","dairy_100.json"),encoding="utf-8"))
OUT=os.path.join(ROOT,"textures","dairy_100")
PREV=os.path.join(ROOT,"previews","dairy_100")
for p in (OUT,PREV):os.makedirs(p,exist_ok=True)
W,H=1024,768
def rgb(h):return tuple(int(h[k:k+2],16) for k in (1,3,5))
def ft(sz,kind="bold"):
    opts={
      "bold":["/usr/share/fonts/truetype/lato/Lato-Heavy.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
      "black":["/usr/share/fonts/truetype/lato/Lato-Black.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
      "normal":["/usr/share/fonts/truetype/lato/Lato-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    }
    for p in opts[kind]:
        if os.path.exists(p):return ImageFont.truetype(p,max(9,int(sz)))
    return ImageFont.load_default()
def type_center(d,s,cy,width,sz,color,kind="bold",xc=512):
    while sz>12:
        f=ft(sz,kind);box=d.textbbox((0,0),s,font=f)
        if box[2]-box[0]<=width:break
        sz-=2
    d.text((round(xc-(box[2]+box[0])/2),round(cy-(box[3]+box[1])/2)),
           s,font=f,fill=color)
def background(col,seed):
    base=np.array(col,dtype=np.float32)
    rng=np.random.default_rng(seed)
    y,x=np.mgrid[:H,:W].astype(np.float32)
    v=.08+.12*(x/W)+.055*np.sin(y*.016+x*.008)+.04*np.sin(y*.039-x*.019)
    a=base[None,None,:]*(1-v[:,:,None])+np.array([251,248,231],dtype=np.float32)[None,None,:]*v[:,:,None]*.23
    a+=rng.normal(0,2.2,(H,W))[:,:,None]
    return Image.fromarray(np.uint8(np.clip(a,0,255)),"RGB")
def logo(d,p):
    b=p["brand"].upper()
    if b=="LOOP":
        d.rounded_rectangle((275,34,747,180),radius=63,fill=(27,98,114),outline=(253,251,230),width=6)
        type_center(d,"LOOP",109,420,97,(255,250,228))
    elif b=="AMIGOS":
        d.polygon([(257,24),(772,24),(736,178),(291,178)],fill=(228,115,40))
        type_center(d,"AMIGOS",106,456,86,(255,252,226),"black")
    elif b=="SPARFIX":
        d.rounded_rectangle((274,32,750,176),radius=18,fill=(251,248,232))
        type_center(d,"SPARFIX",104,450,84,(39,108,165),"black")
    else:
        d.rounded_rectangle((248,34,777,182),radius=13,fill=(36,62,60))
        type_center(d,"ALP FARM",107,479,83,(252,249,228),"black")
def icons(im,p,seed):
    d=ImageDraw.Draw(im,"RGBA");rr=random.Random(seed)
    name=p["name"].lower()
    x=512;y=550
    # Bespoke but restrained illustration families; not reused identical art.
    if p["shape"] in ("carton","bottle") or "milch" in name or "rahm" in name:
        d.polygon([(220,617),(348,516),(438,585),(539,452),(701,587),(809,525),
                   (860,675),(172,675)],fill=(243,251,242,155))
        d.polygon([(220,618),(348,517),(438,586),(539,454),(701,588),(809,525),
                   (860,678),(780,676),(698,628),(538,528),(435,633),(351,575),(252,682)],
                  fill=(245,251,250,190))
        for k in range(10):
            xx=rr.randrange(213,830);yy=rr.randrange(598,712)
            d.arc((xx-45,yy-15,xx+45,yy+18),190,355,fill=(220,244,249,150),width=3)
        if "schoko" in name or "coffee" in name or "mocca" in name:
            for k in range(32):
                xx=rr.randrange(270,750);yy=rr.randrange(566,704)
                d.ellipse((xx,yy,xx+rr.randrange(4,14),yy+8),fill=(94,52,33,150))
    elif p["shape"] in ("wedge","round","tray","pouch") and ("käse" in name or "mozz" in name or "brie" in name or "feta" in name or "burrata" in name):
        d.ellipse((272,531,767,721),fill=(55,47,33,65))
        d.polygon([(334,682),(665,676),(716,559),(525,492)],fill=(246,220,142,244))
        d.polygon([(334,682),(525,492),(525,657)],fill=(231,188,106,255))
        d.polygon([(525,492),(716,559),(665,676),(525,657)],fill=(255,231,169,244))
        for _ in range(24):
            xx=rr.randint(541,664);yy=rr.randint(557,652);r=rr.randint(2,11)
            d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(174,127,63,100))
    elif p["shape"]=="brick":
        d.rounded_rectangle((282,536,728,681),radius=28,fill=(253,227,123,245),outline=(244,241,194,255),width=8)
        d.arc((339,568,677,646),190,330,fill=(255,251,203,230),width=14)
    else:
        d.ellipse((284,503,746,713),fill=(250,249,241,237))
        d.ellipse((304,516,727,690),fill=(243,235,218,237))
        name=p["name"].lower()
        if any(s in name for s in ("erdbeer","himbeer","beeren","kirsche","strawberry")): cc=(208,63,103)
        elif any(s in name for s in ("mango","aprikos","pfirsich","caramel")):cc=(227,145,54)
        elif any(s in name for s in ("heidelbeer","blaubeer")):cc=(109,77,157)
        elif any(s in name for s in ("schoko","mocca","tiramisu","zimt")):cc=(112,63,46)
        elif any(s in name for s in ("limette","zitrone","vanille")):cc=(207,196,89)
        else:cc=(178,203,168)
        for k in range(27):
            xx=rr.randrange(342,676);yy=rr.randrange(557,648)
            r=rr.randrange(7,23)
            d.ellipse((xx-r,yy-r*.52,xx+r,yy+r*.52),fill=(*cc,rr.randrange(80,185)))
        d.arc((310,526,713,685),175,342,fill=(255,251,235,177),width=8)
def draw(p):
    seed=int(hashlib.sha256(p["id"].encode("utf8")).hexdigest()[:8],16)
    bg=background(rgb(p["color"]),seed)
    d=ImageDraw.Draw(bg,"RGBA")
    logo(d,p)
    d.polygon([(0,205),(1024,191),(1024,307),(0,312)],fill=(249,247,229,216))
    type_center(d,p["name"].upper(),260,910,84,(32,40,41,255),"black")
    type_center(d,p["brand"].upper()+"  /  SWISS DAIRY",380,815,30,(252,249,235,255))
    icons(bg,p,seed)
    d=ImageDraw.Draw(bg,"RGBA")
    d.rounded_rectangle((766,665,981,733),radius=17,fill=(31,42,40,215))
    unit="ml" if p["shape"] in ("carton","bottle","spray") else "g"
    type_center(d,str(p["net"])+" "+unit,703,202,41,(253,249,220,255),xc=870)
    d.text((23,718),"FIKTIVE SPIELMARKE  •  HELVETIA",font=ft(20,"normal"),fill=(255,249,227,255))
    output=os.path.join(OUT,p["id"]+".jpg")
    bg.save(output,quality=90,subsampling=0,optimize=True)
    return output

all_items=[]
for batch in CAT["batches"]:
    all_items.extend(batch["products"])
assert len(all_items)==100 and len(set(p["id"] for p in all_items))==100
for i,p in enumerate(all_items):
    draw(p)
    if i%10==0:print("LABEL",i+1,"/",len(all_items),p["id"],flush=True)

# Contact sheets are designed as shelf planning reference, not substitutes for 3D previews.
for batch in CAT["batches"]:
    sheet=Image.new("RGB",(5*256+40,4*235+106),(234,237,233))
    d=ImageDraw.Draw(sheet)
    d.text((24,12),batch["name"].replace("_"," ").upper()+" | 20 DISTINCT PRODUCTS",
           font=ft(33),fill=(26,36,33))
    for i,p in enumerate(batch["products"]):
        x=22+i%5*256;y=76+i//5*235
        im=Image.open(os.path.join(OUT,p["id"]+".jpg"))
        im.thumbnail((226,168),Image.Resampling.LANCZOS)
        sheet.paste(im,(x+7,y))
        title=p["name"][:23]
        d.text((x+6,y+176),title,font=ft(17),fill=(34,38,34))
        d.text((x+6,y+198),p["shape"]+" | "+str(p["net"]),font=ft(15,"normal"),fill=(60,65,60))
    path=os.path.join(PREV,batch["name"]+"_All_20.jpg")
    sheet.save(path,quality=88,optimize=True)
    print("SHEET",batch["name"],os.path.getsize(path),flush=True)
print("DONE: 100 unique label textures, 5 complete assortment sheets",flush=True)
