"""Protocol definitions for structural subtyping (duck typing with type hints)."""

from __future__ import annotations

from typing import Protocol

from bot.models import Character, GuildData, User


class Message:
    """Minimal Protocol for Discord message objects."""

    content: str
    author: object
    channel: object


class RollHandlerProtocol(Protocol):
    """Protocol for roll command handlers."""

    async def handle(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...


class CharacterHandlerProtocol(Protocol):
    """Protocol for character command handlers."""

    async def handle(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...


class SessionHandlerProtocol(Protocol):
    """Protocol for session command handlers."""

    async def handle(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...


class UtilityHandlerProtocol(Protocol):
    """Protocol for utility command handlers."""

    async def handle_distance(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...

    async def handle_fall(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...

    async def handle_help(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...

    async def handle_macro(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...

    async def handle_variable(
        self,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None: ...


class RollServiceProtocol(Protocol):
    """Protocol for roll services."""

    async def resolve_references(self, character: Character, value: str) -> str: ...

    async def get_character_roll(
        self,
        character: Character,
        target: str,
        modifiers: object,
    ) -> str: ...

    def generate_summary(
        self,
        character: str,
        target: str,
        modifiers: object,
        macros: dict[str, str],
    ) -> str: ...

    def parse_modifiers(
        self,
        fields: list[str],
        character: Character,
    ) -> object: ...


class SessionServiceProtocol(Protocol):
    """Protocol for session services."""

    def clean_sessions(self, guild_data: GuildData, current_user: User) -> None: ...

    def parse_date(self, date_str: str) -> object: ...

    def format_date(self, date: object) -> str: ...

    def is_session_day(self, date: object, guild_data: GuildData) -> bool: ...

    def get_missing_players(self, date: str, guild_data: GuildData) -> list[str]: ...

    def get_upcoming_sessions(
        self,
        guild_data: GuildData,
        count: int = 4,
    ) -> list[tuple[str, list[str]]]: ...

    def get_next_session(
        self,
        guild_data: GuildData,
    ) -> tuple[str, list[str]] | None: ...
