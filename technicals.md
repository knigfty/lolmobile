# Developer technical guide — LM ARENA

Updated: 2026-11-11. Describes the implementation on `main`, including citadel NPC spawns and the walkable throne platform.

## Project overview

LoL Mobile is a mobile-based, single-player 3D playground with support for desktop controls. The player moves around an arena map. A separate settings page configures champion stats and keyboard bindings.

The application is a static site with no backend, database, player authentication, package manifest or build step. The main pages contain HTML/CSS and gameplay JavaScript; shared ES modules implement audio, collisions, dummy animations and NPC behavior. Node-based checks live in `tests/`. Public titles use **LM ARENA**; Garen asset names and `garen.*` storage keys remain internal compatibility identifiers.

## Repository layout

| Path | Purpose |
| --- | --- |
| `index.html` | Arena UI, scene, camera/POV, controls, combat and frame loop. |
| `settings/index.html` | Attack speed, first/third-person selection and key bindings; fixed Back to arena button. |
| `Assets/Champs/garen.glb` | Player model and animations. |
| `Assets/Champs/lux.glb`, `jarvan_iv.glb` | Animated non-combat NPCs. |
| `Assets/Objects/target_dummy.glb` | Independently animated training targets. |
| `Assets/Objects/garen_sword.glb` | Dedicated first-person sword viewmodel. |
| `Assets/Map/Models/demacian_citadel.glb` | Current rendered citadel and courtyard. |
| `Assets/Map/Metadata/citadel-layout.json` | Spawn, bounds, obstacle footprints and walkable tread heights. |
| `Assets/Map/citadel-collision.mjs` | `containsPosition`, `constrainPosition`, `groundHeight`. |
| `Assets/Map/Source/generate_citadel.py` | Deterministic map generator (Python, NumPy, Pillow). |
| `Assets/Map/Textures/`, `Previews/`, `Metadata/` | Map texture, generated previews and validation metadata. |
| `scripts/npcs/roaming.mjs` | Landmark navigation, activity budget and social reactions. |
| `scripts/npcs/champion-npcs.mjs` | GLB loading, model normalization, mixers and body registration. |
| `scripts/npcs/body-collision.mjs` | Swept circles, overlap tests and body separation. |
| `scripts/objects/dummy-animations.mjs` | Spawn/idle/hit/death animation transitions. |
| `scripts/audio/garen-audio.js` | Player voice, combat SFX and dance audio. |
| `Assets/Audio/Garen_Audio/` | Runtime Ogg audio assets. |
| `tests/` | Audio, Justice, map, dummy, NPC and throne regression checks. |
| `AGENTS.md` | Direct-to-main workflow; no PRs or feature branches unless requested. |
| `vercel.json` | Rewrites `/settings` to `/settings/index.html`. |

Other champion GLBs, Blender/FBX sources, map kit assets and reference images are present but are not automatically spawned. `Assets/References/` is excluded from Vercel deployments by `.vercelignore`.

## Startup and rendering

The module in `index.html` imports Three.js and `GLTFLoader`, then builds the renderer, environment, targets, and player group. It also reads preferences and registers input listeners before loading game assets. The import map pins Three.js and its addons to `0.165.0` on jsDelivr.

The renderer uses antialiasing, a device-pixel-ratio cap of 2, soft shadows, sRGB output, and ACES filmic tone mapping. The scene contains hemisphere and directional lighting, fog, the loaded citadel GLB, skinned target dummies and animated champion models. No physics engine is used.

Startup loads the map layout (`?v=3`), map GLB (`?v=2`), target dummy, Lux and Jarvan, then the player. Retired `TrainingInlays` are removed from the map scene. NPC GLBs load in parallel; a failed required asset leaves an explanatory loading screen.

`GLTFLoader` normally loads `./Assets/Champs/garen.glb`. There is also a fallback code path for a base64 GLB inside an element named `embedded-model`; that element is not included in the current page. On success, `start(gltf)` attaches the model, enables mesh shadows and double-sided materials, disables mesh frustum culling, and registers every animation clip with an `AnimationMixer`. It starts `Idle1_Base`, loads the separate first-person sword, then removes the loading overlay and begins `animate()`. The sword is required even if the initial POV is third person. On failure, `fail()` logs the error and leaves an explanatory loading screen.

Each animation frame:

