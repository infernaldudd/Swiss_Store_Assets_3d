"""Original fictional Swiss supermarket cup-noodle packaging art.

Generate 8 complete cups plus a premium HERO opening. No outside logos,
photographs, licensed package graphics or pre-made textures are used.
Usage: /usr/bin/python3 tools/generate_noodle_cup_textures.py
"""
import os, math, random, json, hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"textures","noodle_cups")
os.makedirs(OUT,exist_ok=True)

PRODUCTS=[
 dict(id="LOOP_Chicken_Instant_Noodles",brand="LOOP",flavor="CHICKEN",subtitle="Poulet / Huhn",color="#e7ba38",accent="#155f6e",size=65,family="loop"),
 dict(id="LOOP_Beef_Instant_Noodles",brand="LOOP",flavor="BEEF",subtitle="Rind / Boeuf",color="#bb452d",accent="#185569",size=65,family="loop"),
 dict(id="LOOP_Curry_Instant_Noodles",brand="LOOP",flavor="CURRY",subtitle="Curry / Gewuerzt",color="#d48419",accent="#18576d",size=65,family="loop"),
 dict(id="AMIGOS_Spicy_Chicken_Noodles",brand="AMIGOS",flavor="SPICY CHICKEN",subtitle="Scharfes Poulet",color="#dc412f",accent="#54252c",size=70,family="amigos"),
 dict(id="AMIGOS_Vegetable_Noodles",brand="AMIGOS",flavor="VEGETABLE",subtitle="Gemuese / Legumes",color="#50985b",accent="#244f36",size=70,family="amigos"),
 dict(id="AMIGOS_Hot_Curry_Noodles",brand="AMIGOS",flavor="HOT CURRY",subtitle="Scharfer Curry",color="#bf4727",accent="#533524",size=70,family="amigos"),
 dict(id="SparFix_Budget_Noodles",brand="SPARFIX",flavor="ORIGINAL",subtitle="Guenstiger Nudelbecher",color="#e6bc55",accent="#326db1",size=65,family="budget"),
 dict(id="ALP_Ramen_Extra_Hot",brand="ALP RAMEN",flavor="FIRE & CHILI",subtitle="Extra Hot / Intense",color="#2a252c",accent="#df4431",size=85,family="premium")
]

