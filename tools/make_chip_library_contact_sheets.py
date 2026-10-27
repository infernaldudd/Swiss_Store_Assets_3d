"""Make retailer-style contact sheets for all 88 original chips package fronts.
The contact sheets are previews only; the .glb models are 3D geometry.
"""
import os,json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
D=json.load(open(os.path.join(ROOT,"catalog/chip_collection.json")))["entries"]
TEX=os.path.join(ROOT,"textures","chips")
PREV=os.path.join(ROOT,"previews","chips")
os.makedirs(PREV,exist_ok=True)
def font(size):
    for p in ("/usr/share/fonts/truetype/lato/Lato-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.isfile(p):return ImageFont.truetype(p,size)
    return ImageFont.load_default()
brands=sorted(set(e["brand"] for e in D))
for brand in brands:
    entries=[e for e in D if e["brand"]==brand]
    cols=4
    rows=math.ceil(len(entries)/cols)
    w,h=230,340
    sheet=Image.new("RGB",(cols*w+60,rows*h+116),(224,227,225))
    d=ImageDraw.Draw(sheet)
    d.text((32,18),brand+" | GAME SNACK COLLECTION",font=font(32),fill=(23,33,31))
    for i,e in enumerate(entries):
        col=i%cols;row=i//cols
        x=30+col*w;y=92+row*h
        art=Image.open(os.path.join(TEX,e["id"]+"_front.jpg")).convert("RGB")
        art.thumbnail((190,282),Image.Resampling.LANCZOS)
        sheet.paste(art,(x+20,y))
        label=(e["flavour"]+"  "+str(e["weight_g"])+"g")
        if len(label)>23:label=label[:21]+".."
        d.text((x+13,y+289),label,font=font(17),fill=(28,32,29))
    path=os.path.join(PREV,brand+"_variants.jpg")
    sheet.save(path,quality=87,optimize=True)
    print("CONTACT",brand,len(entries),path,flush=True)
assert len(brands)==8
print("DONE: all 8 family contact sheets",flush=True)
