"""Top-down airplane demo: take off, fly a short path, land.

Simulation lives in ``pysim/``. This file is the game loop: keys, tick, draw.
"""

from __future__ import annotations

import sys

import pygame

from pysim.aircraft import Aircraft
from pysim.physics import apply_controls, step
from pysim.phases.landing import check_landing
from pysim.phases.path import check_path, gate_hit
from pysim.phases.takeoff import check_takeoff
from pysim.world import World, build_world, spawn_on_runway_a
from render.camera import Camera
from render.draw import draw_hud, draw_plane, draw_world

WINDOW = (1280, 720)
FPS = 60


class Flight:
    def __init__(self) -> None:
        self.world: World = build_world()
        self.plane: Aircraft = spawn_on_runway_a(self.world)
        self.phase = "takeoff"
        self.next_gate = 0
        self.hint = "Hold W / Up to add throttle. Keep the nose on the centerline."
        self.outcome = "playing"
        self.fail_reason = ""

    def reset(self) -> None:
        self.__init__()

    def update(self, dt: float, turn: float, throttle_delta: float) -> None:
        if self.outcome != "playing":
            return
        apply_controls(self.plane, turn, throttle_delta, dt)
        step(self.plane, dt)
        self._update_lesson()

    def _update_lesson(self) -> None:
        if not (0.0 <= self.plane.x <= self.world.width and 0.0 <= self.plane.y <= self.world.height):
            self._fail("You flew off the map.")
            return

        if self.phase == "takeoff":
            note = check_takeoff(self.plane, self.world)
            self.hint = note.hint
            if note.failed:
                self._fail(note.fail_reason)
            elif note.done:
                self.phase = "path"
                self.hint = note.hint
            return

        if self.phase == "path":
            if gate_hit(self.plane, self.world, self.next_gate):
                self.next_gate += 1
            note = check_path(self.plane, self.world, self.next_gate)
            self.hint = note.hint
            if note.done and self.next_gate >= len(self.world.gates):
                self.phase = "landing"
            # Ground contact during the path is judged by the landing rules.
            if not self.plane.airborne:
                self.phase = "landing"
                self._finish_landing()
            return

        if self.phase == "landing":
            self._finish_landing()

    def _finish_landing(self) -> None:
        note = check_landing(self.plane, self.world)
        self.hint = note.hint
        if note.failed:
            self._fail(note.fail_reason)
        elif note.done:
            self.outcome = "success"

    def _fail(self, reason: str) -> None:
        self.outcome = "fail"
        self.fail_reason = reason


def read_input() -> tuple[float, float]:
    keys = pygame.key.get_pressed()
    turn = 0.0
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        turn -= 1.0
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        turn += 1.0
    throttle = 0.0
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        throttle += 1.0
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        throttle -= 1.0
    return turn, throttle


def run() -> None:
    pygame.init()
    pygame.display.set_caption("Runway lesson — takeoff, path, landing")
    screen = pygame.display.set_mode(WINDOW)
    clock = pygame.time.Clock()
    camera = Camera(*WINDOW)
    flight = Flight()

    while True:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1 / 30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if event.key == pygame.K_r:
                    flight.reset()

        turn, throttle = read_input()
        flight.update(dt, turn, throttle)
        camera.update(flight.plane, flight.world, dt)

        draw_world(screen, flight.world, camera, flight.next_gate)
        draw_plane(screen, flight.plane, camera)
        draw_hud(
            screen,
            flight.plane,
            flight.hint,
            flight.phase,
            flight.next_gate,
            len(flight.world.gates),
            flight.outcome,
            flight.fail_reason,
        )
        pygame.display.flip()


if __name__ == "__main__":
    run()
