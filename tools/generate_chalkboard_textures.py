"""Generate ORIGINAL PBR oak and readable chalk artwork for a 3D A-frame café board.

Run with system Python: python3 tools/generate_chalkboard_textures.py
No externally licensed textures, logos, or fonts are distributed.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os, random
random.seed(24471)
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"textures","aframe")
os.makedirs(OUT,exist_ok=True)

def font(size,serif=False):
    opts=(["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"] if serif else
          ["/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
    for p in opts:
        if os.path.exists(p):return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def canvas_board(seed):
    rng=random.Random(seed)
    im=Image.new("RGB",(1024,1408))
    px=im.load()
    for y in range(1408):
        for x in range(1024):
            v=rng.gauss(0,1.45) + 2.8*math.sin(x*.024+y*.008) + 1.7*math.sin(x*.003)
            shade=int(max(0,min(255, 22+v)))
            px[x,y]=(shade+1,shade+4,shade+4)
    d=ImageDraw.Draw(im,"RGBA")
    for i in range(3600):
        x=rng.randrange(1024); y=rng.randrange(1408)
        val=rng.randrange(70,145)
        d.point((x,y),fill=(val,val,val,rng.randrange(12,48)))
    # Faint pre-existing wipe marks add photographic use / chalk dust.
    for j in range(12):
        x=rng.randrange(25,980);y=rng.randrange(35,1380)
        d.arc((x-75,y-21,x+75,y+21),0,160,fill=(166,168,161,14),width=rng.randint(2,9))
    return im

def txt(d,phrase,cy,maxwidth,height,fill=(236,230,210,250),center=512,serif=False,stroke=0):
    point=height
    while point>16:
        ft=font(point,serif)
        bounds=d.textbbox((0,0),phrase,font=ft,stroke_width=stroke)
        if bounds[2]-bounds[0]<=maxwidth:break
        point-=2
    x=center-(bounds[2]-bounds[0])/2-bounds[0]
    y=cy-(bounds[3]-bounds[1])/2-bounds[1]
    d.text((round(x),round(y)),phrase,font=ft,fill=fill,stroke_width=stroke,stroke_fill=fill)
    return bounds[2]-bounds[0]

def line(d,x1,y1,x2,y2,c=(222,218,203,230),width=4):
    d.line((x1,y1,x2,y2),fill=c,width=width,joint="curve")

def star(d,x,y,r,color=(224,224,201,205)):
    line(d,x-r,y,x+r,y,color,3)
    line(d,x,y-r,x,y+r,color,3)
    line(d,x-r*.58,y-r*.58,x+r*.58,y+r*.58,color,2)

def decorate(im,label):
    d=ImageDraw.Draw(im,"RGBA")
    cream=(232,224,206,246)
    gray=(183,196,196,231)
    muted=(173,160,142,230)
    # Graphic layout knowingly differs between the two reference photos.
    line(d,76,79,948,79,muted,3)
    line(d,76,1320,948,1320,muted,3)
    for c in (90,936):
        star(d,c,114,9,gray)
        star(d,c,1285,9,gray)
    if label=="LUNCH":
        txt(d,"LOOP  BISTRO",149,730,51,cream)
        line(d,289,201,735,201,muted,2)
        txt(d,"LUNCH",315,840,149,cream)
        txt(d,"10:30 - 15:00",428,800,69,gray)
        line(d,220,510,804,510,gray,3)
        txt(d,"TODAY'S SPECIALS",577,840,45,cream)
        txt(d,"SOUP  &  BREAD",715,810,58,gray)
        txt(d,"CHF  12.50",775,780,41,muted)
        line(d,230,834,794,834,muted,2)
        txt(d,"GARDEN SALAD",912,785,57,gray)
        txt(d,"CHF  15.00",973,780,41,muted)
        for x in (300,724):
            star(d,x,1070,19,cream)
        txt(d,"FRESH  -  LOCAL  -  HOMEMADE",1181,830,31,cream)
    else:
        txt(d,"AMIGOS   CAFE",158,770,49,cream)
        txt(d,"we are",285,700,62,muted,serif=True)
        txt(d,"OPEN",450,855,167,cream)
        line(d,203,566,821,566,gray,4)
        txt(d,"COFFEE  &  CAKE",667,795,54,cream)
        txt(d,"hot drinks  /  small bites",749,780,37,gray,serif=True)
        # Stylized original coffee-cup icon: saucer, cup, steam, handle.
        line(d,381,923,628,923,cream,6)
        line(d,414,851,414,901,cream,6)
        line(d,414,901,578,901,cream,6)
        line(d,578,901,578,851,cream,6)
        d.arc((571,845,619,894),270,90,fill=cream,width=6)
        line(d,456,817,454,776,gray,4)
        line(d,509,817,514,779,gray,4)
        txt(d,"COME ON IN",1065,825,76,cream)
        txt(d,"WELCOME / BIENVENUE",1188,750,36,muted)
    # The foreground has a hand-wiped chalk look: many fine near-black flecks,
    # not a uniformly perfect vector print.
    rng=random.Random(840+len(label))
    mask=Image.new("RGBA",im.size,(0,0,0,0))
    m=ImageDraw.Draw(mask,"RGBA")
    for i in range(12500):
        x=rng.randrange(1024);y=rng.randrange(1408)
        r=rng.choice([1,1,1,2])
        m.ellipse((x,y,x+r,y+r),fill=(10,15,15,rng.randint(8,41)))
    return Image.alpha_composite(im.convert("RGBA"),mask).convert("RGB")

for txtname in ("LUNCH","OPEN"):
    im=decorate(canvas_board(1007 if txtname=="LUNCH" else 1012),txtname)
    filename=os.path.join(OUT,f"Chalk_{txtname}.png")
    im.save(filename,optimize=True)
    print("TEXTURE",filename,os.path.getsize(filename))

# Grain follows the timber long axis. This bitmap is UV-mapped onto each beam
# and does not require unsupported Blender procedural shaders in game engines.
rng=random.Random(7300)
W,H=512,1024
wood=Image.new("RGB",(W,H))
p=wood.load()
for y in range(H):
    for x in range(W):
        sweep=(8.2*math.sin(x*.075+2.0*math.sin(y*.006)) +
               5.0*math.sin(x*.215+y*.018) +
               5.2*math.sin(x*.019+y*.002) +
               3.0*math.sin(x*.85+.7*math.sin(y*.05)))
        warm=rng.gauss(0,2.4)
        c=max(-30,min(32,sweep+warm))
        # Weathered brown stained oak with actual variation.
        p[x,y]=(int(max(0,min(255,121+c))),
                int(max(0,min(255,100+c*.82))),
                int(max(0,min(255,77+c*.70))))
d=ImageDraw.Draw(wood,"RGBA")
for i in range(200):
    x=rng.randrange(W);y=rng.randrange(H)
    span=rng.randrange(35,300)
    d.line((x,y,x+rng.randrange(-8,8),min(H,y+span)),
           fill=(44,31,24,rng.randrange(15,95)),width=rng.choice([1,1,2]))
for i in range(18):
    x=rng.randrange(W);y=rng.randrange(H)
    d.arc((x-5,y-15,x+5,y+15),30,320,fill=(55,35,24,90),width=2)
wood_path=os.path.join(OUT,"Weathered_Oak_Albedo.png")
wood.save(wood_path,optimize=True)
print("TEXTURE",wood_path,os.path.getsize(wood_path))
