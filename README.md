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

Hold **W** on Runway A until you lift off (around speed 40). Steer through
gates 1–4. Hold **S** to bring throttle down — it eases off, it does not snap
to zero — then descend onto Runway B and roll to a stop.

Throttle also climbs and descends: high throttle goes up, idle comes down.
Altitude is one number. Higher means a bigger plane and a longer shadow.

Tests (no window required):

```bash
python -m pytest
```

## Ideas to extend

- A second path that starts from Runway B.
- A little wind that drifts the plane sideways.
- Flaps: a key that lets you fly slower on final.
- A score based on how centered your landing was.
