"""The airplane sprite is a painted 2D aircraft, not a triangle."""

import pygame

from pysim.aircraft import Aircraft
from render.camera import Camera
from render.plane_sprite import draw_plane, plane_surface
from pysim.world import build_world


def test_plane_sprite_is_larger_than_a_triangle():
    pygame.display.init()
    screen = pygame.display.set_mode((64, 64))
    surf = plane_surface()
    assert surf.get_width() >= 100
    opaque = 0
    for x in range(0, surf.get_width(), 4):
        for y in range(0, surf.get_height(), 4):
            if surf.get_at((x, y)).a > 0:
                opaque += 1
    assert opaque > 40
    world = build_world(seed=0)
    cam = Camera(400, 300)
    screen = pygame.Surface((400, 300))
    plane = Aircraft(x=200, y=150, heading=0.4, speed=40, altitude=20, throttle=0.5, airborne=True)
    cam.update(plane, world, 0.016)
    draw_plane(screen, plane, cam)
    pygame.display.quit()
