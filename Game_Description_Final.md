# The Twilight Zone — Build Specification

> Source: Year 9 Computing Technology GDD, converted into an implementation-ready spec for an AI coding agent. Research/inspiration material has been condensed into concrete constraints; all narrative prose has been converted to explicit rules, values, and tables.

## 0. Project Summary

| Field | Value |
|---|---|
| Genre | 2D underwater cave exploration & survival, endless-runner style |
| Engine/Stack | Python 3.10+, Pygame 2.x (`pip install pygame`) |
| Window | Fixed size, 1024×768 |
| Rendering | CPU-rendered (no GPU dependency) |
| Target perf | 60 fps stable on mid-range hardware, <50 ms input-to-movement latency, <5 s load |
| Win condition | None — endless run; goal is maximum distance before death |
| Core loop | Swim through stitched pre-built cave sections, manage HP + O₂, collect items, survive as long as possible |

**Premise:** Player is a diver pulled into an underwater cave network by volcanic activity. Survive by managing health and oxygen while navigating hazards, collecting resources, and traveling as far as possible.

---

## 1. Core Systems

### 1.1 Survival Meters
- **HP**: reaches 0 → instant death.
  - Damage sources: hostile fish contact, spiky plant contact, thermal vent proximity/eruption.
- **Oxygen (O₂)**: depletes passively while in water.
  - At 0: screen fades to black over **3 seconds** (recovery/grace window), then death occurs if not resolved.
  - O₂ tanks (consumable, hotbar item) restore oxygen when used, then are discarded (removed from world, not redroppable).

### 1.2 Movement & Collision
- Omnidirectional swimming on a 2D plane: up/down/left/right, always available.
- Cave walls: simple polygon collision boundaries, block all movement.
- Wall contact triggers: camera/screen nudge + scraping sound effect.

### 1.3 Hotbar & Inventory
- 5 hotbar slots total.
- Selection: keys `1`–`5` (direct select) or scroll wheel (cycle).
- Active item use: `Q` or `Z`.
- Auto-pickup: item is collected automatically when player enters its pickup radius **and** a hotbar slot is free.
- Picked-up-then-dropped items cannot be re-collected for **3 seconds**.
- Reordering: in the Pause & Inventory Manager, hold `Shift` + select 2 slots → contents swap.
- No large storage grid — hotbar only (deliberate simplification vs. Subnautica reference).

### 1.4 Hazards

| Hazard | Trigger | Effect |
|---|---|---|
| Thermal vents | Player proximity; vent periodically erupts | Heat damage (continuous near-vent + spike on eruption); orange screen wash while taking damage |
| Silt clouds | Player enters cloud | Visibility drops to near-zero; vignette darkening |
| Water currents | Player enters current zone | Pushes player velocity in current direction; player sprite wobble animation; bubble stream indicates direction |
| Hostile fish | Collision with player | HP damage; fish patrol in straight lines until player enters detection range, then engage. Fish cannot be killed by the player (no combat) |
| Spiky plants | Collision with player | HP damage (static hazard) |

### 1.5 Progression / Content Variation
- No full procedural generation. Instead: a library of **pre-built cave section chunks** with standardized entry/exit points, randomly stitched together at runtime to vary each run.
- Hidden lore rooms contain text-overlay lore fragments (exploration reward, non-mechanical).
- Progress metric: distance traveled, tracked as a personal high score.

---

## 2. Controls

| Input | Action |
|---|---|
| `W`/`A`/`S`/`D` or Arrow Keys | Swim (4-directional, 2D plane) |
| `Q` or `Z` | Use active hotbar item |
| `Esc` | Open/close Pause & Inventory Manager |
| `1`–`5` | Select hotbar slot directly |
| Scroll wheel | Cycle hotbar slot forward/backward |
| Mouse click | Menu/UI interaction (buttons, overlays) |
| Hold `Shift` + select 2 slots | Swap hotbar item positions (in Pause menu) |

Implementation note: use Pygame's `KEYDOWN`/`KEYUP` events for movement and hotbar selection, and the `MOUSEWHEEL` event for scroll cycling.

---

## 3. Game State Machine

