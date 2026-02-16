# Repository Guidelines

## Project Structure & Module Organization
- `runtime/`: core runtime (event queue, ZMQ bus, sinks, adapters).
- `worker_runtime/`: worker-side ZMQ loop and adapter registry.
- `sample/`: runnable CLI example for the runtime.
- `docs/`: design notes and architecture context.
- `main.py`: minimal smoke entry point.

## Build, Test, and Development Commands
- `python main.py`: quick smoke run; prints a hello message.
- `python sample/main.py`: launches the sample CLI and exercises the runtime.
- `python -m venv .venv && source .venv/bin/activate`: create/activate a local venv.
- `pip install -e .`: install dependencies for local development.
- `pyright`: type checking (configured in `pyproject.toml`).

## Coding Style & Naming Conventions
- Python 3.11+; follow PEP 8 with 4-space indentation.
- Use type hints for public methods and data structures.
- Naming: `snake_case` for functions/vars, `CapWords` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep files ASCII unless existing content requires Unicode.

## Testing Guidelines
- No test framework is set up yet.
- If adding tests, place them under `tests/` and use `pytest` naming like `test_runtime.py`.
- Prefer fast unit tests for ZMQ-independent logic; mock external workers.

## Commit & Pull Request Guidelines
- No established commit message convention (repository has no commits yet).
- Suggested format: short imperative summary (<= 72 chars), optional body for rationale.
- PRs should include: summary, testing notes (`python sample/main.py`), and linked issues if any.

## Architecture Notes
- Read `docs/design.md` for the event model and runtime/worker split.
