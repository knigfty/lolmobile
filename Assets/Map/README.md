# Royal Kingdom — playable exterior and entrance hall

The active `Models/demacian_citadel.glb` is an original procedural, stylized blockout based on the supplied `grand-city(2).png`. It establishes the complete walkable layout, not a final-detail recreation of the reference painting.

## Playable layout

- 260 × 320-unit exterior with enclosed courtyard, ceremonial plaza and central monument.
- Two curved colonnades with 60 independently collidable columns. Players can walk through the gaps; the overhead stone beams do not block ground movement.
- Eight formal garden parterres with intersecting paths, fountains, cypress trees and solid low hedges.
- Monumental citadel, blue-domed towers, front guardian sculpture, and a 12-unit-wide open front doorway.
- Entrance hall with columns, vault ribs, carpet, mosaic and a solid throne dais. The hall roof cuts away while inside; other obstructing architecture fades using the existing camera system.
- Background city and white mountain immediately behind the citadel. Background scenery, tower interiors, roofs and wall tops are not playable.

All movement remains at Y=0, including the portal and garden paths. Low edging is intentionally traversable; solid fountains, columns, walls, hedges and dais have matching collision footprints. The champion model and movement speed are unchanged: its rest-pose mesh is about 2.07 units high. The citadel roof reaches about 80 units. This is an inferred reference scale, not a surveyed reconstruction.

Spawn is (0, 0, 112), facing the central route. The existing five training targets remain in the plaza at their existing coordinates. A cached minimap tracks the player and labels the courtyard, plaza, gardens and hall. Desktop bindings, touch controls, combat, audio and settings are retained.

## Rebuild and checks

Run from the repository root:

```sh
python Assets/Map/Source/generate_citadel.py
node tests/test-citadel.mjs
node tests/test-kingdom.mjs
python tests/test-kingdom-geometry.py
node tests/test-audio.mjs
node tests/test-justice.mjs
node tests/test-dummy.mjs
```

Generation requires numpy and Pillow. The GLB embeds one 1024 × 1024 texture atlas. Pieces sharing an occlusion section are batched, reducing the map to 124 meshes and about 73,000 triangles. Tests enforce budgets of fewer than 200 meshes, 100,000 triangles and 9 MiB. These are geometry budgets, not measured phone frame rates.

`Metadata/citadel-layout.json` contains bounds, colliders, hall bounds, spawn, landmarks and six representative passage centers. Connectivity tests flood-fill the navigable map, verify cross-colonnade routes, and simulate a round trip through the portal into the hall. Existing collision and combat checks are retained.

`Previews/` contains software renders of the actual generated geometry, including a hall cutaway. They are not screenshots from the running game. `Metadata/citadel-validation.json` records geometry checks and the GLB hash. Browser/WebGL and real-device performance remain unverified because the workspace preview service was unavailable.

## Provenance

Geometry and textures are generated locally by `Source/generate_citadel.py` (seed 211), adapting the repository's original generator. No paid generation, downloaded model packs or extracted Riot meshes were used for this map. The user's reference is not embedded. Existing third-party assets elsewhere in the repository retain their own licensing. Demacia and League of Legends remain associated with their respective rights holders.
