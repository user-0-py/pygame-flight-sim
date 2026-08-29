"""The island, two runways, and the gated path between them."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random


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


def generate_flight_path(
    island: tuple[float, float, float, float],
    runway_a: Runway,
    runway_b: Runway,
    rng: random.Random,
) -> tuple[Gate, ...]:
    """Lay 3–5 gates from after takeoff to a final for Runway B.

    X always moves east so a beginner can follow the rings without looping.
    Y wanders, but not so far that a single turn cannot keep up.
    """
    _ix, iy, _iw, ih = island
    y_lo, y_hi = iy + 140.0, iy + ih - 140.0
    count = rng.randint(3, 5)

    a_end = runway_a.cx + runway_a.length / 2
    b_start = runway_b.cx - runway_b.length / 2
    first_x = a_end + rng.uniform(70.0, 130.0)
    last_x = b_start - rng.uniform(30.0, 90.0)
    first_y = max(y_lo, min(y_hi, runway_a.cy + rng.uniform(-50.0, 50.0)))
    last_y = max(y_lo, min(y_hi, runway_b.cy + rng.uniform(-24.0, 24.0)))

    xs = [first_x]
    span = last_x - first_x
    for i in range(1, count - 1):
        t = i / (count - 1)
        xs.append(first_x + span * t + rng.uniform(-35.0, 35.0))
    xs.append(last_x)
    for i in range(1, len(xs) - 1):
        xs[i] = min(xs[i], last_x - 50.0 * (len(xs) - 1 - i))
        xs[i] = max(xs[i], xs[i - 1] + 50.0)
    xs[-1] = last_x

    ys = [first_y]
    for i in range(1, count - 1):
        step = rng.uniform(-220.0, 220.0)
        # Mix a little toward the landing centerline so the last turn is gentle.
        toward_b = (last_y - ys[-1]) * 0.25
        y = ys[-1] + step + toward_b
        ys.append(max(y_lo, min(y_hi, y)))
    ys.append(last_y)

    gates = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        radius = rng.uniform(68.0, 86.0)
        gates.append(Gate(x, y, radius, str(i + 1)))
    return tuple(gates)


def build_world(seed: int | None = None) -> World:
    """One grassy island, takeoff west, a fresh path, landing east."""
    rng = random.Random(seed)
    width, height = 2400.0, 1400.0
    island = (80.0, 120.0, 2240.0, 1160.0)

    runway_a = Runway(cx=420.0, cy=720.0, length=520.0, width=78.0, heading=0.0)
    runway_b = Runway(cx=1980.0, cy=980.0, length=560.0, width=78.0, heading=0.0)
    gates = generate_flight_path(island, runway_a, runway_b, rng)
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
