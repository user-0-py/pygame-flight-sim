# Harness engineering notes

Theory and a working lab for **AI agent harnesses**: the control program around a language model (loop, tools, policy, context, traces, eval).

This folder is meant to stand alone as the GitHub repository **`harness_engineering_notes`**. It currently lives inside `pygame-flight-sim` only because this environment cannot create a new GitHub repo (the token is not allowed to call `createRepository`). After you create an empty public repo with that name under your account, copy this directory into it:

```bash
# from a clone of this branch
git clone https://github.com/YOUR_USER/harness_engineering_notes.git
rsync -a harness_engineering_notes/ harness_engineering_notes-repo/ --exclude scripts/generate_notebook.py
# or: copy the folder contents into the new repo and push
```

## Contents

| Path | What it is |
| --- | --- |
| [`index.html`](index.html) | Theory worksheet |
| [`questions.html`](questions.html) | MCQ (auto-graded) + subjective practice |
| [`notebooks/01_harness_from_scratch.ipynb`](notebooks/01_harness_from_scratch.ipynb) | Step-by-step harness + local MLflow experiment |
| [`src/agent_harness/`](src/agent_harness) | Importable loop, policy, MLflow helpers |
| [`tests/test_harness.py`](tests/test_harness.py) | Harness unit tests, golden task, MLflow logging |
| [`examples/toy_workspace/`](examples/toy_workspace) | Tiny fake service wiki the demo agent reads |

## Setup

Python 3.10+.

```bash
cd harness_engineering_notes
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Open the theory page in a browser (`index.html`).

Run tests:

```bash
PYTHONPATH=src python3 -m pytest tests -q
```

Run the notebook (Jupyter):

```bash
jupyter notebook notebooks/01_harness_from_scratch.ipynb
```

Or VS Code / Cursor: open the `.ipynb` and run all cells. The notebook adds `src/` to `sys.path` automatically.

Regenerate the notebook from the generator script if you edit `scripts/generate_notebook.py`:

```bash
python3 scripts/generate_notebook.py
```

## What “harness” means here

The model proposes assistant text and tool calls. The harness:

1. Builds the message list (system + user + history)
2. Offers tool schemas
3. Executes or **refuses** tool calls
4. Writes observations back as `role=tool` messages
5. Stops on final text or a step budget

Errors are observations. Policy is code. Context is curated. Every run has a stop reason.

## License

Use freely as personal engineering notes.
