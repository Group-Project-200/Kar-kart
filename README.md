# Kar-Kart

A top-down pixel-art kart racer built with `pygame`. The cars have a 
pseudo-3d render and are affected by collisions and power-ups, like 
any other arcade racer. There are three distinct game-modes, with
Time Trial, Race and Championship. Your goal is to finish the fastest.

## Getting started

Look at 'REQUIREMENTS.md' for the requirements.

To run the program, run main.py from the Kar-Kart directory with the
following commend:

```bash
python3 main.py
```

## Controls

| Key       | Action                                               |
| --------- | ---------------------------------------------------- |
| `W` / `S` | Throttle / brake-reverse and selection in the screens|
| `A` / `D` | Steer left / right and selection in the screens      |
| `SPACE`   | Hold to drift — release for a boost                  |
| `F1`      | Toggle checkpoint debug overlay                      |
| `ESC`     | Pause / back                                         |
| `RETURN`  | Confirm selection                                    |

The in-race HUD shows current lap, checkpoint progress, speed, and
position (order of checkpoints cleared vs. the AI).

## Project layout

```
Kar-kart/
├── main.py                  Entry point + main loop
├── map_data.json            Checkpoints, start grid, item spawns
├── resources/               Fonts, maps, UI art, car sprite stacks
└── karkart/                 All game code
    ├── app_data.py            Loaded tracks + selected car / map
    ├── constants.py          Colors, screen anchors, key bindings
    ├── helpers.py            Math helpers (clamp, lerp, angles)
    ├── paths.py              Absolute paths to resources
    ├── screen_manager.py     Active-screen router
    │
    ├── ai/                   CPU opponent
    │   ├── pathfinder.py      A* on a wall-padded occupancy grid
    │   └── ai_controller.py   Steers a Car along the planned path
    │
    ├── physics/              Simulation
    │   ├── car.py             Dynamics, drift, boost, handling profiles
    │   ├── camera.py          Follow-camera with drift tilt
    │   ├── checkpoint.py      Rect-based checkpoint + racer state
    │   └── collision.py       Per-pixel map-vs-car collision
    │
    ├── rendering/            Drawing
    │   ├── map.py             Zoomed map + collision masks
    │   ├── renderer.py        Per-frame composition
    │   ├── stacker.py         Pre-baked rotated sprite cache
    │   └── preview.py         Standalone car preview pipeline
    │
    ├── screens/              One file per top-level screen
    │   ├── start.py
    │   ├── race_selection.py
    │   ├── car_selection.py
    │   ├── map_selection.py
    │   ├── gameplay.py
    │   └── start_sequence.py
    │
    ├── tools/                Dev utilities (map editor)
    │   └── map_editor.py      Click-to-place checkpoints, saves map_data.json
    │
    └── ui/                   Reusable widgets
        ├── button.py         Button / PaddingButton / ColorButton
        ├── card.py           Card / MapCard
        ├── container.py      Grid Container / SelectContainer / MapContainer
        └── track.py          Track entry (cover image + display name)
```

## Frame flow

1. `main.py` pulls the active screen from `ScreenManager` and dispatches
   events -> `update()` -> `draw()`.
2. `GamePlay.update()` alternates work on even / odd frames:
   * *Even* — mask collisions (player + AI) and car-to-car overlap.
   * *Odd* — checkpoint bookkeeping and the AI planning/steering.
   * *Every frame* steps `Car.step_physics()` for all cars, emits
     sparks, and moves the camera — motion never stutters.
3. `draw()` composes a pixelated frame: map (camera-rotated) → cars
   (rotated sprite stacks) → HUD at full resolution.
4. If a frame busts the ~16.7 ms budget, `main.py` skips the next
   `draw()` and holds the last image. Physics keeps running so the
   simulation stays in sync.


## Adding a track

1. Create `resources/maps/<name>/` with:
   * `cover.png` — thumbnail for the map-selection screen.
   * `0.png` — ground layer.
   * `1.png`, `2.png`, ... — collision / decoration layers.
2. Run the map editor:

   ```bash
   python3 -m karkart.tools.map_editor
   ```

## Class diagrams

- legend: `[abs]` abstract · `*` many · `→` owns / holds · `⇢` reads or writes (no ownership)

### Screens & UI

