from dataclasses import dataclass

from render import RenderSetup


@dataclass(frozen=True, slots=True)
class PreviewDebuggerConfig:
    # Per-frame rotation step in preview mode.
    rotation_step_degrees: float = 0.6
    # Preview-only multiplier so the debugger can inspect larger cars.
    car_zoom_multiplier: float = 1.5


@dataclass(slots=True)
class PreviewDebuggerState:
    # Toggle for entering/leaving debugger mode.
    enabled: bool = False
    # Free-running angle used by smooth preview rendering.
    rotation_degrees: float = 0.0
    # Selected entry from discovered `car_*` folders.
    selected_car_index: int = 0


def make_initial_preview_state(default_car_index: int) -> PreviewDebuggerState:
    # Keep preview initialization explicit and isolated from gameplay state.
    return PreviewDebuggerState(
        enabled=False,
        rotation_degrees=0.0,
        selected_car_index=default_car_index,
    )


def toggle_preview(state: PreviewDebuggerState) -> None:
    # Mode switch helper so toggle behavior stays in one place.
    state.enabled = not state.enabled


def apply_sprite_delta(state: PreviewDebuggerState, *, sprite_delta: int, sprite_count: int) -> bool:
    # Sprite cycling is preview-specific debugger input.
    if sprite_delta == 0 or sprite_count <= 0:
        return False

    state.selected_car_index = (state.selected_car_index + sprite_delta) % sprite_count
    return True


def advance_preview_rotation(state: PreviewDebuggerState, config: PreviewDebuggerConfig) -> None:
    # Smooth preview rotation updates every frame with no angle snapping.
    state.rotation_degrees = (state.rotation_degrees + config.rotation_step_degrees) % 360.0


def _compute_zoom_ratio(base_car_zoom: float, active_car_zoom: float) -> float:
    safe_base_zoom = max(0.01, base_car_zoom)
    safe_active_zoom = max(0.01, active_car_zoom)
    return safe_active_zoom / safe_base_zoom


def _clamp_pixelation_scale(pixelation_scale: float) -> float:
    return max(0.1, min(pixelation_scale, 1.0))


def _compute_car_draw_scale(setup: RenderSetup) -> float:
    # Effective draw size in the low-res buffer is zoom multiplied by pixelation scale.
    return max(0.01, setup.car_zoom) * _clamp_pixelation_scale(setup.pixelation_scale)


def _scale_stack_spread_for_draw_scale(base_spread: int, *, draw_scale_ratio: float) -> int:
    if base_spread == 0:
        return 0

    scaled_spread = int(round(base_spread * max(0.01, draw_scale_ratio)))
    if scaled_spread == 0:
        return -1 if base_spread < 0 else 1
    return scaled_spread


def build_preview_visual_settings(
    base_setup: RenderSetup,
    base_stack_spread: int,
    *,
    preview_enabled: bool,
    config: PreviewDebuggerConfig,
) -> tuple[RenderSetup, int]:
    # Preview zoom changes car size, pixelation is inversely adjusted by zoom ratio.
    zoom_multiplier = config.car_zoom_multiplier if preview_enabled else 1.0
    active_car_zoom = base_setup.car_zoom * zoom_multiplier
    zoom_ratio = _compute_zoom_ratio(base_setup.car_zoom, active_car_zoom)
    active_setup = RenderSetup(
        map_zoom=base_setup.map_zoom,
        car_zoom=active_car_zoom,
        pixelation_scale=base_setup.pixelation_scale / zoom_ratio,
    )

    # Stack spread tracks effective draw scale so the car silhouette stays consistent.
    base_draw_scale = _compute_car_draw_scale(base_setup)
    active_draw_scale = _compute_car_draw_scale(active_setup)
    draw_scale_ratio = active_draw_scale / base_draw_scale
    active_stack_spread = _scale_stack_spread_for_draw_scale(
        base_stack_spread,
        draw_scale_ratio=draw_scale_ratio,
    )
    return active_setup, active_stack_spread
