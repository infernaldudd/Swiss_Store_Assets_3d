"""Generate 18 original 2K labels for fictional Swiss supermarket food tins.

No trademark logos, photographs, copied retail designs, or third-party
product artwork. Pillow+NumPy; system Python:
 /usr/bin/python3 tools/generate_canned_food_labels.py
"""
import os, json, math, random, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"textures","canned_food")
os.makedirs(OUT,exist_ok=True)
DATA=json.load(open(os.path.join(ROOT,"catalog","canned_food.json"),encoding="utf-8"))
W,H=2048,1024

def ft(sz,style="bold"):
    paths={
      "bold":["/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
      "black":["/usr/share/fonts/truetype/lato/Lato-Black.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
      "regular":["/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
      "italic":["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf"]
    }
    for p in paths[style]:
        if os.path.isfile(p):return ImageFont.truetype(p,max(9,int(sz)))
    return ImageFont.load_default()
def hexrgb(s):return tuple(int(s[k:k+2],16) for k in (1,3,5))
def center(d,s,x,y,maxw,fontsize,color,style="bold"):
    while fontsize>15:
        f=ft(fontsize,style)
        b=d.textbbox((0,0),s,font=f)
        if b[2]-b[0]<=maxw:break
        fontsize-=2
    cx=x-(b[2]+b[0])/2
    cy=y-(b[3]+b[1])/2
    d.text((round(cx),round(cy)),s,font=f,fill=color)
def bg(col,seed,style):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    base=np.array(col,dtype=np.float32)
    r=np.random.default_rng(seed)
    v=.08+.14*np.sin(xx/W*math.pi)**2 + .09*(yy/H)
    grain=(3.7*np.sin(xx*.03+yy*.006)+2.4*np.sin(yy*.052-xx*.01)+
           r.normal(0,2.0,(H,W)))
    c=np.clip(base[None,None,:]*(1-v[:,:,None])+
              (grain[:,:,None]),0,255)
    return Image.fromarray(c.astype(np.uint8),"RGB").convert("RGBA")
def draw_food(img,kind,seed):
    # Entire illustration is original drawn geometry, not a photograph.
    rr=random.Random(seed)
    d=ImageDraw.Draw(img,"RGBA")
    cx,cy=1024,729
    # a softly shaded dark dish provides consistent food-photo-like structure
    d.ellipse((661,543,1387,929),fill=(25,23,17,82))
    d.ellipse((681,525,1367,907),fill=(250,237,208,235))
    d.ellipse((707,543,1341,883),fill=(91,52,28,240))
    d.ellipse((725,554,1324,862),fill=(155,83,42,250) if kind in ("ravioli","soup","beans","lentils") else (199,174,113,244))
    recipes={
      "ravioli":((225,169,96),(201,93,38),32),
      "tomato":((215,47,32),(248,112,53),21),
      "corn":((242,190,54),(250,225,105),95),
      "peas":((93,156,57),(166,196,72),88),
      "beans":((122,42,43),(194,85,59),56),
      "coconut":((245,231,192),(242,248,235),35),
      "chickpea":((204,171,112),(237,208,154),76),
      "mushroom":((144,118,83),(198,172,117),39),
      "soup":((210,61,34),(238,121,48),25),
      "peach":((244,160,73),(255,199,103),20),
      "pineapple":((246,206,57),(254,230,109),21),
      "vegetables":((102,165,77),(228,184,74),98),
      "tuna":((175,157,128),(225,201,167),52),
      "lentils":((157,111,62),(201,150,78),135),
      "apricot":((241,147,55),(255,190,69),22)
    }
    primary,highlight,n=recipes.get(kind,recipes["vegetables"])
    for k in range(n):
        ang=rr.random()*math.tau
        radius=math.sqrt(rr.random())
        x=cx+rr.uniform(1,269)*radius*math.cos(ang)
        y=cy+rr.uniform(1,125)*radius*math.sin(ang)
        diameter=rr.uniform(17,41) if n<60 else rr.uniform(7,19)
        if kind=="ravioli":
            diameter=rr.uniform(26,43)
            d.rounded_rectangle((x-diameter,y-diameter*.65,x+diameter,y+diameter*.65),
                       radius=6,fill=primary,outline=(249,217,140,229),width=4)
            d.rounded_rectangle((x-diameter*.64,y-diameter*.36,
                                 x+diameter*.64,y+diameter*.36),
                       radius=6,outline=(150,109,58,124),width=2)
        elif kind in ("peach","apricot"):
            d.pieslice((x-diameter,y-diameter*.78,x+diameter,y+diameter*.78),
                       15,350,fill=primary)
            d.arc((x-diameter*.9,y-diameter*.6,x+diameter*.4,y+diameter*.7),
                  25,188,fill=highlight,width=5)
        elif kind=="pineapple":
            rr2=diameter*1.23
            d.ellipse((x-rr2,y-diameter,x+rr2,y+diameter),fill=primary,outline=highlight,width=5)
            d.ellipse((x-diameter*.32,y-diameter*.28,x+diameter*.32,y+diameter*.28),
                      fill=(184,123,44,225))
        elif kind=="mushroom":
            d.pieslice((x-diameter,y-diameter*.65,x+diameter,y+diameter*.65),
                       180,360,fill=primary)
            d.rounded_rectangle((x-5,y,x+5,y+16),radius=3,fill=highlight)
        elif kind=="tuna":
            points=[(x+math.cos(t)*diameter*rr.uniform(.6,1.1),
                     y+math.sin(t)*diameter*.38*rr.uniform(.6,1.1))
                    for t in (0,math.pi*.36,math.pi*.72,math.pi*1.12,math.pi*1.6)]
            d.polygon(points,fill=primary)
            d.line(points[:3],fill=highlight,width=5)
        elif kind in ("tomato","soup"):
            d.ellipse((x-diameter,y-diameter*.75,x+diameter,y+diameter*.75),
                      fill=primary,outline=(150,55,28,155),width=3)
            d.arc((x-diameter*.7,y-diameter*.5,x+diameter*.2,y+diameter*.2),
                  200,315,fill=highlight,width=5)
        elif kind=="coconut":
            d.ellipse((x-diameter,y-diameter*.42,x+diameter,y+diameter*.42),fill=primary,outline=highlight,width=3)
        else:
            d.ellipse((x-diameter*.62,y-diameter*.52,x+diameter*.62,y+diameter*.52),
                      fill=primary,outline=highlight,width=3)
    # Deliberately restrained garnish: the printed images should read as foods.
    for i in range(23):
        a=rr.random()*math.tau; r=rr.uniform(28,275)
        x=cx+r*math.cos(a);y=cy+r*.48*math.sin(a)
        d.ellipse((x-6,y-3,x+6,y+3),fill=(51,123,52,210))
    d.arc((697,539,1342,884),185,346,fill=(255,251,224,137),width=10)

def art(p):
    seed=int(hashlib.sha256(p["id"].encode("utf8")).hexdigest()[:8],16)
    c=hexrgb(p["color"])
    img=bg(c,seed,p["brand"])
    d=ImageDraw.Draw(img,"RGBA")
    brand=p["brand"].upper()
    if brand=="LOOP":
        d.rounded_rectangle((590,34,1458,205),radius=80,fill=(22,91,112,245),
                            outline=(248,241,211,240),width=11)
        center(d,"LOOP",1024,118,700,114,(251,247,228,255),"black")
        d.polygon([(540,241),(1508,195),(1508,269),(540,300)],fill=(249,243,212,200))
    elif brand=="AMIGOS":
        d.polygon([(522,30),(1550,30),(1490,227),(583,227)],fill=(235,119,37,245))
        center(d,"AMIGOS",1024,129,890,115,(255,249,228,255),"black")
        d.line((585,252,1475,252),fill=(246,231,201,200),width=13)
    elif brand=="SPARFIX":
        d.rounded_rectangle((584,43,1466,225),radius=22,fill=(244,247,232,252))
        center(d,"SPARFIX",1024,133,800,119,(24,100,174,255),"black")
    else:
        d.rounded_rectangle((527,44,1518,223),radius=14,fill=(33,48,44,245))
        center(d,"ALP PANTRY",1024,126,925,106,(249,248,223,255),"black")
    d.rounded_rectangle((555,326,1490,487),radius=18,fill=(245,241,217,229))
    flavor=p["flavour"].upper()
    center(d,flavor,1024,402,857,99,(42,48,39,255),"black")
    draw_food(img,p["food"],seed)
    d=ImageDraw.Draw(img,"RGBA")
    d.rounded_rectangle((1187,915,1427,993),radius=19,fill=(29,36,35,218))
    center(d,str(p["weight_g"])+(" ml" if p["food"]=="coconut" else " g"),
           1307,950,225,45,(247,243,222,255))
    center(d,"FIKTIVES SPIELPRODUKT",1024,979,630,30,(246,239,221,235),"regular")
    d.rectangle((0,0,W,21),fill=(28,32,28,144))
    d.rectangle((0,1001,W,H),fill=(29,33,27,151))
    # Rear-print information stays away from hero front region (u≈0.5).
    d.rounded_rectangle((42,109,460,948),radius=17,fill=(250,245,220,227))
    rear=["SWISS STORE", "CANNED GOODS","",brand,"",flavor[:22],
          "", "FIKTIVES PRODUKT", "KEIN LEBENSMITTEL",
          "KEINE NAEHRWERTE", "INHALT: SPIELASSET", "",
          "LABEL: ORIGINAL", "", "HELVETIA / BASEL"]
    y=135
    for txt in rear:
        if txt:
            f=ft(23 if len(txt)>16 else 28,"regular")
            d.text((69,y),txt,font=f,fill=(56,51,40,253))
        y+=48
    d.rounded_rectangle((1607,104,2009,948),radius=15,fill=(250,244,223,223))
    for j,l in enumerate(("SWISS STYLE","PANTRY","FOOD TIN","","","INGREDIENT","ILLUSTRATION","FICTIONAL","",str(p["weight_g"])+" g")):
        d.text((1644,133+j*66),l,font=ft(30 if len(l)<14 else 24),fill=(53,48,37,250))
    # Not a functional scannable barcode; game shelf dressing.
    rr=random.Random(seed+32)
    x=1637
    for i in range(47):
        thickness=rr.choice((2,3,5,7))
        d.rectangle((x,817,x+thickness,897),fill=(35,31,27,200))
        x+=thickness+rr.choice((3,4,6))
        if x>1972:break
    path=os.path.join(OUT,p["id"]+"_wrap_2K.png")
    img.convert("RGB").save(path,optimize=True)
    print("LABEL",os.path.basename(path),os.path.getsize(path),flush=True)

def metal_normal():
    size=512
    y,x=np.mgrid[:size,:size].astype(np.float32)
    rr=np.random.default_rng(17353)
    f=(.11*np.sin(x*.11+y*.07)+.067*np.sin(x*.41-y*.31)+
       rr.normal(0,.03,(size,size)))
    gy,gx=np.gradient(f)
    nx=np.clip(-gx*.25,-.3,.3)
    ny=np.clip(-gy*.25,-.3,.3)
    nz=np.sqrt(np.maximum(.01,1-nx*nx-ny*ny))
    norm=np.stack([127.5*(nx+1),127.5*(ny+1),127.5*(nz+1)],axis=-1)
    Image.fromarray(np.uint8(np.clip(norm,0,255)),"RGB").save(
        os.path.join(OUT,"_Shared_Fine_Metal_Normal.png"),optimize=True)
    rough=np.uint8(np.clip(255*(.23+.022*np.sin(x*.025)+.014*np.cos(y*.04))+
                          rr.normal(0,4,(size,size)),0,255))
    Image.fromarray(rough,"L").save(os.path.join(OUT,"_Shared_Steel_Roughness.png"),optimize=True)
    paper=np.uint8(np.clip(255*(.72+.03*np.sin(y*.054)+.02*np.sin(x*.019))+
                          rr.normal(0,7,(size,size)),0,255))
    Image.fromarray(paper,"L").save(os.path.join(OUT,"_Shared_Label_Paper_Roughness.png"),optimize=True)

if __name__=="__main__":
    metal_normal()
    for item in DATA["items"]:art(item)
    assert len(DATA["items"])==18
    print("FINISHED 18 unique 2K labels and three PBR detail maps",flush=True)
