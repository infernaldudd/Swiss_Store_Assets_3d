"""Generate original 2K printed-foil artworks for a fictional Swiss chips packet.

Original parody-style brand: SCHWEFEL. No third-party artwork or logo is copied.
Run: /usr/bin/python3 tools/generate_schwefel_textures.py
Needs python3-numpy and python3-pil.
"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
DEST=os.path.join(ROOT,"textures","schwefel_paprika")
os.makedirs(DEST,exist_ok=True)
W,H=2048,3072
random.seed(11827)
rng=np.random.default_rng(11827)

def font(n,bold=True,italic=False):
    choices=(
      ['/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf']
      if italic else
      ['/usr/share/fonts/truetype/lato/Lato-Heavy.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
    ) if bold else ['/usr/share/fonts/truetype/lato/Lato-Regular.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for p in choices:
        if os.path.exists(p): return ImageFont.truetype(p,n)
    raise FileNotFoundError("No suitable system font")

def center_text(d,text,y,size,fill,width=1870,stroke=0,stroke_fill=None,font_italic=False):
    f=font(size,italic=font_italic)
    while d.textbbox((0,0),text,font=f,stroke_width=stroke)[2]>width and size>18:
        size-=3
        f=font(size,italic=font_italic)
    b=d.textbbox((0,0),text,font=f,stroke_width=stroke)
    x=(W-b[2]+b[0])//2
    d.text((x,y),text,font=f,fill=fill,stroke_width=stroke,stroke_fill=stroke_fill)
    return b

def background(rear=False):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    wobble=12*np.sin(xx*.005 + yy*.002)+6*np.sin(yy*.014+xx*.009)
    grain=rng.normal(0,2.35,(H,W))
    vig=(xx-W/2)**2/(W/2)**2+(yy-H/2)**2/(H/2)**2
    if rear:
        r=251-22*yy/H-11*vig+wobble*.43+grain
        g=128+25*yy/H-7*vig+wobble*.35+grain*.6
        b=28+17*yy/H-4*vig+wobble*.17
    else:
        r=255-17*yy/H-14*vig+wobble*.46+grain
        g=160-48*yy/H-14*vig+wobble*.45+grain*.65
        b=31-7*yy/H-9*vig+wobble*.18
    a=np.stack([r,g,b],axis=-1)
    return Image.fromarray(np.uint8(np.clip(a,0,255)),'RGB')

def brand(d,y=120,scale=1):
    cx=W//2
    bw=int(300*scale);bh=int(240*scale)
    left=cx-bw//2
    d.rounded_rectangle((left,y,left+bw,y+bh),radius=int(28*scale),fill=(225,30,26),outline=(255,248,228),width=int(14*scale))
    f=font(int(190*scale),italic=True)
    bb=d.textbbox((0,0),'S',font=f)
    d.text((cx-(bb[2]-bb[0])/2-bb[0],y+2*scale-bb[1]),"S",font=f,fill=(255,255,255))
    center_text(d,"SCHWEFEL",y+bh+34*scale,int(82*scale),(191,21,22),width=int(1300*scale))
    center_text(d,"ORIGINAL CHIPS",y+bh+132*scale,int(42*scale),(115,52,18),width=int(1000*scale))

def mountains(im):
    d=ImageDraw.Draw(im,'RGBA')
    d.polygon([(0,2055),(130,1950),(300,2000),(530,1895),(760,1965),(940,1880),(1150,1950),(1320,1830),(1520,1953),(1810,1910),(2048,2050),(2048,2500),(0,2500)], fill=(140,180,176,200))
    d.polygon([(0,2140),(220,2066),(410,2090),(680,2025),(950,2075),(1230,2010),(1490,2098),(1845,2015),(2048,2100),(2048,2445),(0,2490)],fill=(75,140,88,240))
    d.polygon([(0,2235),(300,2170),(680,2199),(970,2150),(1320,2235),(1795,2110),(2048,2140),(2048,2615),(0,2615)],fill=(76,139,65,254))
    d.polygon([(0,2262),(2048,2145),(2048,2590),(0,2660)],fill=(132,175,49,255))
    for i in range(36):
        off=i*68
        d.line([(-150+off,2590), (680+off*.39,2215)],fill=(65,137,45,85),width=random.randrange(3,9))
    # golden paprika dust and grain fields
    for i in range(3000):
        x=random.randrange(W);y=random.randrange(2220,2560)
        d.ellipse((x,y,x+2,y+2),fill=(224,206,87,random.randrange(20,80)))

def chip(im,cx,cy,rx,ry,rotate,seed):
    rr=random.Random(seed)
    n=110
    edge=[]
    for i in range(n):
        t=math.tau*i/n
        f=1+rr.uniform(-.046,.045)+.026*math.sin(7*t+seed)
        edge.append((rx*f*math.cos(t),ry*f*math.sin(t)))
    a=math.radians(rotate)
    transformed=[(int(cx+x*math.cos(a)-y*math.sin(a)),
                  int(cy+x*math.sin(a)+y*math.cos(a))) for x,y in edge]
    mask=Image.new("L",(W,H),0)
    md=ImageDraw.Draw(mask)
    md.polygon(transformed,fill=255)
    shadow=mask.filter(ImageFilter.GaussianBlur(30))
    sh=Image.new("RGBA",(W,H),(49,23,0,0))
    sh.putalpha(shadow.point(lambda a:int(a*.40)))
    im.alpha_composite(sh,(24,40))
    px_rng=np.random.default_rng(seed)
    yy,xx=np.ogrid[:H,:W]
    # very fine paprika spice texture + fried-chips gradient
    surf=np.empty((H,W,4),dtype=np.uint8)
    across=np.clip((xx-cx)/max(rx,1),-1,1)
    up=np.clip((yy-cy)/max(ry,1),-1,1)
    bump=(21*np.sin(xx*.035+yy*.011)+9*np.sin(xx*.15-yy*.068) +
          px_rng.normal(0,16,(H,W)))
    orange=16+22*np.sin((xx+yy)*.003)
    light=np.clip(1-.20*across+.09*up, .72,1.2)
    surf[:,:,0]=np.clip((230+bump*.33+orange)*light,0,255)
    surf[:,:,1]=np.clip((169+bump*.46+orange*.53)*light,0,255)
    surf[:,:,2]=np.clip((58+bump*.28)*light,0,255)
    surf[:,:,3]=np.array(mask)
    chip_layer=Image.fromarray(surf,'RGBA')
    # dark toasted edge / crispy ridges
    md2=ImageDraw.Draw(chip_layer,"RGBA")
    md2.line(transformed+[transformed[0]],fill=(135,79,18,155),width=13,joint="curve")
    chip_layer.putalpha(mask)
    im.alpha_composite(chip_layer)
    dots=ImageDraw.Draw(im,'RGBA')
    for j in range(1650):
        x=rr.randint(int(cx-rx),int(cx+rx))
        y=rr.randint(int(cy-ry),int(cy+ry))
        if 0<=x<W and 0<=y<H and mask.getpixel((x,y))>0:
            radius=rr.choice((1,2,2,3,5,7))
            col=rr.choice([(180,62,20,85),(199,82,25,120),(255,242,149,115),(129,76,18,90)])
            dots.ellipse((x-radius,y-radius,x+radius,y+radius),fill=col)

def pepper(im):
    d=ImageDraw.Draw(im,"RGBA")
    pts=[(1230,2570),(1280,2480),(1370,2455),(1490,2410),(1565,2330),(1640,2360),(1642,2480),(1555,2568),(1405,2585)]
    d.polygon([(x+17,y+29) for x,y in pts],fill=(55,38,8,70))
    d.polygon(pts,fill=(20,113,41,255))
    d.line([(1283,2530),(1400,2490),(1513,2423),(1598,2399)],fill=(83,189,64,220),width=26,joint="curve")
    d.line([(1578,2382),(1612,2322),(1680,2312)],fill=(41,83,24,255),width=29,joint="curve")
    d.ellipse((1300,2530,1355,2552),fill=(170,229,97,165))
    # small fresh paprika flakes and herb leaves
    for j in range(70):
        x=random.randrange(1200,1790);y=random.randrange(2470,2720)
        rad=random.randrange(5,19)
        d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=(218,155+random.randrange(65),28,random.randrange(100,210)))

def front():
    im=background()
    mountains(im)
    d=ImageDraw.Draw(im,'RGBA')
    # recognizable white swooping paper-printed graphic; not a copied original.
    d.polygon([(0,1050),(182,975),(2048,1435),(2048,1950),(1760,1848),(0,1475)],fill=(242,248,242,240))
    d.polygon([(0,1005),(190,960),(2048,1380),(2048,1464),(0,1070)],fill=(230,235,231,170))
    brand(d,100,1)
    # Large dark italic Paprika artwork with warm light outline; give it prominence.
    lettering=Image.new('RGBA',(2048,720),(0,0,0,0))
    td=ImageDraw.Draw(lettering)
    big=font(330,italic=True)
    # fit to wide screen
    while td.textbbox((0,0),"Paprika",font=big,stroke_width=12)[2]>1930:
        big=font(big.size-4,italic=True)
    bbox=td.textbbox((0,0),"Paprika",font=big,stroke_width=12)
    td.text(((W-bbox[2]+bbox[0])//2,140),"Paprika",font=big,
            fill=(29,30,30,255),stroke_width=13,stroke_fill=(250,250,245,255))
    lettering=lettering.rotate(7,resample=Image.Resampling.BICUBIC,expand=False)
    im=Image.alpha_composite(im.convert("RGBA"),lettering.transform((W,H),Image.Transform.AFFINE,(1,0,0,0,1,-1030),resample=Image.Resampling.BICUBIC))
    d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle((1260,1695,1960,1771),24,fill=(16,31,24,235))
    d.text((1322,1703),"SCHWEIZER CHIPS",font=font(47),fill=(242,251,235,255))
    chip(im,655,2360,375,340,-23,801)
    chip(im,1420,2304,357,351,18,921)
    pepper(im)
    d=ImageDraw.Draw(im,'RGBA')
    d.rectangle((0,2875,W,3072),fill=(200,94,7,215))
    # Narrow ridges at the crimp edges printed in darker orange.
    for y in list(range(16,114,13))+list(range(2920,3060,13)):
        d.line((0,y,W,y),fill=(179,77,10,135),width=4)
    center_text(d,"MIT SCHWEIZER ALPENSALZ & RAPSÖL",2765,48,(43,39,25,255),width=1880)
    d.text((1685,2882),"90 g",font=font(75),fill=(42,32,20,255))
    d.text((128,2945),"FIKTIVE SPIELMARKE",font=font(34),fill=(89,36,10,250))
    path=os.path.join(DEST,"Schwefel_Paprika_Front_2K.png")
    im.convert('RGB').save(path,optimize=True)
    print("TEXTURE",os.path.basename(path),os.path.getsize(path),flush=True)

def back():
    im=background(rear=True)
    d=ImageDraw.Draw(im,"RGBA")
    brand(d,115,.72)
    d.rounded_rectangle((130,650,1916,1020),30,fill=(255,204,104,130),outline=(183,80,25,170),width=6)
    center_text(d,"SCHWEFEL",680,96,(99,38,20,255))
    center_text(d,"KNUSPRIGE KARTOFFELCHIPS",805,58,(73,48,34,255))
    center_text(d,"PAPRIKA  /  ORIGINAL",906,65,(52,48,33,255))
    d.text((160,1160),"FEIN GEWÜRZT. KNUSPRIG. SCHWEIZER STYLE.",font=font(55),fill=(59,40,21,255))
    paragraphs=[
        "Kartoffelchips mit Paprika-Geschmack.",
        "Fiktives Lebensmittel für Videospiele.",
        "Nicht zum Verkauf oder Verzehr.",
        "Illustration und Gestaltung: Original-Spielasset.",
        "Geschmack: würzig, rauchig und knusprig.",
        "Inhalt: 90 g  |  Produktidee: Schweiz."
    ]
    for i,line in enumerate(paragraphs):
        d.text((165,1290+i*74),line,font=font(40,False),fill=(61,48,28,255))
    d.line((155,1835,1895,1835),fill=(125,73,30,190),width=5)
    d.text((160,1890),"NÄHRWERTE (FIKTIVE ANGABE)",font=font(51),fill=(60,41,25,255))
    nutrition=[
        ("Energie","—"),("Fett","—"),("Kohlenhydrate","—"),
        ("Eiweiss","—"),("Salz","—")
    ]
    for i,(label,val) in enumerate(nutrition):
        y=1970+i*83
        d.rounded_rectangle((150,y-11,1100,y+63),9,fill=(245,179,75,90))
        d.text((177,y),label,font=font(40,False),fill=(66,39,20,245))
        d.text((1020,y),val,font=font(40),fill=(66,39,20,245))
    # invented non-scannable visual stripes: explicitly NOT an EAN.
    d.rounded_rectangle((1255,1864,1922,2555),radius=16,fill=(245,227,183,240))
    r=random.Random(881)
    cursor=1305
    while cursor<1846:
        width=r.choice((2,4,6,9,11))
        d.rectangle((cursor,1988,cursor+width,2435),fill=(32,25,19,248))
        cursor+=width+r.choice((3,7,12))
    d.text((1340,2452),"0000 0000 0000",font=font(37,False),fill=(40,32,27,240))
    d.text((1337,2510),"DUMMY / GAME PROP",font=font(21),fill=(92,64,39,245))
    d.rectangle((0,2890,W,3072),fill=(178,83,16,120))
    for y in list(range(16,110,13))+list(range(2918,3070,13)):
        d.line((0,y,W,y),fill=(169,74,19,120),width=4)
    d.text((152,2774),"SCHWEFEL SNACKS  |  IMAGINÄRE FIRMA",font=font(42),fill=(73,43,18,255))
    path=os.path.join(DEST,"Schwefel_Paprika_Back_2K.png")
    im.save(path,optimize=True)
    print("TEXTURE",os.path.basename(path),os.path.getsize(path),flush=True)

def foil_maps():
    # Procedural fine-fold normal and roughness maps, separately stored as packed PBR.
    ww,hh=1024,1536
    yy,xx=np.mgrid[0:hh,0:ww].astype(np.float32)
    v=np.sin(xx*.037+yy*.012)*.12+np.sin(yy*.081-xx*.044)*.1
    v+=.22*np.sin((yy*.009+xx*.056)+np.sin(yy*.021))*np.sin(xx*.014)
    v+=rng.normal(0,.047,(hh,ww))
    gy,gx=np.gradient(v)
    nx=np.clip(-gx*.85,-.65,.65)
    ny=np.clip(-gy*.85,-.65,.65)
    nz=np.sqrt(np.maximum(.1,1-nx*nx-ny*ny))
    normal=np.uint8(np.clip(np.stack([(nx+1)*127.5,(ny+1)*127.5,(nz+1)*127.5],axis=-1),0,255))
    npth=os.path.join(DEST,"Foil_MicroWrinkle_Normal.png")
    Image.fromarray(normal,'RGB').save(npth,optimize=True)
    rough=np.uint8(np.clip((.27+.045*np.abs(v)+.018*rng.normal(size=(hh,ww)))*255,15,255))
    rpath=os.path.join(DEST,"Foil_Roughness.png")
    Image.fromarray(rough,'L').save(rpath,optimize=True)
    print("PBR MAPS",os.path.getsize(npth),os.path.getsize(rpath),flush=True)

if __name__=="__main__":
    front();back();foil_maps()
    print("DONE: original front/back and foil maps",flush=True)
