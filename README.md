## Running locally

Serve the repository root over HTTP. For example, if Python is installed:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/`. The Python server does not apply `vercel.json`; use `http://localhost:8000/settings/` to open settings directly. The arena's `/settings` link may be redirected to that directory by the local server.

Use a browser with WebGL and JavaScript module/import-map support. Internet access is required to fetch Three.js: the import map pins both `three` and `three/addons/` to version `0.165.0` on jsDelivr. Opening the HTML with `file://` can prevent model or module loading.

For static hosting, publish the repository root with its asset directories intact. Hosts other than Vercel need an equivalent `/settings` route or directory handling. Navigation uses root-relative URLs, so deployment beneath a URL subdirectory requires changes to the links and routing.

## Scripts and checks

Runtime champion audio lives in `scripts/audio/garen-audio.js`. Keep this module deployed: the game imports it. Its sound URLs resolve to `Assets/Audio/Garen_Audio/` relative to the module location.

Development checks live in `tests/`; the browser does not load these files. Run from the repository root:

```sh
node tests/test-audio.mjs
node tests/test-justice.mjs
node tests/test-citadel.mjs
node tests/test-dummy.mjs
```


## Target dummies

The game loads `Assets/Objects/target_dummy.glb` once, then clones its skeleton for each target. Each copy has an independent animation mixer controlled by `scripts/objects/dummy-animations.mjs`. Spawn plays on initial appearance and respawn; the three supplied idle clips cycle between hits; Hit restarts on nonlethal damage; lethal damage plays Death to completion and hides the target. Targets retain 10 HP, collision, health bars and the four-second respawn delay (respawn waits if the champion occupies their position). The visuals normalize to 2.2 units high without modifying the source GLB or its clips.

## Roaming champions

Lux and Jarvan IV load from `Assets/Champs/lux.glb` and `jarvan_iv.glb` as non-combat NPCs. `scripts/npcs/roaming.mjs` owns landmark navigation and reactions; `champion-npcs.mjs` loads and animates the models. Both use Idle1–Idle4 and Run at its original 1× animation speed, traveling at 4.5 units/second (the normal player speed). A cumulative activity budget targets 30% actual movement and 70% stationary time, with a four-second initial pause. After each trip, the idle wait is calculated from actual travel time; emotes and blocked movement count as stationary. Reactions and safety can temporarily lower the moving share. Destinations are the citadel hall, central square, both fountains and the dummy training section. Routes use the map collision layout plus dummy footprints and enter the hall through its doorway.

Within 4 units and clear line of sight, a fresh approach rolls a 30% chance of Joke. Leaving beyond 6 units rearms that encounter. Each player dance has its own ID: a nearby NPC within 7 units rolls once for Dance (50%) or Laugh (50%), including when entering range during that dance. Dance reactions take priority over jokes. NPCs stop, face the player's position before the clip starts, finish the emote once, then idle before roaming again. Reaction rolls are independent for each NPC. Run root drift is removed at runtime; source GLBs remain unchanged.

Run `node tests/test-npcs.mjs` for landmark connectivity, swept collision checks, reaction probabilities and encounter gating, facing, recovery, a long roaming simulation, and required clips in both GLBs.

NPCs have solid 0.55-unit-radius bodies. Player movement projects out of these bodies using the same substeps and wall validation as dummy collisions. NPC movement checks swept circles against the player and other NPCs; after two seconds blocked, it replans around their current positions or chooses another landmark. NPCs remain non-combat characters.
