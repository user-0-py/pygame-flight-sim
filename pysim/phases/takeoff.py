"""Takeoff: roll on Runway A until you have enough speed to lift off."""

from __future__ import annotations

from pysim.aircraft import Aircraft
from pysim.phases.note import PhaseNote
from pysim.physics import ROTATE_SPEED
from pysim.world import World


def check_takeoff(plane: Aircraft, world: World) -> PhaseNote:
    if plane.airborne:
        return PhaseNote("Airborne — fly through the numbered gates.", done=True)

    on_strip = world.runway_a.contains(plane.x, plane.y, pad=12.0)
    if plane.speed > 12.0 and not on_strip and not world.on_any_runway(plane.x, plane.y):
        return PhaseNote(
            "Stay on the runway until you lift off.",
            failed=True,
            fail_reason="You rolled off the runway before takeoff.",
        )

    if plane.speed < 8.0:
        return PhaseNote("Hold W / Up to add throttle. Keep the nose on the centerline.")
    if plane.speed < ROTATE_SPEED:
        return PhaseNote(f"Keep accelerating — rotate at {int(ROTATE_SPEED)} speed.")
    return PhaseNote("Rotate speed — you should lift off any second.")
