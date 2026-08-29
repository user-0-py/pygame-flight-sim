# Runway lesson

A small **top-down airplane demo** built with Python. The point is not a real
flight model — it is a personal project you can read in an evening.

You take off from the west runway, fly through four numbered gates, then land
on the east runway.

- **`pysim/`** — where the plane is, how it moves, whether a landing counts.
- **`render/`** — Pygame drawing (island, runways, triangle plane, HUD).
- **`main.py`** — the loop: keys → simulate one step → draw.

## Run it

You need Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
| --- | --- |
| `W` / `Up` | Add throttle |
| `S` / `Down` | Cut throttle |
| `A` / `D` or arrows | Turn |
| `R` | Restart |
| `Esc` | Quit |

Hold throttle on Runway A until you lift off (~40 speed). Steer through gates
1–4, then idle to descend onto Runway B and roll to a stop.

Altitude is a single number. Higher means a bigger plane and a longer shadow —
there is no 3D camera.

## Ideas to extend

- A second path that starts from Runway B.
- A little wind that drifts the plane sideways.
- Flaps: a key that lets you fly slower on final.
- A score based on how centered your landing was.

Smoke test without opening a window:

```bash
python -m pytest tests/test_smoke.py
```
