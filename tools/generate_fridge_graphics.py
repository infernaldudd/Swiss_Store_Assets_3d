"""Original 2K art for two generic refrigeration fixtures.

No Coop/Migros marks, no product photography or copied retail imagery.
 /usr/bin/python3 tools/generate_fridge_graphics.py
"""
from PIL import Image,ImageDraw,ImageFont
import os,math
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
DIR=os.path.join(ROOT,"textures","refrigeration")
os.makedirs(DIR,exist_ok=True)
def font(sz,bold=False):
    for p in (["/usr/share/fonts/truetype/lato/Lato-Heavy.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/lato/Lato-Regular.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]):
        if os.path.isfile(p):return ImageFont.truetype(p,sz)
    return ImageFont.load_default()
def center(d,txt,y,w,size,col):
    while size>12:
        f=font(size,True);box=d.textbbox((0,0),txt,font=f)
        if box[2]-box[0]<w:break
        size-=2
    d.text((round(1024-(box[2]+box[0])/2),round(y-(box[3]+box[1])/2)),txt,font=f,fill=col)
# Long chiller topper: very dark graphite panel, original clean lettering.
I=Image.new("RGB",(2048,512),(25,34,40))
d=ImageDraw.Draw(I)
for y in range(512):
    val=round(14+12*math.sin(y/512*math.pi))
    d.line((0,y,2048,y),fill=(24+val//5,31+val//5,38+val//5))
d.rectangle((0,477,2048,511),fill=(91,174,194))
d.rectangle((95,61,125,450),fill=(133,201,215))
center(d,"FRISCH  &  KÜHL",230,1760,213,(228,241,244))
d.text((1635,429),"SWISS STORE • SPIELWELT",font=font(23),fill=(148,183,196))
I.save(os.path.join(DIR,"Chiller_Header_2K.png"),optimize=True)
# Generic front counter LED menu/thermostat / original ink only.
I=Image.new("RGB",(2048,512),(22,32,36))
d=ImageDraw.Draw(I)
d.rounded_rectangle((37,32,2011,481),radius=34,fill=(37,48,52),outline=(109,130,137),width=13)
d.ellipse((112,188,250,326),outline=(101,221,202),width=18)
d.ellipse((154,228,202,276),fill=(113,231,208))
d.text((300,109),"FRISCHE  THEKE",font=font(158,True),fill=(226,231,228))
d.text((351,360),"GEKÜHLTE AUSLAGE  •  SPIELASSET",font=font(41),fill=(141,164,167))
I.save(os.path.join(DIR,"Counter_Front_Panel_2K.png"),optimize=True)
# 2K multi-panel diagnostic label for high-contrast LED digits, no fake actual UI.
I=Image.new("RGB",(2048,512),(19,26,30));d=ImageDraw.Draw(I)
d.rounded_rectangle((54,36,1990,479),radius=36,outline=(93,106,109),width=18)
d.text((147,64),"+4.0°C",font=font(301,True),fill=(103,224,229))
d.text((1320,112),"KÜHLUNG",font=font(116,True),fill=(184,203,212))
d.text((1379,304),"AKTIV",font=font(79),fill=(123,218,174))
I.save(os.path.join(DIR,"Digital_Thermostat_2K.png"),optimize=True)
print("DONE: three original 2048x512 texture prints",flush=True)
