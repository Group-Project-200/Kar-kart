# Kar-Kart

A top-down pixel-art kart-racing game built with `pygame`. Cars are rendered
as stacks of rotated sprite slices; the camera rotates smoothly with the
car's heading and tilts during drifts; collision uses per-pixel masks
against the map layers.

## Running the game

Requires Python 3.10+ (for `match` statements and PEP 604 unions) and
`pygame`. The codebase otherwise uses only the Python standard library.

```bash
pip install pygame
python main.py
```

Controls:

| Key | Action |
| --- | --- |
| `W` / `S` | Throttle / brake-reverse |
| `A` / `D` | Steer left / right |
| `SPACE` | Hold to drift; release to trigger a boost |
| `ESC` | Back (on menu screens) |
| `RETURN` | Confirm selection |

## Project layout

```
Kar-kart/
├── main.py                 # Entry point: pygame init + the main loop
├── map_data.json           # Checkpoints / start / items per track
├── resources/              # Images, fonts, map layers, car sprite stacks
│   ├── assets/             #   Fonts
│   ├── maps/               #   Per-track folders (cover.png + layer PNGs)
│   ├── pictures/           #   UI images and flags
│   └── render/             #   car_01 .. car_04 sprite stacks
│
└── karkart/                # All game code lives here
    ├── app_data.py         # Shared runtime state: loaded tracks + cars
    ├── constants.py        # Colors, screen anchors, key bindings
    ├── helpers.py          # Math helpers (clamp, lerp, angle maths)
    ├── paths.py            # Absolute paths to resources/
    ├── screen_manager.py   # Router that activates one screen at a time
    │
    ├── physics/            # Simulation layer
    │   ├── camera.py       #   Follow-camera with drift tilt
    │   ├── car.py          #   Car dynamics, drift, boost
    │   ├── checkpoint.py   #   Single-rect checkpoint
    │   └── collision.py    #   Per-pixel map-vs-car collision
    │
    ├── rendering/          # Drawing layer
    │   ├── map.py          #   Zoomed map + collision masks
    │   ├── preview.py      #   Standalone pipeline for the car preview
    │   ├── renderer.py     #   In-game frame composition
    │   └── stacker.py      #   Pre-baked rotated car sprite cache
    │
    ├── screens/            # One file per top-level screen
    │   ├── start.py
    │   ├── race_selection.py
    │   ├── car_selection.py
    │   ├── map_selection.py
    │   ├── gameplay.py
    │   └── start_sequence.py
    │
    ├── tools/              # Developer-only utilities
    │   └── map_editor.py   #   Click-to-place checkpoints, saves map_data.json
    │
    └── ui/                 # Reusable widgets (no game knowledge)
        ├── button.py       #   Button / PaddingButton / ColorButton
        ├── card.py         #   Card / MapCard
        ├── container.py    #   Grid Container / SelectContainer / MapContainer
        └── track.py        #   Track entry (cover image + display name)
```

## How a frame flows

1. `main.py` asks the `ScreenManager` for the active screen.
2. The main loop calls `handle_event` for each pygame event, then
   `update()`, then `draw(screen)`.
3. On the gameplay screen, `update()` runs `CollisionDetector.check()`,
   advances the `Car.step_physics()` state, updates the follow camera,
   and ticks checkpoints.
4. `draw()` asks the `Renderer` to compose the frame: the `Map` blits
   itself with camera rotation, then the `Stacker` blits the car's
   rotated sprite stack at the centre of the frame.

## Adding a new track

1. Drop a new folder under `resources/maps/<name>/` containing:
   * `cover.png` — the thumbnail shown on the map-selection screen.
   * `0.png` — the ground layer (also used for collision-free rendering).
   * `1.png`, `2.png`, ... — additional collision/decoration layers.
2. Run the map editor to place checkpoints and a start box:

   ```bash
   python -m karkart.tools.map_editor
   ```

   Edit the `MAP_NAME` constant in that file first to point to your new
   track, then use the keybindings in the module docstring to place
   regions. The tool writes the result back to `map_data.json` on exit.

## Tuning the car

Every tunable constant lives on `karkart.physics.car.CarHandling` as a
field with a default value. Rotation response, drift skew, boost tiers,
overspeed braking curves, and slip/grip blending are each isolated
blocks of that dataclass.