1. Advances a simulation clock with a delta capped at 0.05 seconds.
2. Updates the run spell, attack recovery and queued attacks, and spin expiration.
3. Reads movement, handles action cancellation and attack holds, and moves the player.
4. Sets player elevation from `groundHeight`, then updates targets and NPCs.
5. Updates animation blending and the player mixer.
6. Updates camera look, POV-specific weapon animation, shadow tracking and architecture occlusion, then renders.

## Camera and first-person sword

The camera uses a 55-degree perspective field of view. Third person is the default. Canvas drag acts as a virtual look stick: holding away from the drag origin keeps turning. The deadzone is 5 pixels, full-speed displacement is 140 pixels and maximum angular speed is 2.5 radians/second. Wheel or two-finger pinch changes the third-person orbit distance between 2.5 and 300 units; dragging changes view direction, not zoom. The camera can look outside the closed walls without moving the player outside them.

First person aligns the player's combat facing to camera yaw and puts the eye at the player's ground height plus 1.65 units. The player model stays animated for gameplay but is hidden from rendering; the dedicated sword viewmodel is shown. The sword is normalized to 1.85 units high about its grip. Its resting pitch blends from 10° idle to 20° moving, and the run spell raises it to 45°. Portrait-specific offsets keep the blade visible.

Basic attacks swing down from top-right (`Attack1`) and top-left (`Attack2`). The top-left attack has a steeper downward follow-through. Viewmodel motion follows the same attack duration and 17.55% hit phase as combat. Empowered strike uses a raise/plunge at its 45% impact, spin sweeps the horizontal blade without spinning the camera, and Justice has its own sword pose. These visual movements do not add separate damage or root movement.

Both POVs follow throne-step elevation. First-person dummy proximity handling protects the near plane; architecture groups between camera and player fade using raycasts, with extra near-eye handling. Hall roof visibility also depends on whether the player is inside the hall. Resize updates projection, renderer dimensions and pixel ratio.

## Coordinates, movement, and collision

Gameplay runs on world X/Z; Y is height. The character faces local +Z. Keyboard and joystick input combine in `movementInput()`, with a 0.14 threshold and normalization to prevent faster diagonals. Movement is camera-relative in both POVs. Normal travel is 4.5 units/second, with smoothed facing except during target-facing actions or first-person alignment.

The old 10.9-unit arena limit is removed. `citadel-layout.json` defines the closed courtyard bounds: X -30.5 to 30.5, Z -36.5 to 36.5, inset by body radius. Player spawn is `(0, 0, 12)`. Circle and box footprints constrain walls, towers, fountains, palace wings, hall pillars/guardians and the throne chair. The citadel hall is entered through its southern doorway; the outer gate stays closed. Only authored collision footprints are solid—collision is not generated automatically from every rendered mesh.

| Body | Radius | Behavior |
| --- | ---: | --- |
| Player | 0.4 | Substepped movement, up to eight projection passes, rollback if still blocked. |
| Living dummy | 0.8 | Blocks the player; dead/hidden targets do not. |
| Lux / Jarvan | 0.55 | Solid to player and each other; NPC sweeps also avoid the player. |

`movePlayer` separates against live dummies and NPC bodies while applying map constraints. NPC navigation always reserves dummy footprints, including during death/respawn, and checks dynamic bodies before moving. After two seconds blocked, NPCs attempt a route around current bodies or abandon that trip for another landmark. This is custom circle/box collision and routing, not a physics engine.

### Walkable throne platform

The whole-dais blocking box has been removed. Five `walkable_surfaces` match the existing `ThroneSteps` geometry, with heights 0.24, 0.46, 0.68, 0.90 and 1.12 units. `groundHeight(position, layout)` returns the highest tread under an actor's X/Z position, or the ground height (0) elsewhere. Player and NPC feet follow this height when climbing or descending. The chair/back footprint remains solid at X -0.9 to 0.9, Z -27.55 to -26.6; guardian statues remain obstacles. The generator exports matching surface metadata on rebuild. No GLB replacement was required for this change.

## Controls

| Action | Default keyboard input | Touch input |
| --- | --- | --- |
| Move | WASD or arrow keys | Left joystick |
| Attack | Space | ATTACK |
| Run spell | Hold attack while moving | Hold ATTACK while using joystick |
| Spin | E | SPIN |
| Justice | R | JUSTICE |
| Dance | F | DANCE |
| Look | Drag on canvas | Drag on canvas |
| Third-person zoom | Mouse wheel | Two-finger pinch |
| POV | Settings → Point of view | Settings → Point of view |

