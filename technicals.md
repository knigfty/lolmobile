# Developer technical guide

## Project overview

LoL Mobile is a mobile-based, single-player 3D playground with support for desktop controls. The player moves around an arena map. A separate settings page configures champion stats and keyboard bindings.

The application is a static site: there is no backend, database, authentication, package manifest, build step, or automated test suite in this repository. HTML, CSS, and JavaScript live directly in the two HTML files.

## Repository layout

| Path | Purpose |
| --- | --- |
| `index.html` | Arena UI, styles, Three.js scene, input handling, combat, animation, and render loop. |
| `settings/index.html` | Attack-speed slider, keyboard-binding editor, and preference persistence. |
| `Assets/Champs/garen.glb` | Character scene and animation clips loaded at runtime. |
| `Garen_Audio/` | Bundled Ogg voice and sound-effect assets; currently unused by the code. |
| `vercel.json` | Rewrites `/settings` to `/settings/index.html`. |

## Startup and rendering

The module in `index.html` imports Three.js and `GLTFLoader`, then builds the renderer, environment, targets, and player group. It also reads preferences and registers input listeners before loading the model.

The renderer uses antialiasing, a device-pixel-ratio cap of 2, soft shadows, sRGB output, and ACES filmic tone mapping. The scene contains hemisphere and directional lighting, fog, procedural ground and arena meshes, decorative blocks, and procedural target meshes. No physics engine is used.

`GLTFLoader` normally loads `./Assets/Champs/garen.glb`. There is also a fallback code path for a base64 GLB inside an element named `embedded-model`; that element is not included in the current page. On success, `start(gltf)` attaches the model, enables mesh shadows and double-sided materials, disables mesh frustum culling, and registers every animation clip with an `AnimationMixer`. It starts `Idle1_Base`, removes the loading overlay, and begins `animate()`. On failure, `fail()` logs the error and leaves an explanatory loading screen.

Each animation frame:

1. Advances a simulation clock with a delta capped at 0.05 seconds.
2. Updates the run spell, attack recovery and queued attacks, and spin expiration.
3. Reads movement, handles action cancellation and attack holds, and moves the player.
4. Updates target health bars, damage feedback, destruction, and respawn.
5. Updates animation blending and the mixer.
6. Smooths the follow camera toward the player and renders the scene.

The camera uses a 55-degree perspective field of view. It sits farther back on narrow portrait screens and looks at a point above the player. Resize handling updates the camera projection, renderer dimensions, and pixel ratio.

## Coordinates, movement, and collision

Gameplay runs on the world X/Z plane; Y is height. The character faces local +Z. Screen right maps to +X and screen down maps to +Z. Keyboard and joystick inputs combine in `movementInput()`, with a movement threshold of 0.14 and normalization to prevent faster diagonal movement.

Base movement speed is 4.5 world units per second. Rotation approaches the movement direction smoothly, except while the empowered strike holds a target-facing direction.

`movePlayer(dx, dz)` implements circular collision constraints:

- Player radius: 0.4 units.
- Living target radius: 0.8 units.
- Maximum player distance from arena center: 10.9 units.
- Movement is split into small steps, then projected out of obstacles for up to eight passes per step. Unresolved steps revert to the previous position.

Dead or hidden targets do not block movement. Decorative scenery has no collision logic.

## Controls

| Action | Default keyboard input | Touch input |
| --- | --- | --- |
| Move | WASD or arrow keys | Left joystick |
| Attack | Space | ATTACK |
| Run spell | Hold attack while moving | Hold ATTACK while using joystick |
| Spin | E | SPIN |
| Justice | R | JUSTICE |
| Dance | F | DANCE |

The arena shows the keyboard hint and hides the joystick/action buttons by default. On devices whose primary pointer is coarse (typically phones and tablets), the CSS `pointer: coarse` media query shows the touch controls and hides the keyboard hint, including in landscape orientation. This follows input capability rather than viewport width; resizing a desktop window does not enable touch controls.

Keyboard matching uses `KeyboardEvent.code`, so bindings represent physical keys. Repeated keydown events do not retrigger actions. The arena ignores keydown events with Ctrl, Meta, or Alt held. Pointer capture supports holding attack or dragging the joystick beyond its initial bounds. Window blur clears held keys, attack input, and joystick movement.

