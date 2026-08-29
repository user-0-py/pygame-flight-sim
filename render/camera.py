"""Follow the plane, zoom out a little when it climbs."""

from __future__ import annotations

from pysim.aircraft import Aircraft
from pysim.world import World


class Camera:
    def __init__(self, view_w: int, view_h: int) -> None:
        self.view_w = view_w
        self.view_h = view_h
        self.x = 0.0
        self.y = 0.0
        self.zoom = 1.0

    def update(self, plane: Aircraft, world: World, dt: float) -> None:
        target_zoom = 1.05 - min(0.28, plane.altitude / 420.0)
        self.zoom += (target_zoom - self.zoom) * min(1.0, dt * 3.0)

        target_x = plane.x - self.view_w / (2 * self.zoom)
        target_y = plane.y - self.view_h / (2 * self.zoom)
        follow = min(1.0, dt * 6.0)
        self.x += (target_x - self.x) * follow
        self.y += (target_y - self.y) * follow

        max_x = max(0.0, world.width - self.view_w / self.zoom)
        max_y = max(0.0, world.height - self.view_h / self.zoom)
        self.x = max(0.0, min(max_x, self.x))
        self.y = max(0.0, min(max_y, self.y))

    def to_screen(self, wx: float, wy: float) -> tuple[int, int]:
        sx = int((wx - self.x) * self.zoom)
        sy = int((wy - self.y) * self.zoom)
        return sx, sy

    def scale(self, world_size: float) -> float:
        return world_size * self.zoom
