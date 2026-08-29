"""Checks that the sim can take off, score a gate, and accept a landing.

These tests do not open a Pygame window.
"""

from pysim.aircraft import Aircraft
from pysim.physics import apply_controls, step
from pysim.phases.landing import check_landing
from pysim.phases.path import check_path, gate_hit
from pysim.phases.takeoff import check_takeoff
from pysim.world import build_world, spawn_on_runway_a


def test_world_has_two_runways_and_gates():
    world = build_world(seed=1)
    assert world.runway_a.contains(420, 720)
    assert world.runway_b.contains(1980, 980)
    assert 3 <= len(world.gates) <= 5


def test_seeds_make_different_paths():
    a = [(g.x, g.y) for g in build_world(seed=1).gates]
    b = [(g.x, g.y) for g in build_world(seed=99).gates]
    assert a != b


def test_path_finishes_on_final_for_runway_b():
    for seed in range(12):
        world = build_world(seed=seed)
        last = world.gates[-1]
        assert last.x < world.runway_b.cx
        assert abs(last.y - world.runway_b.cy) < 80
        xs = [g.x for g in world.gates]
        assert xs == sorted(xs)


def test_full_throttle_on_runway_lifts_off():
    world = build_world(seed=0)
    plane = spawn_on_runway_a(world)
    note = check_takeoff(plane, world)
    assert not note.done
    for _ in range(400):
        apply_controls(plane, turn=0.0, throttle_delta=1.0, dt=1 / 60)
        step(plane, 1 / 60)
    assert plane.airborne
    assert check_takeoff(plane, world).done


def test_gate_hit_and_path_completion():
    world = build_world(seed=0)
    g = world.gates[0]
    plane = Aircraft(x=g.x, y=g.y, heading=0.0, speed=60.0, altitude=40.0, throttle=0.5, airborne=True)
    assert gate_hit(plane, world, 0)
    note = check_path(plane, world, len(world.gates))
    assert note.done


def test_slow_aligned_stop_on_runway_b_wins():
    world = build_world(seed=0)
    plane = Aircraft(
        x=world.runway_b.cx,
        y=world.runway_b.cy,
        heading=world.runway_b.heading,
        speed=4.0,
        altitude=0.0,
        throttle=0.0,
        airborne=False,
    )
    note = check_landing(plane, world)
    assert note.done
    assert not note.failed


def test_hot_touchdown_fails():
    world = build_world(seed=0)
    plane = Aircraft(
        x=world.runway_b.cx,
        y=world.runway_b.cy,
        heading=world.runway_b.heading,
        speed=90.0,
        altitude=0.0,
        throttle=0.2,
        airborne=False,
    )
    note = check_landing(plane, world)
    assert note.failed