The arena shows the keyboard hint and hides the joystick/action buttons by default. On devices whose primary pointer is coarse (typically phones and tablets), the CSS `pointer: coarse` media query shows the touch controls and hides the keyboard hint, including in landscape orientation. This follows input capability rather than viewport width; resizing a desktop window does not enable touch controls.

Keyboard matching uses `KeyboardEvent.code`, so bindings represent physical keys. Repeated keydown events do not retrigger actions. The arena ignores keydown events with Ctrl, Meta, or Alt held. Pointer capture supports holding attack or dragging the joystick beyond its initial bounds. Window blur clears held keys, attack input, and joystick movement.

The controls hint is generated from the loaded bindings. A `pageshow` listener reloads bindings and POV, rebuilds the movement-key set, and clears held keys when returning to the arena.

## Action and animation state

State is stored in module-level variables rather than a formal state-machine class. Important groups are:

| State | Responsibility |
| --- | --- |
| `actions`, `current`, `mixer` | Clip lookup, current animation, and playback. |
| `now`, `lockUntil` | Simulation-time action gating. Infinite locks are explicitly released by action-specific logic. |
| `activeAttackName`, `attackStartedAt`, `attackUntil`, `attackReadyAt` | Attack animation, recovery, and next legal attack time. |
| `attackRequested`, `pendingAttackCommand` | Buffered attack requests and commands during an attack. |
| `activeSpinName`, `spinStartedAt`, `spinUntil` | Spin playback and expiration. |
| `runSpellArmed`, `runSpellUntil`, `runSpellReadyAt` | Run-spell availability, boost lifetime, and cooldown. |
| `spell1Target`, `spell1Until`, `pendingSpellCommand` | Empowered-strike target, recovery, and queued command. |
| `dancing`, `playerDanceId` | Dance intro/loop, cancellation and per-performance NPC reactions. |

`play()` selects clips, updates the action label, and configures looping or one-shot playback. Attack-to-idle and attack-to-attack transitions use explicit normalized animation weights over 0.12 seconds; other transitions use mixer fades.

The code expects these exact GLB clip names:

```text
Idle1_Base
Run_Base
Attack1
Attack2
Run_Spell1
Spell1
Spell3_0
Spell4_Base
Dance_Base
Dance_Loop_BASE
```

Replacing the model requires preserving these names or updating all references. Although `play()` skips missing clips, several ability functions directly access clip durations and require those clips to exist.

### Basic attacks

Basic attacks alternate between `Attack1` and `Attack2`. Their playback speed is scaled to the configured attack duration: 1.5 seconds by default, otherwise the inverse of the configured attacks per second, capped at 2.5 attacks per second.

Damage runs through a timeout at 17.55% of the attack duration. At that point, the code snapshots all living, visible targets within 2.45 units and a forward cone with a total angle of 135 degrees, then damages every matching target. Basic attacks can therefore hit multiple targets.

Another attack can be buffered after half the active attack's recovery window. Holding movement when an attack begins queues movement and shortens recovery to half its normal duration; a fresh movement command cancels an active attack immediately and clears its pending damage timer. The next attack still respects `attackReadyAt`.

### Run spell and empowered strike

Holding attack for at least 120 ms while moving attempts to arm the run spell once the current action permits it. The boost lasts 2.5 seconds and multiplies movement speed by 1.35. While armed, the code automatically finds the nearest living target within 3 units and a 90-degree forward cone, faces it, and plays `Spell1`.

The empowered strike applies one damage at 45% of the clip duration if the target remains within range. Movement is allowed during this strike, with its speed multiplier decreasing from 1 to 0.2 across the strike window. Queued commands can shorten recovery to 0.2 seconds before the clip's normal end. The eight-second cooldown begins when the strike ends, or when the unused boost expires.

### Spin

Spin repeats `Spell3_0` at the asset's original playback speed for three seconds. Seven scheduled pulses each damage every living, visible target within 3 units. Movement remains enabled during the spin. Spin has no separate cooldown in the current implementation.

### Justice

Justice selects the nearest living target in the basic attack's forward cone, turns toward it, and plays `Spell4_Base`. Its range constant is currently **800 world units**, effectively covering the arena. It displays `NO TARGET IN FRONT` if selection fails. Justice deals **5 HP** to the selected target at 45% of `Spell4_Base` duration and plays impact audio on the same tick. The `false` passed to the generic action helper prevents that helper from scheduling generic damage; it does not disable Justice's explicit damage timeout. Dead/hidden targets are skipped at impact.

### Dance

