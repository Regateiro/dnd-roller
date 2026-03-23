"""Command registry for centralizing command aliases and magic strings."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    import discord
    from bot.services.session import SessionService
    from bot.services.roll import RollService
    from models import GuildData, User


class RollMode(str, Enum):
    """Roll modes for dice rolls."""

    NORMAL = "n"
    ADVANTAGE = "a"
    TRIPLE_ADVANTAGE = "ta"
    DISADVANTAGE = "d"


@dataclass
class CommandHandler:
    """Container for a command handler and its callable."""

    handler: Callable
    aliases: tuple[str, ...]


class CommandRegistry:
    """Registry for all bot commands and their handlers."""

    def __init__(
        self,
        roll_handler,
        character_handler,
        session_handler,
        utility_handler,
    ) -> None:
        self._handlers: dict[str, Callable] = {}
        self._roll_handler = roll_handler
        self._character_handler = character_handler
        self._session_handler = session_handler
        self._utility_handler = utility_handler
        self._build_registry()

    def _build_registry(self) -> None:
        """Build the command registry."""
        commands = {
            "!r": self._roll_handler.handle,
            "!roll": self._roll_handler.handle,
            "!character": self._character_handler.handle,
            "!char": self._character_handler.handle,
            "!c": self._character_handler.handle,
            "!m": self._utility_handler.handle_macro,
            "!macro": self._utility_handler.handle_macro,
            "!v": self._utility_handler.handle_variable,
            "!var": self._utility_handler.handle_variable,
            "!variable": self._utility_handler.handle_variable,
            "!session": self._session_handler.handle,
            "!s": self._session_handler.handle,
            "!distance": self._utility_handler.handle_distance,
            "!d": self._utility_handler.handle_distance,
            "!fall": self._utility_handler.handle_fall,
            "!f": self._utility_handler.handle_fall,
            "!h": self._utility_handler.handle_help,
            "!help": self._utility_handler.handle_help,
        }
        self._handlers = commands

    def get_handler(self, command: str) -> Callable | None:
        """Get the handler for a command."""
        return self._handlers.get(command)


ROLL_MODIFIER_ALIASES = {
    "save": ("save", "s"),
    "crit": ("crit", "critical"),
    "advantage": ("a", "adv", "advantage"),
    "triple_advantage": ("ta", "tadv", "tadvantage"),
    "disadvantage": ("d", "dis", "disadvantage"),
}

ROLL_MODE_MAP = {
    "a": RollMode.ADVANTAGE,
    "adv": RollMode.ADVANTAGE,
    "advantage": RollMode.ADVANTAGE,
    "ta": RollMode.TRIPLE_ADVANTAGE,
    "tadv": RollMode.TRIPLE_ADVANTAGE,
    "tadvantage": RollMode.TRIPLE_ADVANTAGE,
    "d": RollMode.DISADVANTAGE,
    "dis": RollMode.DISADVANTAGE,
    "disadvantage": RollMode.DISADVANTAGE,
}

CHARACTER_COMMAND_ALIASES = {
    "create": ("create", "c"),
    "delete": ("delete", "d"),
    "update": ("update", "u"),
    "active": ("active", "a"),
    "info": ("info", "show", "i", "s"),
    "list": ("list", "l"),
}

CHARACTER_UPDATE_ALIASES = {
    "main": ("main",),
    "saves": ("saves",),
    "bonus": ("bonus",),
    "skills": ("skills",),
    "expertise": ("expertise",),
    "half": ("half",),
    "advantage": ("adv", "advantage"),
}

MACRO_COMMAND_ALIASES = {
    "set": ("set", "s"),
    "delete": ("delete", "d"),
    "list": ("list", "l"),
}

VARIABLE_COMMAND_ALIASES = MACRO_COMMAND_ALIASES

SESSION_COMMAND_ALIASES = {
    "weekday": ("weekday", "w"),
    "schedule": ("schedule", "s"),
    "cancel": ("cancel", "c"),
    "available": ("available", "a"),
    "unavailable": ("unavailable", "u"),
    "list": ("list", "l"),
    "next": ("next", "n"),
}

HELP_ALIASES = ("help", "h")


def resolve_command_alias(aliases: dict[str, tuple[str, ...]], value: str) -> str | None:
    """Resolve an alias to its canonical command name."""
    for canonical, alias_list in aliases.items():
        if value in alias_list:
            return canonical
    return None


def get_roll_mode(value: str) -> RollMode | None:
    """Get roll mode from string alias."""
    return ROLL_MODE_MAP.get(value)
