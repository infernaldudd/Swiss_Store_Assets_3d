"""Produce compact, human-inspectable contact sheet of both shelf renders.

The Cycles PNGs are kept intact; this downsizes only an additional JPEG for
quick QA, avoiding GitHub's base64 size cap for larger PNG previews.
"""
import os
from PIL import Image, ImageOps, ImageDraw, ImageFont
root=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
folder=os.path.join(root,"previews","shelving")
names=[
 "Swiss_Supermarket_Wall_Shelf_1m_5Tier",
 "Swiss_Supermarket_Wall_Shelf_2m_TwoBay"
]
im=Image.new("RGB",(1100,650),(228,229,225))
d=ImageDraw.Draw(im)
try:
 title=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",31)
 small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",20)
except OSError:
 title=small=ImageFont.load_default()
d.text((40,17),"SWISS STORE · LOW-GLARE STEEL SHELF QA",font=title,fill=(30,40,41))
for i,name in enumerate(names):
 path=os.path.join(folder,name+".png")
 pic=Image.open(path).convert("RGB")
 pic.thumbnail((515,520),Image.Resampling.LANCZOS)
 x=25+i*550;y=80
 im.paste(pic,(x+(515-pic.width)//2,y))
 label="1m / 5 metal trays" if i==0 else "2m / two joined bays"
 d.text((x+20,610),label,font=small,fill=(35,43,44))
out=os.path.join(folder,"Shelf_QA_Contact.jpg")
im.save(out,quality=78,optimize=True)
print("QA SHEET",out,os.path.getsize(out))
assert os.path.getsize(out)<900000