The controls hint is generated from the loaded bindings. A `pageshow` listener reloads bindings, rebuilds the movement-key set, and clears held keys when returning to the arena.

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
| `dancing` | Dance intro/loop behavior and cancellation. |

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

Justice selects the nearest living target in the basic attack's forward cone, turns toward it, and plays `Spell4_Base`. Its range constant is currently **800 world units**, effectively covering the arena. It displays `NO TARGET IN FRONT` if selection fails. The action currently passes `false` for damage: Justice is an animation-only ability.

### Dance

Dance plays `Dance_Base` once, then switches to `Dance_Loop_BASE` when the mixer emits the intro's finished event. Movement cancels dancing. Attack initiation also cancels it; other action gating depends on the calling function, so dance does not share one universal interruption rule.

## Targets and damage

Five stationary targets start at `(4, -3)`, `(-4, -4)`, `(5, 5)`, `(-5, 4)`, and `(0, -7)` in X/Z coordinates. Each has 10 HP. Every `damageTarget()` call removes one HP and increments the global hit counter, including repeated spin pulses; the counter measures damage events rather than defeated targets.

Health bars use separate red and green planes and face the camera. Damage reveals the bar for three seconds, flashes the body, and tilts the target away from the player. On death, a 1.1-second collapse/rubble animation hides the target. Respawn becomes eligible after four seconds and waits until the player no longer overlaps the target's collider. HP and visuals then reset.

## Settings and persistence

Both pages use local storage on the same origin. Preferences are device/browser-local and have no server synchronization.

| Key | Format | Behavior |
| --- | --- | --- |
| `garen.attackSpeed` | Numeric string | Settings accepts 0.67–2.50 attacks per second in 0.01 steps. Arena treats 0.67 as an exact 1.5-second duration. |
| `garen.controls` | JSON object mapping action names to arrays of key codes | Movement actions have two bindings each; attack, spin, dance, and justice have one each. |

Both pages duplicate the control defaults, key-code validator, preference loader, and display-label conversion. Keep these implementations synchronized when changing the binding schema. Invalid arrays, unsupported codes, or duplicate assignments cause the loader to fall back to defaults. The settings editor rejects conflicts and modifier combinations, supports Escape to cancel, and saves each successful change immediately. Storage failures display a message in settings; the arena falls back to defaults.

Attack duration is calculated once when the arena module loads. Unlike controls, it is not refreshed by `pageshow`, so returning via browser history with a restored page may retain the previous attack speed until a reload. No `storage` event listener synchronizes open tabs.

## Timing considerations

There are three timing mechanisms: capped simulation time (`now`), wall-clock seconds from `performance.now()` (`inputTime()`), and browser timeouts for damage, spin pulses, and toasts. They serve different purposes and should not be substituted without checking action recovery and cancellation behavior.

Active basic-attack and spin animation positions are explicitly synchronized to wall-clock elapsed time after mixer updates so frame gaps do not stretch their intended duration. Background-tab throttling can still delay timeout callbacks, while simulation-time locks advance only through rendered frames.

## Working on the project

For gameplay changes, start with the constants and action helpers in `index.html`, then trace their updates through `animate()`. For preference changes, update both HTML files and check loading, validation, saving, and return navigation. For character changes, verify clip names and model scale/orientation before adjusting combat ranges or collision sizes.

There is no automated verification harness. Useful manual checks after changes are:

1. Load the arena through HTTP and confirm the model and CDN modules load without console errors.
2. Test keyboard and touch movement, diagonal speed, arena boundaries, and sliding around living targets.
3. Check attack alternation, hit timing, buffered attacks, and immediate cancellation by fresh movement.
4. Hold attack while moving; verify boost, automatic empowered strike, and cooldown.
5. Move during spin, check pulse damage, and verify target death and delayed respawn.
6. Check Justice target selection and dance intro, loop, and cancellation.
7. Save attack speed and bindings, return to the arena, and test reload/history navigation and reset behavior.
8. Resize between desktop and portrait layouts and blur the window while inputs are held.

The repository currently provides no offline dependency bundle, audio playback, multiplayer, enemy AI, or server-side persistence. The loader's error text mentions a single-file edition, but no separate edition is present in this repository.
