# Forest Courtyard

Original, procedural low-poly training arena for LoL Mobile. All model textures are embedded in `Models/forest_courtyard.glb`; no external texture files are required to load it.

## Folders

- `Models/`: standalone runtime GLB.
- `Textures/`: editable 512 × 512 base-color atlas (also embedded).
- `Source/`: deterministic Python generator; requires numpy and Pillow.
- `Metadata/`: layout and structural validation report.
- `Previews/`: software-rendered geometry preview; not an in-game screenshot.

## Scale and layout

Y up, origin at the center, scale 1. Ground footprint 34 × 34 units. Center platform is at Y = 0.01; paths and inlays have small offsets to avoid flicker. The playable radius is 11.5 units, matching the existing arena scale. Trees, rocks and four ruined pillars sit around the perimeter. Meshes are grouped by terrain, courtyard, paths, inlays, rocks, trunks, canopies and ruins.

## Loading

Use the existing Three.js GLTFLoader with `./Assets/Map/Models/forest_courtyard.glb`, then add `gltf.scene` at its original scale and position. Set mesh `receiveShadow` and `castShadow` according to the device budget. Replace the existing procedural environment when integrating to avoid overlapping surfaces. Keep champions and training targets managed by the game.

This change supplies assets only: the game has not been switched to this map. Collision meshes and navigation meshes are not included. Structural checks do not constitute an in-game or GPU import test.

## Rebuild

From any working directory: `python Assets/Map/Source/generate_map.py` (adjust the path to this script if needed). Rebuilding replaces the generated model, texture, preview and metadata.

## Provenance

Created for this project with deterministic local geometry and procedural textures; no extracted Riot map assets or external asset packs were used. Seed: 71. No paid generation services were used. This provenance statement does not apply to other files in the repository.
