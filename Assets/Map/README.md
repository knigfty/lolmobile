# Demacian Citadel

Active map: `Models/demacian_citadel.glb`. Original, stylized architecture inspired by the two castle references: pale masonry, blue domes, gilded ribs, a high sanctum, curtain walls, lancet windows, guardians, gardens, and reflecting fountains. This is a new procedural interpretation, not an extracted game map or exact reconstruction.

## Organization

- `Models/demacian_citadel.glb`: self-contained map with embedded 1024 × 1024 texture atlas.
- `Textures/citadel_atlas.png`: editable copy of the embedded atlas.
- `Source/generate_citadel.py`: deterministic geometry, texture, layout, validation and preview generation (Python + numpy + Pillow).
- `Metadata/citadel-layout.json`: wall bounds, spawn, and solid building/fountain footprints; loaded by the game.
- `Metadata/citadel-validation.json`: geometry and file checks.
- `citadel-collision.mjs`: player-radius collision and sliding helpers.
- `Previews/citadel_overview.png`, `Previews/citadel_courtyard.png`: software renders of the exported geometry; not screenshots of the running game.

The earlier `forest_courtyard` model, texture, preview, generator and metadata remain available as the previous map. The game now loads only the citadel.

## Play area and camera

The enclosing walls span 64 × 76 game units. The playable rectangle follows their inside faces, with an additional player-radius inset. Towers, the keep, palace wings, fountains and guardian plinths are solid. The southern gate is closed. All courtyard movement remains at Y=0. The palace interior and wall-top walkways are decorative and inaccessible.

The player spawns at (0, 0, 12). Training dummies stay near the center. Scenery extends roughly 260 units across, beyond the walls, with cliffs, trees and mountain silhouettes. The camera is allowed outside player bounds. Mouse-wheel or two-finger pinch changes zoom; architecture obscuring the champion fades while retaining collision. Shadows follow the player, and the camera far plane/fog range cover the larger scene.

## Generation and validation

Run `python Assets/Map/Source/generate_citadel.py` from the repository root. Replaces citadel outputs in the folders above. Run `node test-citadel.mjs` to check enclosed movement, solid landmarks, spawn clearance, GLB structure, and upward courtyard normals. The export asserts positive signed volumes for closed architectural meshes, keeps the foundation below the paved ground to avoid overlapping faces, and embeds the PNG so no external textures are needed.

Software previews and structural tests do not verify GPU rendering or performance on a real phone. The runtime metadata accurately reports whether an in-engine import has been tested.

## Provenance

Original local geometry and procedural textures, seed 211. User-provided `Demacia_Citadel.jpg` and `demacia-foreground.jpg` guided architectural shapes and colors; they are not embedded or redistributed. No extracted Riot meshes, external asset packs, or paid generation services were used. Demacia and League of Legends remain associated with their respective rights holders. This provenance statement applies only to this new map.
