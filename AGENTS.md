# Agent Guidelines for dnd-roller

## Run

```bash
poetry install
poetry run python dnd_roller.py
```

Requires `~/.config/dnd-roller/config.ini` with `[General]Storage` and `[Discord]Token`.

## Verify

```bash
make test   # 319 passing, 100% coverage
make lint  # black/flake8/isort/pylint (max 150 chars)
```

## Key Facts

- All tests pass with 100% statement coverage - keep it that way
- Config path is non-obvious: `~/.config/dnd-roller/config.ini`
- Handlers: `bot/handlers/` (character, roll, session, utility)
- Services: `bot/services/` (roll, session)
- All handlers are async
- Command aliases defined in `bot/commands.py`