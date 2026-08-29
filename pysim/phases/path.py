"""Guided path: fly through numbered gates in order."""

from __future__ import annotations

from pysim.aircraft import Aircraft
from pysim.phases.note import PhaseNote
from pysim.world import World


def gate_hit(plane: Aircraft, world: World, index: int) -> bool:
    if index < 0 or index >= len(world.gates):
        return False
    gate = world.gates[index]
    dx = plane.x - gate.x
    dy = plane.y - gate.y
    return (dx * dx + dy * dy) ** 0.5 <= gate.radius and plane.airborne


def check_path(plane: Aircraft, world: World, next_index: int) -> PhaseNote:
    if next_index >= len(world.gates):
        return PhaseNote("Path complete — line up with the east runway.", done=True)

    gate = world.gates[next_index]
    if gate_hit(plane, world, next_index):
        if next_index + 1 >= len(world.gates):
            return PhaseNote("Last gate — set up to land on the east runway.", done=True)
        nxt = world.gates[next_index + 1]
        return PhaseNote(f"Gate {gate.label} done. Next: gate {nxt.label}.", done=True)

    remaining = len(world.gates) - next_index
    return PhaseNote(
        f"Fly through gate {gate.label} ({remaining} left). Use A/D to turn, keep some throttle."
    )
