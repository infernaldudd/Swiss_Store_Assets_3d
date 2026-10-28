"""Create 48 UNIQUE 2K retail wrap artworks from fictional brands.

Original typography, colors, vector-style ink decoration and subtle printed
paper/sleeve grain. No real Coop/Migros logos, no copied packaging art.
Pixels: 2048x1024, the entire horizontal coordinate is cylindrical U.
Most important brand/product typography occupies U=.27-.73, visible on
front of physical wrapped cartons, bags and jars.

Run: /usr/bin/python3 tools/generate_pantry_48_art.py
"""
import os,math,json,random,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
CAT=json.load(open(os.path.join(ROOT,"catalog","pantry_48.json")))
OUT=os.path.join(ROOT,"textures","pantry_48")
PRE=os.path.join(ROOT,"previews","pantry_48")
for d in (OUT,PRE):os.makedirs(d,exist_ok=True)
W,H=2048,1024
COL={
"wheat":(201,160,73),"tomato":(178,64,40),"gold":(196,151,59),"mint":(91,143,116),
"cream":(216,198,150),"red":(169,58,53),"teal":(44,130,127),"sand":(173,146,93),
"rose":(173,88,110),"blue":(76,114,154),"yellow":(215,178,75),"brown":(123,73,46),
"black":(50,55,58),"orange":(208,103,52),"olive":(99,125,63)}
BRAND={
"LOOP":((21,93,110),(250,244,225)),
"AMIGOS":((207,96,46),(255,244,225)),
"ALP FARM":((54,92,68),(246,241,220)),
"SPARFIX":((167,48,53),(252,246,227)),
"ALPSWEET":((83,53,94),(251,232,217))}
def ffont(n,bold=True):
 paths=["/usr/share/fonts/truetype/lato/Lato-Heavy.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/lato/Lato-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
 for p in paths:
  if os.path.isfile(p):return ImageFont.truetype(p,n)
 return ImageFont.load_default()
def fitted(draw,value,x,y,width,size,color,heavy=True):
 while size>=17:
  ft=ffont(size,heavy)
  q=draw.textbbox((0,0),value,font=ft)
  if q[2]-q[0]<=width:break
  size-=3
 draw.text((round(x-(q[2]+q[0])/2),round(y-(q[3]+q[1])/2)),
           value,font=ft,fill=color)
def mix(a,b,t):
 return tuple(round(a[i]*(1-t)+b[i]*t) for i in range(3))
def illustration(draw,p,rng):
 c=COL[p["palette"]]
 # Original stylized photoprint-style shapes, not a copied product logo.
 # Deliberately more subtle than large flat cartoon illustrations.
 form=p["form"]
 if form in ("glass_jar","squeeze","bottle"):n=105
 elif form in ("choc_bar","cookie_box","flowpack"):n=115
 elif form in ("pasta_bag","rice_bag","standup_pouch","cereal_box","paper_sack"):n=165
 else:n=100
 # Many shaded individual ingredients produce a believable food illustration
 # at shelf distance; isolated oversized strokes looked like a blank cartoon.
 for j in range(n):
  ang=rng.uniform(0,math.tau)
  dist=rng.uniform(0,215)
  xx=1024+dist*math.cos(ang)
  yy=735+dist*.56*math.sin(ang)
  rad=rng.randint(6,19)
  if "pasta" in form:
   # Penne/short pasta printed decorative ink; wheat colour and dark grooves.
   # Narrow pasta strokes are lines, not short-radius rectangles.
   # Pillow's rounded_rectangle rejects very short fractional heights.
   draw.line((round(xx-rad),round(yy),round(xx+rad),round(yy)),
             fill=mix(c,(249,223,147),.43),width=max(3,rad//2))
   draw.line((round(xx-rad*.58),round(yy),round(xx+rad*.58),round(yy)),
             fill=mix(c,(91,61,29),.28),width=2)
  elif "coffee" in form or "cappuccino" in p["name"].lower():
   draw.ellipse((xx-rad*.65,yy-rad*.45,xx+rad*.65,yy+rad*.45),
                fill=(102,62,39),outline=(178,128,77),width=3)
   draw.arc((xx-rad*.22,yy-rad*.34,xx+rad*.22,yy+rad*.34),-60,135,fill=(46,28,21),width=3)
  elif "choc" in form or form=="flowpack":
   # A little chocolate shard ink stroke; round corners on tiny floating
   # rectangular coordinates cause Pillow to reject valid fractional bounds.
   draw.line((round(xx-rad*.65),round(yy),round(xx+rad*.65),round(yy)),
             fill=mix(c,(102,57,38),.5),width=max(5,round(rad*.72)))
   draw.line((round(xx-rad*.48),round(yy-1),round(xx+rad*.48),round(yy-1)),
             fill=mix(c,(241,205,150),.3),width=2)
  elif form in ("glass_jar","squeeze","bottle"):
   draw.ellipse((xx-rad*.7,yy-rad*.55,xx+rad*.7,yy+rad*.55),
                fill=mix(c,(255,235,173),.23),outline=mix(c,(78,61,43),.32),width=3)
  else:
   draw.ellipse((xx-rad*.55,yy-rad*.49,xx+rad*.55,yy+rad*.49),
                fill=mix(c,(245,223,161),.4),outline=mix(c,(91,69,48),.24),width=2)
 # Fine diagonal short glints/foil highlights and tiny printed flecks.
 for i in range(64):
  x=rng.randrange(600,1440);y=rng.randrange(595,880)
  draw.line((x,y,x+rng.randrange(5,19),y-rng.randrange(2,9)),
            fill=mix(c,(255,248,229),.52),width=1)
def make(p):
 seed=int(hashlib.sha256(p["id"].encode()).hexdigest()[:8],16)
 rng=random.Random(seed)
 base=COL[p["palette"]]
 dark=mix(base,(21,30,34),.67)
 # Fine-grain offset press texture and gentle vertical vignette using
 # image gradients, not uniform untextured Roblox solid colours.
 im=Image.new("RGB",(W,H),base)
 d=ImageDraw.Draw(im)
 for x in range(0,W,5):
  wav=.5+.5*math.sin(x*.007+seed%30)+.25*math.sin(x*.024)
  d.line((x,0,x,H),fill=mix(base,(23,29,33),min(.18,max(.0,.10*wav))),width=5)
 # Material-driven vertical width bands, symmetrical in primary forward half.
 d.rounded_rectangle((510,35,1538,973),radius=38,
                     fill=mix(base,(245,242,226),.79),
                     outline=mix(base,(42,58,64),.36),width=8)
 d.rectangle((524,40,1524,314),fill=mix(base,(22,45,54),.36))
 bback,bink=BRAND[p["brand"]]
 d.rounded_rectangle((604,62,1444,260),radius=28,
                     fill=bback,outline=mix(bback,(242,235,207),.38),width=6)
 fitted(d,p["brand"],1024,150,782,126,bink)
 d.rectangle((603,345,1444,351),fill=dark)
 fitted(d,p["name"].upper(),1024,438,819,88,(29,39,42))
 fitted(d,"SCHWEIZER SUPERMARKT  ·  FIKTIVE MARKE",1024,515,850,28,(74,79,77),False)
 d.ellipse((752,596,1296,912),fill=mix(base,(245,231,204),.53),
           outline=mix(base,(94,74,60),.34),width=11)
 illustration(d,p,rng)
 d.rounded_rectangle((833,891,1217,965),radius=21,
                     fill=mix(bback,(22,31,34),.18))
 fitted(d,p["weight"],1024,926,330,48,(251,248,232))
 # Back and side information is readable but fictional; no copying
 # any real nutrition panel, registered company name or barcode number.
 for xlo,xhi in ((22,455),(1592,2026)):
  d.rounded_rectangle((xlo,93,xhi,909),radius=20,
                      fill=mix(base,(249,250,240),.83))
  d.line((xlo+33,185,xhi-33,185),fill=(112,128,127),width=4)
  for i,line in enumerate(("SWISS STORE",p["brand"],"FIKTIVES",
                            "GAME PRODUKT","ORIGINAL DESIGN",
                            "","NUR SPIELWELT",p["weight"],"",p["id"][:19])):
   if line:
    d.text((xlo+39,119+i*67),line,font=ffont(27 if i!=9 else 17,i<2),
           fill=(47,57,57))
  # Handmade non-scannable stripes, no copy of EAN code.
  kx=xlo+46
  for k in range(27):
   w=rng.randrange(2,6)
   d.rectangle((kx,790,kx+w,867),fill=(41,46,47))
   kx+=w+rng.randrange(3,9)
  d.text((xlo+41,883),"ORIGINAL 3D-ASSET",font=ffont(17,False),fill=(67,75,74))
 # Tonal uncoated-fibre detail, not an attempt to simulate a real photograph.
 grain=Image.new("L",(256,128),0)
 gr=ImageDraw.Draw(grain)
 for i in range(5400):
  x=rng.randrange(256);y=rng.randrange(128)
  gr.point((x,y),fill=rng.randrange(1,63))
 grain=grain.resize((W,H),Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(.4))
 # Image grain added very lightly to preserve premium glossy print clarity.
 from PIL import ImageChops
 overlay=Image.new("RGB",(W,H),(248,248,248))
 im=Image.blend(im,ImageChops.multiply(im,Image.new("RGB",(W,H),(248,248,248))),.038)
 out=os.path.join(OUT,p["id"]+"_2K.jpg")
 im.save(out,quality=91,subsampling=0,optimize=True)
 print("2K PRINT",p["id"],os.path.getsize(out),flush=True)
 return out
if __name__=="__main__":
 total=0
 for group in CAT["categories"]:
  cards=[]
  for p in group["products"]:
   path=make(p);total+=1
   im=Image.open(path).convert("RGB")
   crop=im.crop((535,30,1515,985));crop.thumbnail((255,315))
   cards.append((p["name"],crop))
  out=Image.new("RGB",(3*355,2*410),(233,233,228))
  d=ImageDraw.Draw(out)
  for i,(name,crop) in enumerate(cards):
   xx=(i%3)*355+45
   yy=(i//3)*410+28
   out.paste(crop,(xx,yy))
   fitted(d,name,xx+130,yy+340,300,27,(41,52,54))
  out.save(os.path.join(PRE,group["folder"]+"_Six_Different_SKUs.jpg"),
           quality=86,optimize=True)
 assert total==48
 print("SUCCESS 48 original 2048x1024 wrappers + 8 family galleries",flush=True)
