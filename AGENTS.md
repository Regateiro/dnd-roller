# Agent Guidelines for dnd-roller

This document provides guidelines for agents working on this codebase.

## Project Overview

This is a Python Discord bot for D&D dice rolling and character management. It uses Poetry for dependency management and runs on Python 3.10+.

## Commands

### Dependency Management
```bash
poetry install        # Install all dependencies
poetry install --only dev  # Install only dev dependencies
```

### Running the Bot
```bash
poetry run python dnd_roller.py
```
Requires configuration at `~/.config/dnd-roller/config.ini` with:
- `[General]` section with `Storage` path
- `[Discord]` section with `Token`

### Linting & Formatting
```bash
make lint
```
This runs (via Poetry):
- **black** - line length 150
- **flake8** - max line length 150
- **isort** - with black profile
- **pylint** - errors only, max line length 150

### Running a Single Test
There are currently no tests in this project. Tests can be added using pytest:
```bash
poetry run pytest path/to/test_file.py
poetry run pytest path/to/test_file.py::test_function_name
```

## Code Style Guidelines

### General
- Use `from __future__ import annotations` for forward references
- Use `TYPE_CHECKING` block to avoid circular imports
- Max line length: 150 characters
- Use 4 spaces for indentation (no tabs)

### Imports
- Group imports in order: stdlib, third-party, local
- Use isort for import sorting
- Example:
```python
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import discord

from bot.handlers import RollHandler
from bot.services import RollService
from models import Character

if TYPE_CHECKING:
    from discord import Message
```

### Type Hints
- Always include return types on functions and methods
- Use type hints instead of type comments
- Example: `def __init__(self, roll_service: RollService) -> None:`

### Naming Conventions
- **Classes**: PascalCase (e.g., `RollHandler`, `DNDRollerClient`)
- **Functions/Methods**: snake_case (e.g., `handle`, `_prepare_fields`)
- **Constants**: UPPER_CASE (e.g., `MAX_LINE_LENGTH`)
- **Private methods**: prefix with underscore (e.g., `_dispatch_command`)

### Docstrings
- Use docstrings for all public classes and methods
- Follow Google style:
```python
class RollHandler:
    """Handler for dice roll commands (!r, !roll)."""

    def __init__(self, roll_service: RollService) -> None:
        """Initialize the RollHandler."""
        self._roll_service = roll_service
```

### Error Handling
- Use try/except blocks for operations that may fail
- Log exceptions with `logging.exception()` or `logging.error()`
- Example from `client.py`:
```python
try:
    guild_data = self.cache.get_or_create_guild(guild_id)
except Exception as ex:
    logging.exception(ex)
```

### Data Classes
- Use `@dataclass` for simple data containers
- Example:
```python
@dataclass
class RollModifiers:
    """Modifiers applied to a roll."""

    mode: RollMode = RollMode.NORMAL
    save: bool = False
    crit: bool = False
    vars: list[str] = field(default_factory=list)
```

### File Organization
- Main entry point: `dnd_roller.py`
- Bot client: `bot/client.py`
- Handlers: `bot/handlers/` (roll.py, character.py, session.py, utility.py)
- Services: `bot/services/` (roll.py, session.py)
- Models: `models.py`
- Utils: `utils/`

### Discord Bot Patterns
- Commands start with `!` (e.g., `!roll`, `!character`)
- Commands are dispatched via `_COMMANDS` and `_COMMAND_HANDLERS` dicts
- Handlers receive `message`, `guild_data`, `user`, and `fields` parameters
- Use async/await for all message handling