"""Unit tests for the exceptions module."""

from __future__ import annotations

import pytest

from bot.exceptions import (
    CharacterNotFoundError,
    DNDRollerError,
    InvalidDateError,
    InvalidRollExpressionError,
    InvalidSkillError,
    InvalidStatError,
    SessionNotFoundError,
)


class TestDNDRollerError:
    """Tests for the base DNDRollerError exception."""

    def test_base_exception(self) -> None:
        """Test that DNDRollerError can be raised and caught."""
        with pytest.raises(DNDRollerError):
            raise DNDRollerError("test error")


class TestCharacterNotFoundError:
    """Tests for the CharacterNotFoundError exception."""

    def test_message(self) -> None:
        """Test the exception message includes character name."""
        error = CharacterNotFoundError("Grog")
        assert "Grog" in str(error)
        assert "not found" in str(error).lower()

    def test_attribute(self) -> None:
        """Test the character_name attribute is stored."""
        error = CharacterNotFoundError("Grog")
        assert error.character_name == "Grog"

    def test_can_be_caught(self) -> None:
        """Test that the exception can be caught."""
        with pytest.raises(CharacterNotFoundError):
            raise CharacterNotFoundError("Grog")


class TestInvalidStatError:
    """Tests for the InvalidStatError exception."""

    def test_message(self) -> None:
        """Test the exception message includes stat name."""
        error = InvalidStatError("str")
        assert "str" in str(error)
        assert "stat" in str(error).lower()

    def test_attribute(self) -> None:
        """Test the stat attribute is stored."""
        error = InvalidStatError("str")
        assert error.stat == "str"

    def test_can_be_caught(self) -> None:
        """Test that the exception can be caught."""
        with pytest.raises(InvalidStatError):
            raise InvalidStatError("invalid")


class TestInvalidSkillError:
    """Tests for the InvalidSkillError exception."""

    def test_message(self) -> None:
        """Test the exception message includes skill name."""
        error = InvalidSkillError("athletics")
        assert "athletics" in str(error)
        assert "skill" in str(error).lower()

    def test_attribute(self) -> None:
        """Test the skill attribute is stored."""
        error = InvalidSkillError("athletics")
        assert error.skill == "athletics"

    def test_can_be_caught(self) -> None:
        """Test that the exception can be caught."""
        with pytest.raises(InvalidSkillError):
            raise InvalidSkillError("invalid")


class TestInvalidRollExpressionError:
    """Tests for the InvalidRollExpressionError exception."""

    def test_message(self) -> None:
        """Test the exception message includes expression."""
        error = InvalidRollExpressionError("1d20+")
        assert "1d20+" in str(error)
        assert "roll" in str(error).lower()

    def test_attribute(self) -> None:
        """Test the expression attribute is stored."""
        error = InvalidRollExpressionError("1d20+")
        assert error.expression == "1d20+"

    def test_can_be_caught(self) -> None:
        """Test that the exception can be caught."""
        with pytest.raises(InvalidRollExpressionError):
            raise InvalidRollExpressionError("invalid")


class TestInvalidDateError:
    """Tests for the InvalidDateError exception."""

    def test_message(self) -> None:
        """Test the exception message includes date string."""
        error = InvalidDateError("2024-02-30")
        assert "2024-02-30" in str(error)
        assert "date" in str(error).lower()

    def test_attribute(self) -> None:
        """Test the date_str attribute is stored."""
        error = InvalidDateError("2024-02-30")
        assert error.date_str == "2024-02-30"

    def test_can_be_caught(self) -> None:
        """Test that the exception can be caught."""
        with pytest.raises(InvalidDateError):
            raise InvalidDateError("invalid")


class TestSessionNotFoundError:
    """Tests for the SessionNotFoundError exception."""

    def test_message(self) -> None:
        """Test the exception message includes date string."""
        error = SessionNotFoundError("2024-01-01")
        assert "2024-01-01" in str(error)
        assert "session" in str(error).lower()

    def test_attribute(self) -> None:
        """Test the date_str attribute is stored."""
        error = SessionNotFoundError("2024-01-01")
        assert error.date_str == "2024-01-01"

    def test_can_be_caught(self) -> None:
        """Test that the exception can be caught."""
        with pytest.raises(SessionNotFoundError):
            raise SessionNotFoundError("2024-01-01")
