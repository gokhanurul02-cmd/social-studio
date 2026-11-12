# Asset sources and licences

| File | Used for | Source | Licence / terms |
|---|---|---|---|
| `assets/Xbot.glb` | Skinned rig + `idle`/`walk`/`run` clips for every baby and both strongman figures (re-proportioned by bone scaling, painted by shader masks) | three.js r187 examples, `examples/models/gltf/Xbot.glb` (https://github.com/mrdoob/three.js/tree/r187/examples/models/gltf) | Mixamo-derived character distributed with the three.js examples. Mixamo terms allow use in rendered projects; the raw model should not be redistributed as a standalone asset. |
| `assets/LeePerrySmith.glb`, `Map-COL.jpg`, `Infinite-Level_02_Tangent_SmoothUV.jpg` | Bald male head scan placed on the strongman rig (tinted) | three.js r187 examples, `examples/models/gltf/LeePerrySmith/` | "Infinite, 3D Head Scan" by Lee Perry-Smith (Infinite-Realities), CC Attribution 3.0. Attribution required. It is **not** a likeness of Dwayne Johnson. |
| `C:/Windows/Fonts/verdanab.ttf` (served at runtime, not copied) | Subtitles | Windows system font | Microsoft font licence; referenced from the OS, not redistributed. |
| `reference-source.mp4` audio | Soundtrack (narration) | User-supplied reference | Muxed in unchanged in content (Opus → AAC 256 kb/s for MP4 compatibility). |

Everything else is generated in code: the Cybertruck-style pickups (`src/truck.js`), sky/clouds/grid
(`src/env.js`), snakes, ropes and blood splats (`src/props.js`), the procedural baby head and the
shader-painted diaper/harness/trunks/boots/tattoo (`src/characters.js`).

v3: no frames or crops from the reference were used. v4: one face crop is used as a projected component texture (below); no frames are used as backgrounds.

## v4 additions

| File | Used for | Source | Licence |
|---|---|---|---|
| `../assets/makehuman/base.obj` + `caucasian-male-baby`, `universal-male-baby-averagemuscle-maxweight`, `caucasian-male-young`, `universal-male-young-maxmuscle-averageweight` (×1.6) targets → `assets/mh_baby.json`, `assets/mh_man.json` (built by `../scripts/build_mh.mjs`) | Continuous skinned bodies for all babies (incl. baked crowd) and both strongman figures, bound to the Xbot skeleton (bones moved to MakeHuman joint centres; geometric weights; extra normal-offset muscle bulk on the strongman) | makehumancommunity/makehuman (`data/3dobjs`, `data/targets/macrodetails`), see `../assets/makehuman/sources.json` | CC0 1.0 (asset headers + `LICENSE.ASSETS.md`) |
| `assets/ref_face_strongman.png` → `assets/ref_face_strongman_detail.png` | **Projected texture**: a 320×380 crop of the reference frame at 18.3 s (face only), converted to a luminance detail map and planar-projected onto the front of the MakeHuman head, registered on the eyes | Crop from the user-supplied reference video | Used as a component texture only, as permitted by the job brief; the geometry is MakeHuman, not the reference model |

The Lee Perry-Smith head and the Xbot mesh surfaces are no longer rendered in v4 (Xbot is still the skeleton/animation clip source).

## v5 additions
| `assets/ref_tattoo_mask.png`, `assets/ref_logo_mask.png` | **Projected textures**: ink mask of the shoulder/chest tattoo and the trunks logo, extracted from a crop of the reference frame at 18.3 s | Crop from the user-supplied reference video | Component textures only; projected onto MakeHuman geometry |
