# Installation

Python 3.12+.

## PyPI (recommended)

```bash
pip install agyloop
pipx install agyloop
```

Then:

```bash
agyloop --help
agyloop doctor
```

## TestPyPI

Runtime dependencies still resolve from real PyPI:

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agyloop
```

## Clone / editable (contributors)

```bash
git clone https://github.com/adammatthewsteinberger/agyloop.git
cd agyloop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
agyloop --help
```

Or with uv:

```bash
uv sync --extra dev --extra docs
uv run agyloop --help
```

Auth is **either** `GOOGLE_API_KEY` (Gemini Developer API) **or** Application
Default Credentials with a Vertex / Enterprise flag. `agyloop doctor` reports
the lane; it never guesses. See [Configuration](configuration.md).
