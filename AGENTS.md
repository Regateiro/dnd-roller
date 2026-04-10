# Agent Guidelines for dnd-roller

## Quick Start

```bash
poetry install
poetry run python dnd_roller.py
```

Requires `~/.config/dnd-roller/config.ini` with:
- `[General]` section containing `Storage` path
- `[Discord]` section containing `Token`

## Linting

```bash
make lint
```

Runs: black (150), flake8 (150), isort (black profile), pylint (errors-only, 150).

## Testing

No tests currently exist. Add with pytest:
```bash
poetry run pytest path/to/test_file.py
```

## Project Structure

- Entry point: `dnd_roller.py`
- Bot client: `bot/client.py`
- Command registry: `bot/commands.py` (central alias mapping)
- Handlers: `bot/handlers/` (roll, character, session, utility)
- Services: `bot/services/` (roll, session)
- Models: `models.py`

## Code Style

- Max line length: 150 characters
- Use `from __future__ import annotations` and `TYPE_CHECKING` blocks
- Import order: stdlib, third-party, local (isort handles this)
- Docstrings for public classes/methods (Google style)
- Use `@dataclass` for simple data containers

## Discord Patterns

- Commands start with `!` (e.g., `!roll`, `!character`, `!r`)
- Handlers defined in `bot/commands.py:_build_registry()` via `_COMMANDS` dict
- All handlers use async/await