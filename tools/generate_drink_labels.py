"""Generate 12 original, curvature-ready 2048x1024 drink wrap textures.

Every label's centre is physically mapped to the front of the corresponding
cylindrical can or bottle (u=0.5, front -Y); text is *printed in the UV map*,
not exported as free-floating 3D font geometry. Purely fictional commercial-
safe branding and hand-drawn decoration.

Run: /usr/bin/python3 tools/generate_drink_labels.py
"""
import os, math, random, hashlib
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
TEX=os.path.join(ROOT,"textures","drinks")
os.makedirs(TEX,exist_ok=True)
W,H=2048,1024

PRODUCTS=[
  ("LOOP Cola","COLA","can",(151,27,31),330),
  ("LOOP Cola Zero","COLA ZERO","can",(30,34,42),330),
  ("LOOP Orange","ORANGE","can",(241,111,27),330),
  ("LOOP Lemon","LEMON","can",(199,207,56),330),
  ("AMIGOS Ice Tea Peach","PEACH ICE TEA","pet",(225,117,51),500),
  ("AMIGOS Ice Tea Lemon","LEMON ICE TEA","pet",(157,186,61),500),
  ("ALPQUELL Still Water","STILL WATER","pet",(60,157,196),500),
  ("ALPQUELL Sparkling Water","SPARKLING","pet",(33,119,170),500),
  ("VOLTIX Energy Original","ORIGINAL ENERGY","can",(30,171,167),250),
  ("VOLTIX Energy Berry","BERRY ENERGY","can",(141,80,159),250),
  ("LOOP Apple Juice","APPLE JUICE","carton",(172,171,61),1000),
  ("AMIGOS Orange Juice","ORANGE JUICE","carton",(233,115,48),1000),
]