- `ScreenManager` — stack-based router, screens registered by label; pop-ups draw over the screen below
- `AppData` — shared model (selected car/map, race config) that survives screen transitions
- every screen inherits `Screen` (ABC); pop-ups are flagged `is_popup = True`
- pop-up dim is single-layer: `ScreenManager` calls `off_black_layer()` on the incoming screen whenever the outgoing one was a pop-up — so the dim never stacks (or fails to unstack) across nested pop-ups
- widget tree rooted at `UIObject`; `UISelectObject` adds focus/activation

Inheritance:

```
Screen [abs]
├── StartScreen · RaceSelector · CarScreen · MapScreen
├── GamePlay · LeaderboardScreen · WinnerScreen · EndScreen
└── PopUpMenu [abs]
    ├── PauseMenu · SettingsMenu · HelpMenu
    └── _BaseQuitConfirmMenu
        ├── QuitConfirmMenu · ChampionshipQuitConfirmMenu
        └── ConfirmSettingsMenu

UIObject [abs]
├── Container
│   └── SelectContainer ── MapContainer · PopUpContainer · ArrowContainer
├── Track
└── UISelectObject [abs]
    ├── Card [abs]   ── MapCard · PopUpCard · TextCard · HelpTextCard
    ├── Button       ── BackButton · TextButton
    ├── Arrow
    └── _Icon [abs]  ── SettingsIcon · HelpIcon
```

Wiring:

- `ScreenManager` → `AppData`; routes every `Screen` on a label-keyed stack (`StartScreen`, `RaceSelector`, `CarScreen`, `MapScreen`, `GamePlay`, `LeaderboardScreen`, `WinnerScreen`, `EndScreen`, all `PopUpMenu`s)
- `PopUpMenu` → `Container`/`SelectContainer` (body) + `TextCard` (title)
- `HelpMenu` → `HelpTextCard` · `_BaseQuitConfirmMenu` → 2 × `TextButton` (Yes / No) + `TextCard` (description)
- `MapContainer` → `MapCard*` · `PopUpContainer` → `TextButton*` · `ArrowContainer` → `Arrow×2`
- `AppData` → `Track*`
- `LeaderboardScreen` ⇢ `Leaderboard` (singleton `GAME_LEADERBOARD`) → `RaceResult*`
- `CarScreen` uses preview pipeline: `RenderPipeline` → `RenderSetup` · `MapCache` (preview-side, distinct from `rendering/map.py`'s `MapCache`)

### Gameplay

- `GamePlay` — race orchestrator; owns `World`, `Renderer`, threads, start/end screens
- threads ↔ render via `SnapshotBuffer`: physics writes `WorldSnapshot`, draw reads latest (no lock)
- `Car` is shared by player and AI; only the `ControlState` writer differs

Inheritance:

```
threading.Thread
└── FixedRateThread ── PhysicsScheduler · CollisionScheduler · AIScheduler
```

Composition (who owns what):

```
GamePlay → GameConfig
├── World
│   ├── Car (1..*) → CarHandling (→ BoostTier×2) · PhysicsState · ControlState
│   ├── RacerState (1..*)
│   ├── AIController (0..*)
│   └── CollisionDetector
├── Renderer
│   ├── Map → MapData · MapCache · Checkpoint*
│   ├── Stacker
│   └── SparkManager → Spark*
├── Camera → CameraFollowSettings
├── SnapshotBuffer → WorldSnapshot
│                    ├── player: CarSnapshot · ai: CarSnapshot*
│                    ├── player_racer: RacerSnapshot · ai_racers: RacerSnapshot*
│                    └── sparks: SparkSnapshot*
├── PhysicsScheduler · CollisionScheduler · AIScheduler
├── PowerupsManager → SpeedBoost* · Shield* · EMPJammer* · PowerupRendering
└── StartSequence
```

Cross-refs (no ownership):

- `AIController` ⇢ `Car` · `AStarPathfinder` · `Checkpoint` · `RacerState`
- `CollisionDetector` ⇢ `Map`
- `PhysicsScheduler` ⇢ publishes `WorldSnapshot` to `SnapshotBuffer`
- `GamePlay` ⇢ reads `WorldSnapshot` from `SnapshotBuffer` each draw
- `GamePlay` ⇢ `LeaderboardScreen` on race finish; appends a `RaceResult` to `GAME_LEADERBOARD`
