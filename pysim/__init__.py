"""Tiny flight sim: numbers and rules, no drawing.

Pygame lives in ``render/`` and ``main.py``. This package only tracks
where the plane is and how the world is laid out.
"""

from pysim.aircraft import Aircraft
from pysim.world import World, build_world

__all__ = ["Aircraft", "World", "build_world"]