def font(size,style="black"):
  files={
    "black":["/usr/share/fonts/truetype/lato/Lato-Black.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "bold":["/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "regular":["/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
  }
  for f in files[style]:
    if os.path.isfile(f): return ImageFont.truetype(f,size)
  return ImageFont.load_default()

def centred(d,s,x,y,maxw,size,fill,style="bold"):
  while size>18:
    ft=font(size,style)
    bbox=d.textbbox((0,0),s,font=ft)
    if bbox[2]-bbox[0]<=maxw:break
    size-=2
  d.text((int(x-(bbox[0]+bbox[2])/2),int(y-(bbox[1]+bbox[3])/2)),s,font=ft,fill=fill)

def tone(c,mix,percent):
  return tuple(round((1-percent)*a+percent*b) for a,b in zip(c,mix))

def draw_wave(d,col,seed,water=False):
  rng=random.Random(seed)
  for j in range(9):
    points=[]
    for i in range(83):
      x=i/82*(W+100)-50
      y=405+j*75+38*math.sin(x/215+j*.67)+19*math.sin(x/86+j*.2)
      points.append((x,y))
    d.line(points,fill=(*tone(col,(255,255,255),.36),int(25+5*j)),width=6 if water else 9,joint="curve")
  for k in range(65):
    x=rng.randrange(425,1640); y=rng.randrange(220,810); r=rng.randint(5,20)
    d.ellipse((x-r,y-r,x+r,y+r),outline=(249,250,243,rng.randrange(45,140)),width=3)

def fruit(d,flavor,seed):
  rng=random.Random(seed)
  f=flavor.lower()
  if "lemon" in f: palette=[(232,213,84),(247,235,144),(114,141,43)]
  elif "orange" in f: palette=[(255,165,52),(251,208,101),(155,164,61)]
  elif "apple" in f: palette=[(182,204,76),(239,224,114),(95,154,71)]
  elif "berry" in f:palette=[(183,102,163),(229,142,193),(110,72,146)]
  elif "peach" in f:palette=[(251,181,108),(250,146,95),(166,154,69)]
  else:palette=[(236,219,169),(237,170,108),(193,129,78)]
  # Homemade fruit slice drawing confined below the typography.
  for k in range(7):
    xx=730+rng.randrange(0,615);yy=690+rng.randrange(0,225)
    rr=rng.randrange(36,94)
    d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(*palette[k%3],218),
              outline=(247,239,210,195),width=7)
    d.arc((xx-rr+15,yy-rr+15,xx+rr-15,yy+rr-15),35,245,
          fill=(249,240,197,190),width=5)
    for a in range(6):
      ang=a*math.tau/6
      d.line((xx,yy,xx+.65*rr*math.cos(ang),yy+.65*rr*math.sin(ang)),
             fill=(249,240,202,150),width=4)
  for k in range(10):
    x=rng.randrange(750,1280);y=rng.randrange(590,865)
    d.ellipse((x-17,y-9,x+17,y+9),fill=(*palette[2],173))

def make(p):
  name,flavor,form,col,ml=p
  seed=int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8],16)
  rng=np.random.default_rng(seed)
  y,x=np.mgrid[:H,:W].astype(np.float32)
  # Slight paper/ink texture, not a large flat single colour.
  noise=rng.normal(0,1.7,(H,W))
  v=(.08*np.cos(2*math.pi*x/W))+.08*(y/H)
  arr=np.clip(np.array(col,dtype=np.float32)[None,None,:]*(1-v[:,:,None])+
         noise[:,:,None],0,255).astype(np.uint8)
  im=Image.fromarray(arr,"RGB").convert("RGBA")
  d=ImageDraw.Draw(im,"RGBA")
  pale=(249,249,231,255)
  dark=(28,42,41,255)
  draw_wave(d,col,seed,water=("water" in name.lower()))
  # Can/bottle front is u=.5, so the centred hero copy wraps properly with
  # correct physical UVs. Back-of-pack data sits at either side.
  brand=name.split()[0]
  if brand=="LOOP":
    d.rounded_rectangle((697,84,1352,274),radius=70,
                        fill=(18,91,117,240),outline=(239,248,236,220),width=9)
  elif brand=="AMIGOS":
    d.polygon([(668,83),(1397,83),(1349,292),(705,292)],fill=(239,117,49,238))
  elif brand=="VOLTIX":
    d.polygon([(628,72),(1417,72),(1362,306),(682,306)],fill=(24,30,42,222))
    # Lightning icon: printed, not hovering off the can.
    d.polygon([(1397,305),(1454,315),(1408,415),(1445,409),
               (1373,531),(1396,422),(1355,422)],fill=(251,234,153,237))
  else:
    d.rounded_rectangle((695,87,1362,287),radius=34,fill=(29,77,108,224))
  centred(d,brand,1024,181,660,142,pale,"black")
  d.rounded_rectangle((539,361,1509,589),radius=26,
                      fill=(241,244,227,235))
  centred(d,flavor,1024,433,910,112,dark,"black")
  centred(d,"SWISS STORE • ORIGINAL GAME BRAND",1024,533,810,39,dark,"regular")
  if form=="can":
    fruit(d,flavor,seed)
  elif form=="pet":
    fruit(d,flavor,seed)
  else:
    fruit(d,flavor,seed)
  d.rounded_rectangle((802,915,1255,1006),radius=24,
                     fill=(26,36,39,219))
  centred(d,(str(ml)+" ml") if ml<1000 else "1 L",1024,955,385,61,pale)
  # Fictional rear print / not valid ingredients or nutritional information.
  d.rounded_rectangle((43,132,418,881),radius=21,
                      fill=(243,244,224,226))
  lines=["FICTIONAL","SWISS DRINK","",brand,"",flavor,
         "","GAME PROP","NOT FOR DRINKING","","ORIGINAL LABEL",
         "NO REAL NUTRITION","",str(ml)+" ml"]
  yy=154
  for t in lines:
    if t:
      sz=25 if len(t)<18 else 19
      d.text((66,yy),t,font=font(sz,"regular"),fill=(36,41,42,248))
    yy+=46
  d.rounded_rectangle((1624,143,2017,881),radius=21,
                     fill=(247,248,230,226))
  for i,t in enumerate(["DRINKS", "ALPEN / BASIL", "SWISS GAME",
                        "", "INK ON LABEL", "", "MOCK PRODUCT",
                        "FIKTIV","",name.upper()[:18]]):
    if t:d.text((1651,171+i*57),t,font=font(22,"regular"),fill=(39,43,40,255))
  # Non-scannable stylized lines, no copied barcodes.
  random_=random.Random(seed+90)
  xx=1661
  for i in range(50):
    w=random_.choice([2,3,4])
    d.rectangle((xx,779,xx+w,850),fill=(41,43,42,195))
    xx+=w+random_.randint(3,6)
    if xx>1980:break
  # Seam at u=0 on the BACK and a deliberately quiet strip between faces.
  d.line((0,1,W,1),fill=(255,250,224,106),width=3)
  out=os.path.join(TEX,name.replace(" ","_")+"_wrap_2K.png")
  im.convert("RGB").save(out,optimize=True)
  print("PRINTED UV LABEL",name,os.path.getsize(out),"bytes",flush=True)

if __name__=="__main__":
  for p in PRODUCTS:make(p)
  assert len([x for x in os.listdir(TEX) if x.endswith("_wrap_2K.png")])==12
  print("SUCCESS 12 different, original, physically UV-wrapped 2K drink labels",flush=True)
