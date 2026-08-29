"""One frame of motion. Keep the rules short so they stay readable.

The plane is a point on the map plus a single altitude number.
No lift curves, no stalls-as-tables — just throttle, drag, and a bit of climb.
"""

from __future__ import annotations

import math

from pysim.aircraft import Aircraft

# Speeds are "pixels per second" so they match the map we draw.
MAX_SPEED = 120.0
MAX_ALTITUDE = 180.0
ROTATE_SPEED = 40.0  # leave the ground at or above this
STALL_SPEED = 32.0
THRUST = 58.0
DRAG = 0.0038
GROUND_FRICTION = 22.0
BRAKE_FRICTION = 36.0  # extra when throttle is idle on the ground
AIR_TURN = 1.65  # radians/sec at full speed
GROUND_TURN = 0.28
THROTTLE_RATE = 0.85


def apply_controls(plane: Aircraft, turn: float, throttle_delta: float, dt: float) -> None:
    """``turn`` is -1, 0, or 1. ``throttle_delta`` is -1, 0, or 1."""
    plane.throttle = max(0.0, min(1.0, plane.throttle + throttle_delta * THROTTLE_RATE * dt))

    speed_factor = min(1.0, plane.speed / 55.0)
    if plane.airborne:
        rate = AIR_TURN * max(0.25, speed_factor)
    else:
        rate = GROUND_TURN * speed_factor
    plane.heading += turn * rate * dt


def step(plane: Aircraft, dt: float) -> None:
    """Move the plane forward one tick. Mutates ``plane``."""
    thrust = plane.throttle * THRUST
    drag = DRAG * plane.speed * plane.speed
    accel = thrust - drag

    if not plane.airborne:
        accel -= GROUND_FRICTION
        if plane.throttle < 0.08:
            accel -= BRAKE_FRICTION
    elif plane.throttle < 0.12:
        accel -= 10.0  # idle in the air bleeds speed for landing

    plane.speed = max(0.0, min(MAX_SPEED, plane.speed + accel * dt))

    hx, hy = math.cos(plane.heading), math.sin(plane.heading)
    plane.x += hx * plane.speed * dt
    plane.y += hy * plane.speed * dt

    if not plane.airborne:
        if plane.speed >= ROTATE_SPEED:
            plane.airborne = True
            plane.altitude = 4.0
        else:
            plane.altitude = 0.0
        return

    # Throttle is also the climb lever: high = up, idle = down.
    # Drop below stall speed and you sink no matter what.
    if plane.speed < STALL_SPEED:
        climb = -30.0
    else:
        climb = (plane.throttle - 0.42) * 28.0
        if plane.throttle < 0.12:
            climb -= 14.0

    plane.altitude = max(0.0, min(MAX_ALTITUDE, plane.altitude + climb * dt))
    if plane.altitude <= 0.0:
        plane.altitude = 0.0
        plane.airborne = False