```
MAIN_MENU
  ├─ Play clicked → CONFIRM_NEW_RUN overlay
  │     ├─ Yes → load random start cave section, reset survival stats → GAMEPLAY
  │     └─ No  → MAIN_MENU
  └─ Settings (shown inline on main menu, no separate screen)
        toggle colourblind mode / adjust Master, Ambience, Menu, Game volume
        → writes to local config file on change

GAMEPLAY
  ├─ Esc → PAUSED (Pause & Inventory Manager)
  ├─ HP == 0 → DEATH_SCREEN (cause: combat/hazard)
  └─ O2 == 0 → 3s fade-to-black → if not recovered → DEATH_SCREEN (cause: drowning)

PAUSED (Pause & Inventory Manager)
  ├─ "X" button → resume GAMEPLAY
  ├─ Shift + select 2 slots → swap items, stay in PAUSED
  └─ Quit → CONFIRM_QUIT overlay
        ├─ Yes → discard run state, check/save high score → MAIN_MENU
        └─ No  → PAUSED

DEATH_SCREEN (shows distance travelled + cause of death; writes high score if beaten)
  ├─ Yes/Restart → new run (fresh pre-built section stitch, reset stats) → GAMEPLAY
  └─ No → MAIN_MENU
```

All confirmation overlays (new run, quit) darken the background and block interaction with the screen beneath until resolved.

---

## 4. UI Requirements

- **Visual style**: dark, atmospheric, consistent across all screens.
  - Cave environments: deep blue-green palette, warm orange/red accents reserved for thermal hazards.
  - Menus/UI panels: muted dark backgrounds, bold white or teal text.
  - Shared icon set, font, and layout grid across HUD, Inventory, Pause menu, Death screen, Main Menu.
- **Pause & Inventory Manager**: overlay with close ("X") button in a corner; 5 hotbar slots shown along the bottom; item-swap via Shift+select-2.
- **Feedback/alerts** (every critical event needs a paired visual + audio cue):
  - Damage → red vignette flash
  - Low O₂ → oxygen bar pulses
  - Thermal vent damage → warm orange screen wash
  - Confirmation overlays → background dims
- **Main Menu**: Play and Exit buttons; Settings shown inline (no separate Settings screen).
- **Death screen**: shows distance travelled + cause of death, then Restart / Main Menu choice.

---

## 5. Functional Requirements (flattened)

| ID | Requirement | Spec |
|---|---|---|
| F1 | Omnidirectional swimming | WASD/arrows, 2D plane, always active |
| F2 | Solid wall collision | Polygon boundaries; blocks movement; nudge + scrape SFX |
| F3 | HP system | Bar; 0 HP = instant death |
| F4 | O₂ system | Passive drain; 0 O₂ = 3s fade to black, then death |
| F5 | 5-slot hotbar | Keys 1–5 or scroll wheel to select |
| F6 | Auto-pickup + Pause/Inventory Manager | Auto-collect on proximity + free slot; Esc opens manager; 3s re-pickup cooldown on drops |
| F7 | Consumables | Med kits restore HP; O₂ tanks restore O₂ and are discarded after use |
| F8 | Thermal vents | Periodic eruption; heat damage; orange flash cue |
| F9 | Silt clouds / low visibility | Vignette darkening, near-zero visibility |
| F10 | Water currents | Push velocity + directional bubble stream + wobble animation |
| F11 | Flora/fauna hazards | Spiky plants + patrolling hostile fish deal HP damage on contact; fish not killable |

### Mode / Menu Requirements

| ID | Requirement | Spec |
|---|---|---|
| M1 | Game mode | Single arcade "max distance" mode; Play → confirm overlay → run start |
| M2 | Death screen | Distance + cause of death; Restart / Main Menu |
| M3 | Pause & Inventory Manager | Pauses gameplay; 5 hotbar slots; Shift+2-slot swap; "X" resumes |
| M4 | Quit confirmation | From Pause menu; Yes → Main Menu (+ save high score if beaten); No → back to Pause menu |
| M5 | Settings | Inline on Main Menu: colourblind toggle; Master/Ambience/Menu/Game volume sliders |
| M6 | Persistent menu layout | Main Menu = Play + Exit buttons; confirmation overlays appear above, pausing background interaction |

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | ≥60 fps stable on mid-range hardware, including multiple fauna + low-visibility effects on screen |
| Latency | Input-to-movement latency < 50 ms |
| Load time | Full load < 5 seconds; assets loaded fully into RAM at level start; keep asset files compact |
| HUD readability | HP/O₂ bars stay legible during silt-out and heat-flash visual events |
| Onboarding | New player should understand core controls + at least 2 hazard types within first playthrough, no external instruction |
| Feedback | Every critical event (damage, O₂ depletion, death) has both a visual and audio cue |
| Extensibility | Level architecture supports adding biomes/flora/fauna/hazards via data files only, no core engine rewrites |
| Privacy | No login/account/network required; no PII collected; save data + high scores stored in a local file only, never transmitted |
| Stability | Crashes during gameplay must not corrupt save data |

---

## 7. Architecture Guidance

