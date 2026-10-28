"""Generate five original Swiss-style paper price tickets in one 2K atlas.

5 horizontal rows: each label can be individually selected with UVs.
This is decorative fictional CHF pricing for a game, not a real retailer list.
 /usr/bin/python3 tools/generate_store_shelf_textures.py
"""
import os,random
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"textures","shelving")
os.makedirs(OUT,exist_ok=True)
W,H=2048,1024
im=Image.new("RGB",(W,H),(247,246,241))
d=ImageDraw.Draw(im)
def ft(size,bold=False):
 for p in (["/usr/share/fonts/truetype/lato/Lato-Black.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/lato/Lato-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]):
  if os.path.isfile(p):return ImageFont.truetype(p,size)
 return ImageFont.load_default()
DATA=[
 ("CHF 2.95","PACKUNG 250 G","LOOP"),
 ("CHF 3.40","SORTIMENT 1 STK","AMIGOS"),
 ("CHF 1.60","ORIGINAL 500 ML","ALP FARM"),
 ("CHF 4.90","PREMIUM 250 G","LOOP"),
 ("CHF 2.20","SWISS STYLE","AMIGOS")
]
for i,(price,detail,brand) in enumerate(DATA):
 y=i*H//5
 end=(i+1)*H//5
 d.rectangle((0,y,W,end),fill=(247-i%2*2,247-i%2*2,242))
 d.rectangle((0,y,31,end),fill=(213,94,42))
 d.rectangle((36,y+19,2012,end-20),outline=(203,204,200),width=2)
 d.text((95,y+22),brand,font=ft(60,True),fill=(35,47,49))
 d.text((95,y+101),detail,font=ft(34),fill=(71,81,83))
 d.text((1150,y+27),price,font=ft(115,True),fill=(21,29,32))
 d.text((1595,y+154),"FIKTIVES PREISSCHILD",font=ft(19),fill=(90,97,97))
path=os.path.join(OUT,"Shelf_Price_Tickets_2K.png")
im.save(path,optimize=True)
print("GENERATED",path,os.path.getsize(path),flush=True)
