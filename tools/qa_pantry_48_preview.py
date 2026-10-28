from PIL import Image
import os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
source=os.path.join(root,"previews/pantry_48/Eight_Actual_Package_Shapes_3D.png")
out=os.path.join(root,"previews/pantry_48/Eight_Actual_Package_Shapes_3D_QA.jpg")
im=Image.open(source).convert("RGB")
im.thumbnail((1150,760),Image.Resampling.LANCZOS)
im.save(out,quality=76,optimize=True)
print(out,os.path.getsize(out),flush=True)
assert os.path.getsize(out)<700000
