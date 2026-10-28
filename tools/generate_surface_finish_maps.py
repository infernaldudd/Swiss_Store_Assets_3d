"""Original micro-surface maps for selective realistic packaging gloss.

All scalar maps are linear, non-color roughness maps, embedded in exported
GLBs by Blender. Never apply them universally: metal, paper, printed plastic
and foil require different specularity. Standalone reproducible source.
 /usr/bin/python3 tools/generate_surface_finish_maps.py
"""
import os,math
import numpy as np
from PIL import Image
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"textures","surface_finishes")
os.makedirs(OUT,exist_ok=True)
N=768
yy,xx=np.mgrid[:N,:N].astype(np.float32)
rng=np.random.default_rng(195389)
noise=rng.normal(0,1,(N,N))
slow=(np.sin(xx*.028+yy*.007)*.5+np.sin(yy*.038-xx*.017)*.3)
grain=np.sin(xx*.93+yy*.018)*.23+np.sin(xx*.53-yy*.13)*.21
specs={
  # Mean and amplitude; not unphysically mirror-clear.
  "Glossy_Laminated_Print_Roughness":(.265,.055,.036),
  "SemiGloss_Vinyl_Roughness":(.345,.060,.037),
  "Flex_Foil_Roughness":(.29,.073,.055),
  "PET_Bottle_Roughness":(.185,.029,.017),
  "Powdercoat_Steel_Roughness":(.43,.046,.034),
  "Brushed_Steel_Roughness":(.29,.035,.027),
  "Matte_Paper_Roughness":(.72,.032,.024),
  "Foil_Lid_Roughness":(.235,.036,.029),
}
for name,(mean,a,b) in specs.items():
  val=mean+a*slow+b*grain+.012*noise
  if name.startswith("Flex"):
    # Irregular foil micro-crumples, but do not bake full silhouette folds
    val+=.032*np.sin(xx*.077+yy*.115)
  if name.startswith("Brushed"):
    val+=.016*np.sin(xx*.42)+.013*np.sin(xx*.78)
  if name.startswith("Powdercoat"):
    val+=.012*np.sin(xx*.96-yy*.96)
  val=np.uint8(np.clip(val,.07,.92)*255)
  Image.fromarray(val,"L").save(os.path.join(OUT,name+".png"),optimize=True)
  print("SURFACE",name,"range",val.min(),val.max(),flush=True)
# Very low-amplitude tangent-space micro normal map for powder coat,
# foil and can paint; bumps are deliberately less noticeable than silhouette.
micro= (.004*np.sin(xx*.28+yy*.17)+.003*np.sin(xx*.65-yy*.53)
       +rng.normal(0,.002,(N,N)))
dy,dx=np.gradient(micro)
nx=-dx*4.0;ny=-dy*4.0
nz=np.sqrt(np.maximum(.002,1-nx*nx-ny*ny))
normal=np.uint8(np.clip(np.stack([(nx+1)*127.5,(ny+1)*127.5,
                                  (nz+1)*127.5],axis=2),0,255))
Image.fromarray(normal,"RGB").save(os.path.join(OUT,"Soft_Micro_Normal.png"),optimize=True)
print("DONE",len(specs),"different physical roughness finishes and 1 normal",flush=True)
