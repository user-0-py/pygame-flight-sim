"""Landing: touch down on Runway B, aligned and not too fast, then slow down."""

from __future__ import annotations

from pysim.aircraft import Aircraft
from pysim.phases.note import PhaseNote
from pysim.world import World

TOUCHDOWN_SPEED = 80.0
ALIGN_RADIANS = 0.55  # ~31 degrees
WIN_SPEED = 12.0


def check_landing(plane: Aircraft, world: World) -> PhaseNote:
    strip = world.runway_b
    on_b = strip.contains(plane.x, plane.y, pad=6.0)
    aligned = strip.heading_error(plane.heading) <= ALIGN_RADIANS

    if plane.airborne:
        if plane.altitude < 8.0 and plane.speed > TOUCHDOWN_SPEED + 12 and on_b:
            return PhaseNote("Too fast to land — pull throttle back (S / Down).")
        if plane.altitude < 4.0 and on_b and not aligned:
            return PhaseNote("Almost down, but you are not lined up with the runway.")
        return PhaseNote(
            "Cut throttle to descend. Touch down on the east runway, nose along the strip."
        )

    # On the ground after the path.
    if on_b and aligned and plane.speed <= TOUCHDOWN_SPEED:
        if plane.speed <= WIN_SPEED:
            return PhaseNote("Parked on Runway B. Nice landing.", done=True)
        return PhaseNote("Down and safe — idle throttle and roll to a stop.")

    if on_b and plane.speed > TOUCHDOWN_SPEED:
        return PhaseNote(
            "You arrived too hot.",
            failed=True,
            fail_reason="Touchdown was faster than the landing gear can take.",
        )

    if world.runway_a.contains(plane.x, plane.y, pad=10.0):
        return PhaseNote("That's the takeoff runway. Climb out and try the east strip.")

    if not world.on_island(plane.x, plane.y):
        return PhaseNote(
            "You left the island.",
            failed=True,
            fail_reason="The plane settled in the water.",
        )

    if not world.on_any_runway(plane.x, plane.y) and plane.speed > 18.0:
        return PhaseNote(
            "That wasn't pavement.",
            failed=True,
            fail_reason="You touched down off the runway.",
        )

    if on_b and not aligned:
        return PhaseNote(
            "Crooked landing.",
            failed=True,
            fail_reason="Heading was not lined up with the runway.",
        )

    if plane.speed <= 4.0 and not on_b:
        return PhaseNote(
            "Stopped in the grass.",
            failed=True,
            fail_reason="You came to rest off Runway B.",
        )

    return PhaseNote("Stay lined up with the east runway and keep it slow.")

