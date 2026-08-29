"""A scripted autopilot should be able to finish the lesson."""

from __future__ import annotations

import math

from main import Flight
from pysim.world import World


def _turn_toward(heading: float, tx: float, ty: float, x: float, y: float) -> float:
    desired = math.atan2(ty - y, tx - x)
    err = (desired - heading + math.pi) % (math.tau) - math.pi
    if err > 0.05:
        return 1.0
    if err < -0.05:
        return -1.0
    return 0.0


def _pilot(flight: Flight) -> tuple[float, float]:
    plane = flight.plane
    world: World = flight.world
    if flight.phase == "takeoff":
        err = (world.runway_a.heading - plane.heading + math.pi) % math.tau - math.pi
        turn = 1.0 if err > 0.03 else (-1.0 if err < -0.03 else 0.0)
        return turn, 1.0

    if flight.phase == "path":
        gate = world.gates[min(flight.next_gate, len(world.gates) - 1)]
        return _turn_toward(plane.heading, gate.x, gate.y, plane.x, plane.y), 0.72

    target_x = world.runway_b.cx + 40.0
    target_y = world.runway_b.cy
    turn = _turn_toward(plane.heading, target_x, target_y, plane.x, plane.y)
    if plane.airborne and plane.altitude > 20.0:
        throttle = 0.0
    elif plane.airborne:
        throttle = 0.05
    else:
        throttle = 0.0
    return turn, throttle


def test_scripted_pilot_completes_takeoff_path_landing():
    flight = Flight()
    dt = 1 / 60
    for _ in range(60 * 120):
        turn, throttle = _pilot(flight)
        flight.update(dt, turn, throttle)
        if flight.outcome == "success":
            return
        assert flight.outcome != "fail", flight.fail_reason
    raise AssertionError(
        f"never finished: phase={flight.phase} outcome={flight.outcome} "
        f"alt={flight.plane.altitude:.1f} speed={flight.plane.speed:.1f} "
        f"pos=({flight.plane.x:.0f},{flight.plane.y:.0f}) gate={flight.next_gate}"
    )
