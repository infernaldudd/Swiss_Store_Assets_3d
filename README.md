# Swiss Store Assets 3D

Four fictionalized, game-ready illuminated Swiss storefront signs based on supplied storefront photographs: **LOOP**, **LOOP restaurant**, **AMIGOS**, and the **AMIGOS double-A projecting sign**.

The assets are intended for use in Unreal Engine 5.7 and other glTF-capable engines. All dimensions use **metres**. Generated `.glb` assets will be available under `assets/`, with corresponding preview images under `previews/`. The signs have genuine 3D letters, visible depth, varied PBR materials, emissive faces, metal supports, and separate meshes for practical editing.

## Import

Import `assets/*.glb` using Unreal's **glTF Importer** plugin or drag them into a glTF-compatible engine. Front faces point toward the viewer; the original Blender geometry uses X horizontal, Z vertical, and negative Y outward. Place the back of the signs against the shop facade. Emissive materials make the letters luminous; for visible screen-space light spill activate Bloom and/or add local lighting in your level. Emission alone is not guaranteed to light nearby geometry.

## Files

| Model | Approx. width | Intent |
| --- | ---: | --- |
| `LOOP_Wordmark.glb` | 3.30 m | Freestanding orange channel-letter logo |
| `LOOP_Restaurant.glb` | 3.15 m | Orange LOOP + silver-white restaurant subline |
| `AMIGOS_Wordmark.glb` | 5.20 m | Oversized orange shopfront channel letters |
| `AMIGOS_DoubleA_Projected.glb` | 1.10 m | Two tall illuminated A initials and wall bracket, inspired by projecting M signs |

These are **original fictional brands**, not official Coop or Migros assets. The build script under `tools/` makes the four 3D assets in Blender, and the GitHub Actions workflow exports them directly to this repository.