def font(size,style="heavy"):
    paths={
       "heavy":["/usr/share/fonts/truetype/lato/Lato-Heavy.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
       "black":["/usr/share/fonts/truetype/lato/Lato-Black.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
       "regular":["/usr/share/fonts/truetype/lato/Lato-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
       "italic":["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf"]
    }
    for path in paths[style]:
        if os.path.exists(path): return ImageFont.truetype(path,size)
    return ImageFont.load_default()

def hx(s):return tuple(int(s[i:i+2],16) for i in (1,3,5))
def blend(a,b,t):return tuple(int((1-t)*a[i]+t*b[i]) for i in range(3))

def centered(d,string,cy,width,px,color,style="black",anchor_x=768):
    while px>=12:
        ft=font(px,style)
        bbox=d.textbbox((0,0),string,font=ft)
        if bbox[2]-bbox[0]<=width:break
        px-=2
    x=int(anchor_x-(bbox[2]-bbox[0])/2-bbox[0])
    y=int(cy-(bbox[3]-bbox[1])/2-bbox[1])
    d.text((x,y),string,font=ft,fill=color)

def noodle_illustration(im, cx,cy, seed, scale=1.0):
    # Handmade original illustration of broth, spiral noodles, garnish and steam.
    rr=random.Random(seed)
    overlay=Image.new("RGBA",im.size,(0,0,0,0))
    d=ImageDraw.Draw(overlay,"RGBA")
    rx=int(254*scale); ry=int(123*scale)
    d.ellipse((cx-rx+12,cy-ry+24,cx+rx+19,cy+ry+31),fill=(17,18,21,118))
    d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),fill=(248,245,225,255))
    d.ellipse((cx-rx+17,cy-ry+16,cx+rx-17,cy+ry-17),fill=(145,63,30,250))
    d.ellipse((cx-rx+30,cy-ry+25,cx+rx-30,cy+ry-31),fill=(196,102,51,245))
    for j in range(24):
        phi=rr.uniform(-.3,math.pi+.5)
        ox=rr.randrange(-145,145)*scale
        oy=rr.randrange(-50,60)*scale
        points=[]
        for i in range(32):
            t=i/31*math.tau*rr.uniform(1.0,1.5)
            x=cx+ox+(21+i*.65)*scale*math.cos(t+phi)
            y=cy+oy+(11+i*.38)*scale*math.sin(t+phi)
            points.append((int(x),int(y)))
        d.line(points,fill=(89,54,21,150),width=max(2,int(11*scale)),joint="curve")
        d.line([(x,y-2) for x,y in points],fill=(247,211,111,245),width=max(2,int(8*scale)),joint="curve")
    # Garnish cut vegetables and realistic green onion slices.
    for j in range(30):
        x=int(cx+rr.randrange(-195,196)*scale)
        y=int(cy+rr.randrange(-62,65)*scale)
        r=rr.randrange(4,10)*scale
        fill=rr.choice([(76,134,54,250),(110,161,67,255),(211,55,30,255),(233,139,42,250)])
        d.ellipse((x-r,y-r/2,x+r,y+r/2),fill=fill)
    for a in [-90,0,92]:
        x=cx+a*scale
        d.arc((x-30*scale,cy-250*scale,x+25*scale,cy-125*scale),10,170,fill=(246,240,222,130),width=max(2,int(7*scale)))
    im.alpha_composite(overlay)

def background(w,h,col,seed):
    rr=np.random.default_rng(seed)
    base=np.array(col,dtype=np.float32)
    y,x=np.mgrid[:h,:w].astype(np.float32)
    t=.05+.12*np.sin(y/h*math.pi)**2+.06*np.cos(x/w*math.tau*2)
    wave=5.3*np.sin(x*.023+y*.008)+3.2*np.sin(y*.03-x*.01)
    noise=rr.normal(0,1.9,(h,w))
    ar=np.clip(base[None,None,:]*(1-t[:,:,None])+
             np.array((9,13,16))[None,None,:]*t[:,:,None]+(wave+noise)[:,:,None],0,255)
    return Image.fromarray(np.uint8(ar),"RGB").convert("RGBA")

def wrap_art(p):
    w,h=1536,1024
    seed=int(hashlib.sha1(p["id"].encode()).hexdigest()[:8],16)
    base=hx(p["color"]); accent=hx(p["accent"])
    im=background(w,h,base,seed)
    d=ImageDraw.Draw(im,"RGBA")
    # Artwork front occupies the central 60% of the cylindrical sleeve; the
    # wrap seams, ingredient paragraph and mock information sit at the rear.
    # Horizontal image u=.5 corresponds to front-facing world -Y.
    if p["family"]=="loop":
        d.rounded_rectangle((404,68,1132,296),radius=65,fill=(*accent,249),
                            outline=(247,248,222,220),width=8)
        centered(d,"LOOP",185,620,158,(255,250,230,255),anchor_x=768)
        d.polygon([(215,347),(1318,290),(1318,414),(215,465)],fill=(250,235,162,205))
    elif p["family"]=="amigos":
        d.polygon([(352,50),(1177,50),(1200,291),(341,308)],fill=(236,113,31,245))
        centered(d,"AMIGOS",184,735,125,(255,250,231,255),anchor_x=768)
        d.rounded_rectangle((410,353,1120,462),radius=36,fill=(43,40,35,165))
    elif p["family"]=="budget":
        d.rounded_rectangle((359,70,1177,290),radius=27,fill=(243,248,243,250))
        centered(d,"SPARFIX",172,737,125,(29,99,177,255),anchor_x=768)
        d.line((400,324,1130,324),fill=(248,242,215,229),width=18)
    else:
        d.polygon([(325,54),(1184,54),(1100,323),(399,323)],fill=(20,22,28,255))
        centered(d,"ALP RAMEN",174,739,110,(249,248,232,255),anchor_x=768)
        d.line((400,334,1139,334),fill=(229,51,44,248),width=22)
    centered(d,"INSTANT NOODLES",385,800,52,(253,248,221,255),anchor_x=768)
    centered(d,p["flavor"],466,950,100,(255,247,224,255),anchor_x=768)
    centered(d,p["subtitle"],549,760,43,(248,245,226,246),style="regular",anchor_x=768)
    noodle_illustration(im,768,765,seed,.86)
    d=ImageDraw.Draw(im,"RGBA")
    d.rounded_rectangle((1117,852,1294,949),radius=22,fill=(22,31,29,208))
    d.text((1133,865),str(p["size"])+" g",font=font(46),fill=(255,246,215,255))
    d.rounded_rectangle((338,934,1090,991),radius=17,fill=(33,43,42,192))
    centered(d,"FIKTIVE SPIELMARKE · GAME PROP",961,720,26,(250,246,215,255),style="regular",anchor_x=716)
    # Reverse: replacement information, small decorative icons and seams.
    d.rounded_rectangle((34,100,286,879),radius=18,fill=(246,242,220,219))
    d.text((51,135),"ZUBEREITUNG",font=font(27),fill=(43,43,40,255))
    for i,row in enumerate(["1. Deckel oeffnen","2. Wasser dazu","3. 3 Min. ziehen","4. Geniessen!","", "KEIN ECHTES", "LEBENSMITTEL"]):
        d.text((54,210+i*75),row,font=font(19 if len(row)>14 else 23,"regular"),fill=(56,52,44,255))
    d.rounded_rectangle((1314,115,1509,915),radius=17,fill=(247,243,225,222))
    for i,line in enumerate(["SWISS","STORE","PROP","",p["brand"],"NOODLES","",str(p["size"])+" g","","ORIGINAL","ARTWORK","","NOT FOR","SALE"]):
        d.text((1330,141+i*48),line,font=font(21),fill=(52,49,38,255))
    d.line((12,0,12,h),fill=(225,229,200,220),width=11)
    d.line((w-12,0,w-12,h),fill=(47,45,38,110),width=12)
    d.rectangle((0,h-31,w,h),fill=(31,36,33,180))
    out=os.path.join(OUT,p["id"]+"_Wrap.png")
    im.convert("RGB").save(out,optimize=True)
    return out

def lid_art(p):
    size=768
    seed=int(hashlib.md5(p["id"].encode()).hexdigest()[:8],16)
    bg=hx(p["color"])
    im=background(size,size,bg,seed)
    d=ImageDraw.Draw(im,"RGBA")
    d.ellipse((15,15,752,752),outline=(250,249,230,235),width=21)
    d.ellipse((56,56,710,710),outline=(31,38,36,149),width=9)
    d.rounded_rectangle((126,157,640,294),radius=50,fill=(*hx(p["accent"]),220))
    centered(d,p["brand"],232,474,70,(250,250,233,255),anchor_x=384)
    centered(d,p["flavor"],362,520,70,(249,246,225,255),anchor_x=384)
    centered(d,"NOODLE CUP",466,500,44,(255,251,232,255),anchor_x=384)
    centered(d,"OPEN HERE",585,430,35,(45,48,42,255),anchor_x=384)
    d.polygon([(363,662),(405,662),(384,719)],fill=(33,33,33,219))
    d.arc((91,95,681,681),195,340,fill=(250,241,213,100),width=4)
    out=os.path.join(OUT,p["id"]+"_Lid.png")
    im.convert("RGB").save(out,optimize=True)
    return out

def make_material_maps():
    size=512
    rr=np.random.default_rng(448)
    y,x=np.mgrid[:size,:size]
    height=(np.sin(x*.091+y*.075)*.055+np.sin(x*.37-y*.19)*.029+
            rr.normal(0,.018,(size,size)))
    gy,gx=np.gradient(height)
    nx=-gx*1.5;ny=-gy*1.5
    nz=np.sqrt(np.clip(1-nx*nx-ny*ny,.05,1))
    out=np.uint8(np.clip(np.stack([(nx+1)*127.5,(ny+1)*127.5,(nz+1)*127.5],axis=2),0,255))
    Image.fromarray(out,"RGB").save(os.path.join(OUT,"_Shared_Paper_Normal.png"),optimize=True)
    rough=np.uint8(np.clip(.78*255+18*np.sin(y*.06)+rr.normal(0,9,(size,size)),0,255))
    Image.fromarray(rough,"L").save(os.path.join(OUT,"_Shared_Paper_Roughness.png"),optimize=True)

if __name__=="__main__":
    make_material_maps()
    for i,p in enumerate(PRODUCTS):
        wrap_art(p);lid_art(p)
        print("ART",i+1,"/",len(PRODUCTS),p["id"],flush=True)
    catalog={"collection":"Swiss Noodle Cups · fictional in-game supermarkets",
             "all_fictional":True,"count_closed":8,"count_hero_open":1,
             "units":"meters","products":PRODUCTS}
    with open(os.path.join(ROOT,"catalog","noodle_cups.json"),"w",encoding="utf-8") as f:
        json.dump(catalog,f,indent=2,ensure_ascii=False)
    print("DONE: Eight wraps, eight lid prints, shared material maps and catalog",flush=True)
