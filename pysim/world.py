"""The island, two runways, and the gated path between them."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Runway:
    """A rectangle centered on (cx, cy), long axis along ``heading``."""

    cx: float
    cy: float
    length: float
    width: float
    heading: float

    def contains(self, x: float, y: float, pad: float = 0.0) -> bool:
        dx = x - self.cx
        dy = y - self.cy
        c, s = math.cos(-self.heading), math.sin(-self.heading)
        local_x = dx * c - dy * s
        local_y = dx * s + dy * c
        return abs(local_x) <= self.length / 2 + pad and abs(local_y) <= self.width / 2 + pad

    def heading_error(self, heading: float) -> float:
        """0 means the nose is parallel to the strip (either direction)."""
        return _axis_error(heading, self.heading)

    def ends(self) -> tuple[tuple[float, float], tuple[float, float]]:
        hx, hy = math.cos(self.heading), math.sin(self.heading)
        half = self.length / 2
        return (self.cx - hx * half, self.cy - hy * half), (
            self.cx + hx * half,
            self.cy + hy * half,
        )


def _axis_error(heading: float, runway_heading: float) -> float:
    """0 = parallel to the runway (either direction)."""
    a = (heading - runway_heading) % math.pi
    if a > math.pi / 2:
        a = math.pi - a
    return a


@dataclass(frozen=True)
class Gate:
    x: float
    y: float
    radius: float
    label: str


@dataclass(frozen=True)
class World:
    width: float
    height: float
    island: tuple[float, float, float, float]  # x, y, w, h
    runway_a: Runway
    runway_b: Runway
    gates: tuple[Gate, ...]
    water_margin: float = 40.0

    def on_island(self, x: float, y: float) -> bool:
        ix, iy, iw, ih = self.island
        return ix <= x <= ix + iw and iy <= y <= iy + ih

    def on_any_runway(self, x: float, y: float, pad: float = 8.0) -> bool:
        return self.runway_a.contains(x, y, pad) or self.runway_b.contains(x, y, pad)


def build_world() -> World:
    """One grassy island, takeoff on the west strip, landing on the east."""
    width, height = 2400.0, 1400.0
    island = (80.0, 120.0, 2240.0, 1160.0)

    runway_a = Runway(cx=420.0, cy=720.0, length=520.0, width=78.0, heading=0.0)
    runway_b = Runway(cx=1980.0, cy=980.0, length=560.0, width=78.0, heading=0.0)

    gates = (
        Gate(780.0, 700.0, 70.0, "1"),
        Gate(1120.0, 480.0, 75.0, "2"),
        Gate(1520.0, 520.0, 75.0, "3"),
        Gate(1680.0, 980.0, 80.0, "4"),
    )
    return World(
        width=width,
        height=height,
        island=island,
        runway_a=runway_a,
        runway_b=runway_b,
        gates=gates,
    )


def spawn_on_runway_a(world: World):
    """Park at the west end of the takeoff runway, facing east."""
    from pysim.aircraft import Aircraft

    start, _ = world.runway_a.ends()
    return Aircraft(
        x=start[0] + 40.0,
        y=world.runway_a.cy,
        heading=world.runway_a.heading,
        speed=0.0,
        altitude=0.0,
        throttle=0.0,
        airborne=False,
    )
