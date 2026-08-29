"""Top-down trainer airplane drawn once, then rotated each frame.

The sprite faces +x (east) so ``heading`` in the sim matches Pygame rotation.
"""

from __future__ import annotations

import math

import pygame

from pysim.aircraft import Aircraft
from render.camera import Camera

FUSELAGE = (236, 238, 232)
FUSELAGE_EDGE = (48, 54, 62)
STRIPE = (42, 102, 168)
COCKPIT = (36, 58, 92)
WINDOW = (168, 196, 220)
WING = (214, 218, 214)
WING_EDGE = (40, 46, 54)
TIP = (196, 54, 48)
PROP = (90, 96, 104)
SHADOW = (28, 52, 38, 110)

_BASE: pygame.Surface | None = None


def _build_base() -> pygame.Surface:
    """Paint a light single-engine airplane, nose to the right."""
    w, h = 128, 88
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2

    def poly(pts, color, width=0):
        pygame.draw.polygon(s, color, pts, width)

    # Main wing (behind the cockpit, slightly swept)
    wing = [
        (cx - 6, cy - 38),
        (cx + 22, cy - 36),
        (cx + 28, cy - 32),
        (cx + 26, cy - 8),
        (cx + 8, cy - 6),
        (cx + 8, cy + 6),
        (cx + 26, cy + 8),
        (cx + 28, cy + 32),
        (cx + 22, cy + 36),
        (cx - 6, cy + 38),
        (cx - 14, cy + 12),
        (cx - 14, cy - 12),
    ]
    poly(wing, WING)
    pygame.draw.polygon(s, WING_EDGE, wing, 2)
    pygame.draw.line(s, TIP, (cx + 22, cy - 35), (cx + 27, cy - 32), 4)
    pygame.draw.line(s, TIP, (cx + 22, cy + 35), (cx + 27, cy + 32), 4)

    # Horizontal stabilizer
    tail = [
        (cx - 48, cy - 16),
        (cx - 28, cy - 14),
        (cx - 26, cy - 4),
        (cx - 26, cy + 4),
        (cx - 28, cy + 14),
        (cx - 48, cy + 16),
        (cx - 52, cy + 6),
        (cx - 52, cy - 6),
    ]
    poly(tail, WING)
    pygame.draw.polygon(s, WING_EDGE, tail, 2)

    # Fuselage
    fuselage = [
        (cx + 54, cy),  # nose
        (cx + 42, cy - 6),
        (cx + 10, cy - 8),
        (cx - 30, cy - 7),
        (cx - 50, cy - 5),
        (cx - 56, cy),
        (cx - 50, cy + 5),
        (cx - 30, cy + 7),
        (cx + 10, cy + 8),
        (cx + 42, cy + 6),
    ]
    poly(fuselage, FUSELAGE)
    pygame.draw.polygon(s, FUSELAGE_EDGE, fuselage, 2)

    # Blue cheatline
    pygame.draw.line(s, STRIPE, (cx - 46, cy + 1), (cx + 40, cy + 1), 3)

    # Cockpit glass
    cockpit = [(cx + 28, cy - 5), (cx + 40, cy - 4), (cx + 40, cy + 4), (cx + 28, cy + 5)]
    poly(cockpit, COCKPIT)
    pygame.draw.polygon(s, WINDOW, cockpit, 1)

    # Cabin windows
    for ox in (cx + 8, cx - 4, cx - 16):
        pygame.draw.circle(s, WINDOW, (ox, cy - 2), 2)

    # Vertical tail (seen from above as a fin along the spine)
    fin = [(cx - 54, cy), (cx - 40, cy - 3), (cx - 32, cy), (cx - 40, cy + 3)]
    poly(fin, STRIPE)

    # Propeller disc at the nose
    pygame.draw.circle(s, PROP, (cx + 52, cy), 7, 2)
    pygame.draw.line(s, PROP, (cx + 52, cy - 8), (cx + 52, cy + 8), 2)
    pygame.draw.circle(s, FUSELAGE_EDGE, (cx + 52, cy), 3)

    return s


def plane_surface() -> pygame.Surface:
    global _BASE
    if _BASE is None:
        _BASE = _build_base()
    return _BASE


def draw_plane(surface: pygame.Surface, plane: Aircraft, camera: Camera) -> None:
    base = plane_surface()
    zoom = camera.zoom * (0.42 + plane.altitude * 0.0012)
    angle = -math.degrees(plane.heading)  # pygame rotates CCW; heading 0 is +x
    sprite = pygame.transform.rotozoom(base, angle, zoom)

    # Ground blob, then the airplane on top.
    shadow = pygame.transform.rotozoom(base, angle, zoom * 0.92)
    dark = pygame.Surface(shadow.get_size(), pygame.SRCALPHA)
    dark.fill((20, 40, 28, 100))
    shadow.blit(dark, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    shadow_off = 6 + plane.altitude * 0.08
    sx, sy = camera.to_screen(plane.x + shadow_off, plane.y + shadow_off)
    surface.blit(shadow, shadow.get_rect(center=(sx, sy)))

    px, py = camera.to_screen(plane.x, plane.y)
    surface.blit(sprite, sprite.get_rect(center=(px, py)))
