"""Pygame drawing only. If you change how it looks, you should not touch pysim."""

from __future__ import annotations

import math

import pygame

from pysim.aircraft import Aircraft
from pysim.world import Runway, World
from render.camera import Camera
from render.plane_sprite import draw_plane

WATER = (58, 122, 168)
ISLAND = (94, 148, 78)
ISLAND_EDGE = (70, 118, 62)
RUNWAY = (86, 88, 92)
RUNWAY_EDGE = (58, 60, 64)
PAINT = (236, 232, 214)
GATE_NEXT = (250, 208, 80)
GATE_DONE = (210, 220, 200)
GATE_WAIT = (230, 236, 244)
HUD_BG = (18, 24, 32)
HUD_TEXT = (236, 238, 232)
HINT = (255, 232, 160)
GOOD = (140, 210, 150)
BAD = (230, 120, 110)


def draw_world(
    surface: pygame.Surface,
    world: World,
    camera: Camera,
    next_gate: int,
) -> None:
    surface.fill(WATER)
    ix, iy, iw, ih = world.island
    rect = _world_rect(camera, ix, iy, iw, ih)
    pygame.draw.rect(surface, ISLAND_EDGE, rect.inflate(10, 10), border_radius=18)
    pygame.draw.rect(surface, ISLAND, rect, border_radius=16)

    _draw_runway(surface, camera, world.runway_a, "A  TAKEOFF")
    _draw_runway(surface, camera, world.runway_b, "B  LAND")
    _draw_path(surface, camera, world, next_gate)


def _world_rect(camera: Camera, x: float, y: float, w: float, h: float) -> pygame.Rect:
    sx, sy = camera.to_screen(x, y)
    return pygame.Rect(sx, sy, int(camera.scale(w)), int(camera.scale(h)))


def _draw_runway(surface: pygame.Surface, camera: Camera, runway: Runway, title: str) -> None:
    corners = _runway_corners(runway)
    pts = [camera.to_screen(x, y) for x, y in corners]
    pygame.draw.polygon(surface, RUNWAY_EDGE, pts)
    inner = _runway_corners(runway, shrink=6)
    pygame.draw.polygon(surface, RUNWAY, [camera.to_screen(x, y) for x, y in inner])

    start, end = runway.ends()
    _dashed_line(surface, camera, start, end, PAINT, dash=18, gap=14, width=2)

    label_pos = camera.to_screen(runway.cx, runway.cy - runway.width * 0.7)
    font = pygame.font.SysFont("consolas", max(12, int(14 * camera.zoom)))
    text = font.render(title, True, PAINT)
    surface.blit(text, (label_pos[0] - text.get_width() // 2, label_pos[1]))


def _runway_corners(runway: Runway, shrink: float = 0.0) -> list[tuple[float, float]]:
    hx, hy = math.cos(runway.heading), math.sin(runway.heading)
    px, py = -hy, hx
    half_l = runway.length / 2 - shrink
    half_w = runway.width / 2 - shrink
    return [
        (runway.cx + hx * half_l + px * half_w, runway.cy + hy * half_l + py * half_w),
        (runway.cx + hx * half_l - px * half_w, runway.cy + hy * half_l - py * half_w),
        (runway.cx - hx * half_l - px * half_w, runway.cy - hy * half_l - py * half_w),
        (runway.cx - hx * half_l + px * half_w, runway.cy - hy * half_l + py * half_w),
    ]


def _dashed_line(
    surface: pygame.Surface,
    camera: Camera,
    a: tuple[float, float],
    b: tuple[float, float],
    color,
    dash: float,
    gap: float,
    width: int,
) -> None:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    t = 0.0
    while t < length:
        t2 = min(length, t + dash)
        p1 = camera.to_screen(a[0] + ux * t, a[1] + uy * t)
        p2 = camera.to_screen(a[0] + ux * t2, a[1] + uy * t2)
        pygame.draw.line(surface, color, p1, p2, max(1, int(width * camera.zoom)))
        t += dash + gap


def _draw_path(surface: pygame.Surface, camera: Camera, world: World, next_gate: int) -> None:
    _, a_east = world.runway_a.ends()
    b_west, _ = world.runway_b.ends()
    points = [a_east, *[(g.x, g.y) for g in world.gates], b_west]
    if len(points) >= 2:
        for i in range(len(points) - 1):
            # Segment 0 is takeoff → gate 1; after that, index matches gate pairs.
            color = GATE_DONE if i < next_gate else GATE_NEXT
            _dashed_line(surface, camera, points[i], points[i + 1], color, 16, 10, 2)

    font = pygame.font.SysFont("consolas", max(14, int(16 * camera.zoom)))
    for i, gate in enumerate(world.gates):
        if i < next_gate:
            color = GATE_DONE
        elif i == next_gate:
            color = GATE_NEXT
        else:
            color = GATE_WAIT
        pos = camera.to_screen(gate.x, gate.y)
        r = max(8, int(camera.scale(gate.radius)))
        pygame.draw.circle(surface, color, pos, r, max(2, int(3 * camera.zoom)))
        label = font.render(gate.label, True, HUD_BG)
        surface.blit(label, (pos[0] - label.get_width() // 2, pos[1] - label.get_height() // 2))


def draw_hud(
    surface: pygame.Surface,
    plane: Aircraft,
    hint: str,
    phase: str,
    next_gate: int,
    gate_count: int,
    outcome: str,
    fail_reason: str,
) -> None:
    pygame.draw.rect(surface, HUD_BG, pygame.Rect(16, 16, 300, 118), border_radius=10)
    font = pygame.font.SysFont("consolas", 18)
    small = pygame.font.SysFont("consolas", 16)
    lines = [
        f"Speed     {plane.speed:5.0f}",
        f"Altitude  {plane.altitude:5.0f}",
        f"Throttle  {plane.throttle * 100:5.0f}%",
        f"Phase     {phase}",
    ]
    for i, line in enumerate(lines):
        surface.blit(font.render(line, True, HUD_TEXT), (28, 24 + i * 22))

    bar = pygame.Rect(16, surface.get_height() - 70, surface.get_width() - 32, 52)
    pygame.draw.rect(surface, HUD_BG, bar, border_radius=10)
    surface.blit(small.render(hint, True, HINT), (28, bar.y + 8))
    help_line = "W/S throttle   A/D turn   R new path   Esc quit"
    if next_gate < gate_count and phase == "path":
        help_line = f"Next gate {next_gate + 1}/{gate_count}    " + help_line
    surface.blit(small.render(help_line, True, HUD_TEXT), (28, bar.y + 28))

    if outcome == "success":
        _banner(surface, "Landed on Runway B", "Press R for a new random path.", GOOD)
    elif outcome == "fail":
        _banner(surface, "Try that again", fail_reason + "  Press R.", BAD)


def _banner(surface: pygame.Surface, title: str, subtitle: str, color) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((10, 14, 20, 90))
    surface.blit(overlay, (0, 0))
    box = pygame.Rect(0, 0, 520, 110)
    box.center = (surface.get_width() // 2, surface.get_height() // 2)
    pygame.draw.rect(surface, HUD_BG, box, border_radius=12)
    pygame.draw.rect(surface, color, box, 3, border_radius=12)
    title_font = pygame.font.SysFont("consolas", 28)
    sub_font = pygame.font.SysFont("consolas", 16)
    t = title_font.render(title, True, color)
    s = sub_font.render(subtitle, True, HUD_TEXT)
    surface.blit(t, (box.centerx - t.get_width() // 2, box.y + 24))
    surface.blit(s, (box.centerx - s.get_width() // 2, box.y + 64))
