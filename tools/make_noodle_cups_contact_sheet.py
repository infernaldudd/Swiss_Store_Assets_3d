"""Contact sheet comparing all eight original cup-noodle package variants."""
import os,json,math
from PIL import Image,ImageDraw,ImageFont
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
D=json.load(open(os.path.join(ROOT,"catalog","noodle_cups.json")))
T=os.path.join(ROOT,"textures","noodle_cups")
OUT=os.path.join(ROOT,"previews","noodle_cups")
os.makedirs(OUT,exist_ok=True)
try: f=ImageFont.truetype("/usr/share/fonts/truetype/lato/Lato-Bold.ttf",31)
except Exception:f=ImageFont.load_default()
im=Image.new("RGB",(1552,1120),(219,227,224))
draw=ImageDraw.Draw(im)
draw.text((54,18),"SWISS STORE — 8 FICTIONAL INSTANT NOODLE CUPS",font=f,fill=(23,30,29))
for i,p in enumerate(D["products"]):
    col=i%4;row=i//4
    x=42+col*380;y=99+row*508
    pic=Image.open(os.path.join(T,p["id"]+"_Wrap.png"))
    # A central section of each wrap is the visible front half of the 3D cup.
    pic=pic.crop((340,0,1196,1024))
    pic.thumbnail((337,426),Image.Resampling.LANCZOS)
    im.paste(pic,(x+17,y))
    draw.text((x,y+431),p["brand"]+" · "+p["flavor"],font=f,fill=(29,32,31))
out=os.path.join(OUT,"All_8_Variants_Artwork.jpg")
im.save(out,quality=88,optimize=True)
print("CONTACT SHEET",out,os.path.getsize(out))
