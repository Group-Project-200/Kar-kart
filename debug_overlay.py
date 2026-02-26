from dataclasses import dataclass

import pygame


DEBUG_METRIC_TEXT_COLOR = (245, 245, 245)
DEBUG_METRIC_TEXT_PADDING = (6, 6)
DEBUG_METRIC_FONT_SIZE = 40
FRAME_RUNTIME_SMOOTH_ALPHA = 0.15
BOOST_STATE_LINGER_FRAMES = 45


@dataclass(slots=True)
class DebugOverlayState:
    smoothed_frame_runtime_ms: float | None = None
    font: pygame.font.Font | None = None
    boost_display_level: int = 0
    boost_display_frames: int = 0


def _get_debug_metric_font(state: DebugOverlayState) -> pygame.font.Font:
    if not pygame.font.get_init():
        pygame.font.init()
    if state.font is None:
        state.font = pygame.font.Font(None, DEBUG_METRIC_FONT_SIZE)
    return state.font


def _boost_state_label(boost_level: int) -> str:
    if boost_level <= 0:
        return "no boost"
    if boost_level >= 2:
        return "big boost"
    return "little boost"


def _format_runtime_label(state: DebugOverlayState, frame_runtime_ms: float) -> str:
    if frame_runtime_ms < 0.0:
        return "--"
    if state.smoothed_frame_runtime_ms is None:
        state.smoothed_frame_runtime_ms = frame_runtime_ms
    else:
        state.smoothed_frame_runtime_ms += (
            frame_runtime_ms - state.smoothed_frame_runtime_ms
        ) * FRAME_RUNTIME_SMOOTH_ALPHA
    return f"{state.smoothed_frame_runtime_ms:.1f} ms"


def _resolve_display_boost_level(state: DebugOverlayState, boost_level: int) -> int:
    if boost_level > 0:
        state.boost_display_level = boost_level
        state.boost_display_frames = BOOST_STATE_LINGER_FRAMES
        return state.boost_display_level

    if state.boost_display_frames > 0:
        state.boost_display_frames -= 1
    else:
        state.boost_display_level = 0
    return state.boost_display_level


def draw_runtime_debug_overlay(
    screen: pygame.Surface,
    state: DebugOverlayState,
    *,
    frame_runtime_ms: float,
    speed: float,
    drift_frames: int,
    boost_level: int,
) -> None:
    font = _get_debug_metric_font(state)
    runtime_label = _format_runtime_label(state, frame_runtime_ms)
    speed_kmh = round(speed * 40)
    boost_state_label = _boost_state_label(_resolve_display_boost_level(state, boost_level))
    label = font.render(
        f"Frame: {runtime_label} | Spd: {speed_kmh}km/h | Drift: {drift_frames}f | Boost: {boost_state_label}",
        True,
        DEBUG_METRIC_TEXT_COLOR,
    )
    screen.blit(label, DEBUG_METRIC_TEXT_PADDING)


def draw_runtime_debug_overlay_and_flip(
    screen: pygame.Surface,
    state: DebugOverlayState,
    *,
    frame_runtime_ms: float,
    speed: float,
    drift_frames: int,
    boost_level: int,
) -> None:
    draw_runtime_debug_overlay(
        screen,
        state,
        frame_runtime_ms=frame_runtime_ms,
        speed=speed,
        drift_frames=drift_frames,
        boost_level=boost_level,
    )
    pygame.display.flip()