Dance plays `Dance_Base` once, then switches to `Dance_Loop_BASE` when the mixer emits the intro's finished event. Movement cancels dancing. Attack initiation also cancels it; other action gating depends on the calling function, so dance does not share one universal interruption rule.

## Targets and damage

Five stationary training targets occupy X/Z `(-23,20)`, `(-17,20)`, `(-20,23)`, `(-23,26)` and `(-17,26)`. Each has 10 HP. `damageTarget(t, damage=1)` increments the global hit counter once per damage event; Justice removes 5 HP but counts as one hit.

The dummy GLB is loaded once and cloned with `SkeletonUtils.clone`, giving every copy independent bones and an animation mixer. Models normalize to 2.2 units high. `Spawn` plays initially and on respawn, idle-named clips cycle, `Hit` restarts on nonlethal damage, and `Death` plays to completion before hiding the group. The supplied death clip is 1.5 seconds. This replaces the old procedural target collapse/rubble behavior.

Red/green plane health bars face the camera at Y 2.55 and show for three seconds after damage. Respawn eligibility is the later of four seconds or death duration plus 0.5 seconds, and waits while the player overlaps the target. NPC routing reserves the dummy footprint throughout.

## Lux and Jarvan IV NPCs

Both are non-combat scene characters, not attack targets or alternate playable champions. Lux spawns inside the citadel at X/Z `(-3,-21)` and Jarvan at `(3,-21)`. They have independent skeletons, mixers, activity clocks and reaction rolls.

`champion-npcs.mjs` normalizes by head height rather than weapon bounds: Lux 1.72 units, Jarvan 1.90. Animation clips are cloned; horizontal root translation is held at the root's rest value so navigation owns travel, while vertical motion remains animated. Each model must supply `Idle1`–`Idle4`, `Run`, `Joke`, `Dance` and `Laugh`; missing required clips fail loading. Both use their embedded unlit materials. The source GLBs are unchanged.

### Navigation and movement budget

| Landmark | X | Z |
| --- | ---: | ---: |
| Citadel hall west / Lux spawn | -3 | -21 |
| Citadel hall east / Jarvan spawn | 3 | -21 |
| Central square | 0 | 8 |
| West fountain | -20 | 7 |
| East fountain | 20 | 7 |
| Dummy training | -20 | 29.5 |
| Throne platform | 0 | -25.9 |

Destinations are selected from these authored stops, not arbitrary map coordinates. A visit bag avoids repeatedly selecting the same landmark. Navigation builds a one-unit grid, uses A* when a direct segment is blocked, and smooths routes only when swept-circle clearance is valid. Static neighbors are cached. All 49 ordered landmark route combinations are covered by checks.

`Run` plays at native **1× animation speed**, with **4.5 units/second** travel. Idle1–Idle4 cycle while stationary. A four-second initial pause precedes roaming. After a trip, the idle duration is `max(0, movingTime / 0.3 - elapsed)`: the long-term target is **30% actual moving time / 70% stationary time**. Successful distance divided by movement speed contributes to moving time; blocked motion does not. Emotes, route transitions and blockage can temporarily shift the ratio. This replaces the original fixed 40–70 second waits and slowed Run playback.

### Player reactions

| Trigger | Outcome | Repeat control |
| --- | --- | --- |
| Fresh approach within 4 units, with clear line of sight | 30% `Joke`; otherwise no reaction | Rearms after separation exceeds 6 units; failed rolls do not retry every frame. |
| Player dancing within 7 units, with clear line of sight | 50% `Dance`, 50% `Laugh` | One roll per NPC per `playerDanceId`, including entry into range during an ongoing dance. |

NPCs stop and turn toward the player's current position before an emote starts. They play the reaction once, then return to the idle/roaming schedule. Facing is set at reaction start, not continuously tracked. Dance reactions take priority over proximity jokes and can interrupt an existing reaction. NPCs have no dedicated voice/audio integration yet.

## Player audio

`scripts/audio/garen-audio.js` resolves Ogg files under `Assets/Audio/Garen_Audio/`. It connects movement, alternating attack cast/hit, run-spell activation/strike, spin cast/end/hit, Justice cast/hit and dance intro/loop to gameplay events.

Combat SFX are independent full-length one-shots and may overlap. One voice channel prioritizes idle < movement < attack < spell < ultimate; equal/higher priority replaces the current voice and lower priority is rejected. Movement voice has a 15-second cooldown after completion/interruption. Dance audio uses the voice channel; a generation token prevents an old music loop from restarting after dance cancellation or restart. Browser playback rejection is handled without blocking gameplay.

## Settings and persistence

