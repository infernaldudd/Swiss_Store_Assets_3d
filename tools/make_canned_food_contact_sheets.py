"""Create retail-style contact sheets of all original printed canned-food labels.

These sheets show the design reference for in-game texture review, while GLBs
contain the actual wrapped geometry and metallic materials.
"""
import os,math,json
from PIL import Image, ImageDraw, ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
D=json.load(open(os.path.join(ROOT,"catalog","canned_food.json"),encoding="utf8"))
TEX=os.path.join(ROOT,"textures","canned_food")
OUT=os.path.join(ROOT,"previews","canned_food")
os.makedirs(OUT,exist_ok=True)
try:
    FONT=ImageFont.truetype("/usr/share/fonts/truetype/lato/Lato-Bold.ttf",25)
    HEAD=ImageFont.truetype("/usr/share/fonts/truetype/lato/Lato-Heavy.ttf",39)
except OSError:
    FONT=HEAD=ImageFont.load_default()
collections={}
for product in D["items"]:
    collections.setdefault(product["brand"],[]).append(product)
for brand,items in collections.items():
    cols=4
    rows=math.ceil(len(items)/cols)
    cw,ch=320,330
    img=Image.new("RGB",(cols*cw+60,rows*ch+116),(232,233,227))
    draw=ImageDraw.Draw(img)
    draw.text((30,20),brand+"  |  SWISS GAME PANTRY",font=HEAD,fill=(26,32,30))
    for n,p in enumerate(items):
        cx=n%cols
        cy=n//cols
        x=30+cx*cw
        y=98+cy*ch
        source=Image.open(os.path.join(TEX,p["id"]+"_wrap_2K.png")).convert("RGB")
        # Crop true front centre; reconstruct perspective via Blender render.
        label=source.crop((535,0,1513,1024))
        label.thumbnail((283,279),Image.Resampling.LANCZOS)
        img.paste(label,(x+18,y))
        title=p["flavour"][:21]+("..." if len(p["flavour"])>21 else "")
        draw.text((x+8,y+284),title,font=FONT,fill=(33,36,33))
    path=os.path.join(OUT,brand.replace(" ","_")+"_Collection_Labels.jpg")
    img.save(path,quality=89,optimize=True)
    print("CREATED SHEET",path,os.path.getsize(path),flush=True)
assert len(collections)==4
print("SUCCESS: 4 sheets covering 18 products",flush=True)
