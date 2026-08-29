"""The plane's live numbers — position, speed, throttle, and so on."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class Aircraft:
    x: float
    y: float
    heading: float  # radians; 0 faces +x (east / right on screen)
    speed: float
    altitude: float
    throttle: float  # 0.0 idle → 1.0 full
    airborne: bool = False

    def nose_vector(self) -> tuple[float, float]:
        return math.cos(self.heading), math.sin(self.heading)

    def copy(self) -> Aircraft:
        return Aircraft(
            x=self.x,
            y=self.y,
            heading=self.heading,
            speed=self.speed,
            altitude=self.altitude,
            throttle=self.throttle,
            airborne=self.airborne,
        )
