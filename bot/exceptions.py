"""Custom exceptions for the D&D Roller bot."""

from __future__ import annotations


class DNDRollerError(Exception):
    """Base exception for D&D Roller domain errors."""

    pass


class CharacterNotFoundError(DNDRollerError):
    """Raised when a character is not found."""

    def __init__(self, character_name: str) -> None:
        self.character_name = character_name
        super().__init__(f"Character '{character_name}' not found")


class InvalidStatError(DNDRollerError):
    """Raised when an invalid stat is provided."""

    def __init__(self, stat: str) -> None:
        self.stat = stat
        super().__init__(f"Invalid stat: '{stat}'")


class InvalidSkillError(DNDRollerError):
    """Raised when an invalid skill is provided."""

    def __init__(self, skill: str) -> None:
        self.skill = skill
        super().__init__(f"Invalid skill: '{skill}'")


class InvalidRollExpressionError(DNDRollerError):
    """Raised when a dice roll expression is invalid."""

    def __init__(self, expression: str) -> None:
        self.expression = expression
        super().__init__(f"Invalid roll expression: '{expression}'")


class InvalidDateError(DNDRollerError):
    """Raised when a date string is invalid."""

    def __init__(self, date_str: str) -> None:
        self.date_str = date_str
        super().__init__(f"Invalid date: '{date_str}'")


class InvalidCharacterDataError(DNDRollerError):
    """Raised when character data is invalid or incomplete."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InvalidSessionDateError(DNDRollerError):
    """Raised when a session date is invalid (e.g., in the past)."""

    def __init__(self, date_str: str, reason: str) -> None:
        self.date_str = date_str
        self.reason = reason
        super().__init__(f"Invalid session date '{date_str}': {reason}")


class SessionNotFoundError(DNDRollerError):
    """Raised when a session is not found."""

    def __init__(self, date_str: str) -> None:
        self.date_str = date_str
        super().__init__(f"Session not found for date: '{date_str}'")