- **Component-based architecture**: separate core engine (physics, rendering, input) from game-specific logic (survival systems, level data, hazard behavior). New content = new data/component definitions, not engine changes.
- **Data-driven tuning**: store O₂ drain rate, heat damage threshold, per-biome enemy speed, and other survival parameters in editable data files (e.g. JSON/YAML), not hardcoded.
- **Modular cave chunks**: standardized entry/exit points so pre-built sections can be stitched together reliably at runtime.
- **Testing**: unit-test HP, O₂, inventory, and collision systems independently before integration; full playthroughs per level section to catch unwinnable states/softlocks.
- **Asset consistency**: fixed pixel-art resolution and palette; consistent audio loudness; documented style guide for fonts/icons/spacing.

---

## 8. Hardware / Software Requirements

| Category | Requirement |
|---|---|
| OS | Any platform supporting Python 3 (Pygame is cross-platform) |
| CPU | Pygame is CPU-rendered; no GPU required |
| RAM | 4 GB target (sprites/audio loaded fully into RAM) |
| Storage | ~50 MB for Python + Pygame, plus game assets |
| Display | Fixed window, 1024×768 |
| Input | Pygame event system; `MOUSEWHEEL` for hotbar scroll |
| Dependencies | Python 3.10+, Pygame 2.x — `pip install pygame` |

Reference: https://www.pygame.org/docs/

---

## 9. Data Flow (event → process → output)

| Trigger | Process | Output |
|---|---|---|
| Game launch | Init display/audio/input; load shared assets; read save file | Main Menu rendered, music playing, buttons active |
| Click Play | Load confirm overlay | "Start new run?" prompt |
| Confirm Yes | Select + load random pre-built cave section; reset survival stats | Gameplay begins |
| Confirm No | Remove overlay | Return to Main Menu |
| Toggle colourblind | Update setting + palette conversion; write config | Colourblind visuals applied |
| Adjust audio slider | Update mixer volume + config | Volume changes live |
| Movement key held | Compute movement vector; update velocity; check collision each frame | Player swims |
| Wall collision | Detect overlap; cancel movement; trigger nudge + scrape SFX | Player stopped, feedback shown |
| Vent eruption | Apply heat damage; show orange overlay | Damage + visual cue |
| Enter silt cloud | Enable visibility reduction; increase vignette | Near-zero visibility |
| Enter current | Apply push to velocity; enable wobble animation | Player pushed, visual cue |
| Fish/plant collision | Detect hazard collision; reduce HP; trigger damage feedback | HP drops, red flash |
| HP below warning threshold | Enable heartbeat audio loop + HP bar flash | Low-health warning |
| O₂ depletes to 0 | Start black-fade sequence + recovery timer | Screen fades to black |
| Recovery timer expires | Trigger death state; record cause | Death screen opens |
| Item enters pickup range (slot free) | Detect overlap; add to hotbar; play pickup SFX | Item appears in hotbar |
| Item enters pickup range (hotbar full) | Free-slot check fails | Item stays in world |
| Esc pressed | Set game state to paused; halt gameplay logic | Pause & Inventory Manager shown |
| Shift + select 2 slots | Recognize 2 selections; swap on release | Hotbar reorganized |
| Click Quit (in Pause menu) | Open confirm overlay; disable background interaction | "Are you sure?" shown |
| Confirm Quit Yes | Clear run state; check/save high score | Return to Main Menu |
| Confirm Quit No | Close overlay | Return to Pause & Inventory Manager |
| HP reaches 0 | Trigger death state; store cause; halt gameplay | Death screen displayed |
| Death screen "Yes" | Load new stitched cave sections; reset stats | New run begins |
| Death screen "No" | Clear gameplay state | Return to Main Menu |
| New high score | Write distance to save file | High score updated |
| Window closed | Flush save file; stop audio; Pygame shutdown | Clean exit |

---

## 10. Explicitly Out of Scope

- Combat / killing hostile fauna (not possible by design — exploration/scavenging only incentive)
- Large inventory/storage grid (deliberately simplified to hotbar-only)
- Procedural cave generation (uses pre-built chunk stitching instead)
- Accounts, login, networking, telemetry, or any server-side data
- Multiple graphics settings tiers (visual effects are deliberately minimal for performance, not configurable beyond colourblind mode)

---

## 11. Open Items Not Fully Specified in Source Doc

These appeared as diagrams/wireframes/images in the original document without enough written detail to implement directly — an agent should flag these for clarification or make a reasonable documented assumption:

- Exact color palette hex values (only referenced as images)
- Concept sketches (visual reference only, not geometry/spec)
- Detailed storyboard content for "Game loop 1/2/3" (Level / Player / Items) — headers only, no body content in source
- Exact wireframe layout/coordinates for the HUD (image only)