Both pages use local storage on the same origin. Preferences are device/browser-local and have no server synchronization.

| Key | Format | Behavior |
| --- | --- | --- |
| `garen.attackSpeed` | Numeric string | Settings accepts 0.67–2.50 attacks per second in 0.01 steps. Arena treats 0.67 as an exact 1.5-second duration. |
| `garen.pov` | `first` or `third` | Third person by default; reloaded on `pageshow`. |
| `garen.controls` | JSON object mapping action names to arrays of key codes | Movement actions have two bindings each; attack, spin, dance, and justice have one each. |

The settings Back to arena link is fixed near the top with safe-area spacing and remains visible while scrolling.

Both pages duplicate the control defaults, key-code validator, preference loader, and display-label conversion. Keep these implementations synchronized when changing the binding schema. Invalid arrays, unsupported codes, or duplicate assignments cause the loader to fall back to defaults. The settings editor rejects conflicts and modifier combinations, supports Escape to cancel, and saves each successful change immediately. Storage failures display a message in settings; the arena falls back to defaults.

Attack duration is calculated once when the arena module loads. Unlike controls, it is not refreshed by `pageshow`, so returning via browser history with a restored page may retain the previous attack speed until a reload. No `storage` event listener synchronizes open tabs.

## Timing considerations

There are three timing mechanisms: capped simulation time (`now`), wall-clock seconds from `performance.now()` (`inputTime()`), and browser timeouts for damage, spin pulses, and toasts. They serve different purposes and should not be substituted without checking action recovery and cancellation behavior.

Active basic-attack and spin animation positions are explicitly synchronized to wall-clock elapsed time after mixer updates so frame gaps do not stretch their intended duration. Background-tab throttling can still delay timeout callbacks, while simulation-time locks advance only through rendered frames.

## Working on the project

For gameplay changes, start with the constants and action helpers in `index.html`, then trace their updates through `animate()`. For preference changes, update both HTML files and check loading, validation, saving, and return navigation. For character changes, verify clip names and model scale/orientation before adjusting combat ranges or collision sizes.

Serve the repository root over HTTP, for example `python -m http.server 8000`. With Python's server, open `/settings/` directly; Vercel supplies the `/settings` rewrite. Three.js is fetched from the CDN, so an internet connection is required. Deploy the static root with all runtime modules and assets intact.

Run the existing checks from the repository root (Node required):

```sh
node tests/test-audio.mjs
node tests/test-justice.mjs
node tests/test-citadel.mjs
node tests/test-dummy.mjs
node tests/test-npcs.mjs
node tests/test-throne.mjs
```

These cover audio priority/cancellation and asset paths, Justice impact, map collision, dummy animation transitions, landmark connectivity, social reaction boundaries/debouncing/facing, movement-budget simulation, body collision, and platform height agreement with the GLB. They are script-level checks, not a full rendered browser test suite. Additional local Three.js parsing/mixer checks have used stubbed texture decoding; those do not prove visual correctness.

Manual checks still needed after gameplay/rendering edits:

1. Verify required models, CDN modules and audio load without console errors.
2. Test touch/keyboard controls, camera-relative movement, both POVs, portrait sword framing, look drag and zoom.
3. Check attack alternation/timing, buffering, cancellation, empowered strike, spin pulses and Justice's 5-HP impact.
4. Verify dummy spawn/hit/death/respawn and player/NPC body separation.
5. Watch both NPCs leave the citadel, visit landmarks and react once per approach/dance; verify facing before each emote.
6. Walk player and NPCs up/down the throne steps; check feet and camera height, chair collision and doorway passage.
7. Change settings, scroll to confirm the Back link stays visible, and test reload/history navigation and reset behavior.
8. Blur the window with input held and confirm it clears correctly.

Follow `AGENTS.md`: push validated changes directly to `main`; do not create feature branches or PRs unless explicitly requested. Keep map generator output and collision/surface metadata consistent. Update this guide when gameplay, paths, clip requirements or persistence change.

## Current limitations

There is no multiplayer, backend persistence, offline dependency bundle, combat AI, NPC damage system or player-champion selection. NPC movement uses custom planar pathfinding plus authored ground heights rather than a full navmesh/physics system. The 30% movement goal is a long-term schedule, not an exact ratio during repeated emotes or obstruction. NPC replanning currently adds 0.1 clearance around dynamic blockers; very close contacts can invalidate the start in that temporary layout, causing another destination to be chosen instead of the intended detour. Browser visual validation of the latest NPC/platform work remains outstanding.
