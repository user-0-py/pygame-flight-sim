# Runway lesson

A small **top-down airplane demo** built with Python. The point is not a real
flight model — it is a personal project you can read in an evening.

You take off from the west runway, fly through a **new random path** of
numbered gates (Press **R** for another route), then land on the east runway.

- **`pysim/`** — where the plane is, how it moves, whether a landing counts.
- **`render/`** — Pygame drawing (island, runways, top-down airplane sprite, HUD).
- **`main.py`** — the loop: keys → simulate one step → draw.

## Setup guide

### 1. What you need

- **Python 3.10 or newer** (`python3 --version`)
- A machine with a **display** (this is a Pygame window, not a website)
- **pip** (comes with most Python installs)

On Debian/Ubuntu, if `python3` is missing:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

On macOS, install Python from [python.org](https://www.python.org/downloads/) or Homebrew (`brew install python`).

On Windows, install Python from [python.org](https://www.python.org/downloads/) and tick **Add python.exe to PATH**.

### 2. Get the code

**GitHub** 

```bash
git clone https://github.com/user-0-py/pygame-flight-sim.git
cd pygame-flight-sim
```

### 3. Create a virtual environment

From the project folder:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate          # macOS / Linux
# Windows (Command Prompt):  .venv\Scripts\activate.bat
# Windows (PowerShell):      .venv\Scripts\Activate.ps1
```

Your prompt should show `(.venv)`. Stay in this environment for the next steps.

### 4. Install Python packages

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

That installs **pygame-ce** (the Pygame community build) and **pytest**.

If `pygame-ce` fails to install, try the classic package instead:

```bash
python -m pip install pygame pytest
```

### 5. Run the simulator

```bash
python main.py
```

A window titled **Runway lesson — takeoff, path, landing** should open.

### 6. Check that it works (optional)

These tests do not need a window:

```bash
python -m pytest
```

You should see all tests pass, including a scripted flight that finishes takeoff, the gates, and the landing.

## Controls

| Key | Action |
| --- | --- |
| `W` / `Up` | Add throttle |
| `S` / `Down` | Cut throttle |
| `A` / `D` or arrows | Turn |
| `R` | Restart with a new random path |
| `Esc` | Quit |

Hold **W** on Runway A until you lift off (around speed 40). Steer through
gates 1–4. Hold **S** to bring throttle down — it eases off, it does not snap
to zero — then descend onto Runway B and roll to a stop.

Throttle also climbs and descends: high throttle goes up, idle comes down.
Altitude is one number. Higher means a bigger plane and a longer shadow.

## Troubleshooting

- **`origin: command not found`** — add `~/.local/bin` to `PATH` (see step 2).
- **No window / `pygame.error: No available video device`** — you are on a
  machine with no display. Run it on your laptop, not a headless SSH session.
- **`No module named pygame`** — activate `.venv` and re-run
  `pip install -r requirements.txt`.
- **Window opens then closes** — look at the terminal for a traceback; make
  sure you started `python main.py` from the project root.

## GitHub

Public/private copies live at **[user-0-py/pygame-flight-sim](https://github.com/user-0-py/pygame-flight-sim)**.

If the GitHub repo does not exist yet, from a clone with `gh` signed in:

```bash
gh auth login
gh repo create user-0-py/pygame-flight-sim --private --source=. --remote=github --push
git push github main
```

## Ideas to extend

- A second path that starts from Runway B.
- A little wind that drifts the plane sideways.
- Flaps: a key that lets you fly slower on final.
- A score based on how centered your landing was.
