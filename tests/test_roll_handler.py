"""Unit tests for the RollHandler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from bot.handlers.roll import RollHandler
from bot.models import Character, GuildData, Stat, User
from bot.services.roll import RollService


class MockMessage:
    """Mock Discord message."""

    def __init__(self):
        self.channel = MockChannel()


class MockChannel:
    """Mock Discord channel."""

    def __init__(self):
        self._sent_messages = []

    async def send(self, content: str) -> None:
        self._sent_messages.append(content)


@pytest.fixture
def mock_message():
    """Create a mock Discord message."""
    return MockMessage()


@pytest.fixture
def guild_data():
    """Create guild data."""
    return GuildData()


@pytest.fixture
def user_with_character():
    """Create a user with a character."""
    user = User(name="testuser")
    user.active = "grog"
    user.characters["grog"] = Character(
        level=5,
        stats={
            Stat.STRENGTH: 16,
            Stat.DEXTERITY: 14,
            Stat.CONSTITUTION: 14,
            Stat.INTELLIGENCE: 10,
            Stat.WISDOM: 12,
            Stat.CHARISMA: 8,
        },
        save_prof=[Stat.STRENGTH],
        skill_prof=["athletics"],
        skill_expertise=["perception"],
    )
    return user


@pytest.fixture
def roll_handler():
    """Create a RollHandler with mocked dependencies."""
    with patch("bot.handlers.roll.d20") as mock_d20:
        mock_d20.roll.return_value = MagicMock(__str__=lambda self: "1d20+3: [10]")
        mock_d20.RollSyntaxError = Exception
        service = RollService()
        return RollHandler(service)


class TestRollHandler:
    """Tests for the RollHandler class."""

    @pytest.mark.asyncio
    async def test_handle_roll_command(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling a roll command with dice expression."""
        fields = ["!r", "grog", "1d20+3"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "rolled" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_stat_roll(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling a stat roll."""
        fields = ["!r", "grog", "str"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "rolled" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_skill_roll(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling a skill roll."""
        fields = ["!r", "grog", "athletics"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_with_advantage(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling a roll with advantage."""
        fields = ["!r", "grog", "str", "adv"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_with_save(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling a saving throw."""
        fields = ["!r", "grog", "str", "save"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_no_character(self, mock_message, guild_data, roll_handler) -> None:
        """Test handling roll with no character."""
        user = User(name="testuser")
        user.active = ""
        fields = ["!r", "grog", "1d20"]

        await roll_handler.handle(mock_message, guild_data, user, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestRollHandlerErrors:
    """Tests for RollHandler error handling."""

    @pytest.mark.asyncio
    async def test_handle_invalid_stat(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling with invalid stat."""
        fields = ["!r", "grog", "invalid_stat"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "invalid" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_invalid_roll_expression(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling with invalid roll expression."""
        fields = ["!r", "grog", "invalid_expression"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestRollHandlerCharacterFallback:
    """Tests for RollHandler character fallback logic."""

    @pytest.mark.asyncio
    async def test_prepare_fields_uses_active_character(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test _prepare_fields uses active character when specified character doesn't exist."""
        user = User(name="testuser")
        user.active = "grog"
        user.characters["grog"] = user_with_character.characters["grog"]
        fields = ["!r", "nonexistent", "1d20"]  # "nonexistent" not in user.characters

        await roll_handler.handle(mock_message, guild_data, user, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_get_character_uses_active_when_specified_missing(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test _get_character uses active character when specified character is missing."""
        user = User(name="testuser")
        user.active = "grog"
        user.characters["grog"] = user_with_character.characters["grog"]
        # User has active but specified character doesn't exist
        fields = ["!r", "other", "str"]  # "other" doesn't exist

        await roll_handler.handle(mock_message, guild_data, user, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_get_character_fallback_to_active(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test _get_character falls back to active when specified doesn't exist."""
        user = User(name="testuser")
        user.active = "grog"  # Active character exists
        user.characters["grog"] = user_with_character.characters["grog"]  # Add it
        
        # Verify setup: "missing_char" not in characters, "grog" in active
        assert "missing_char" not in user.characters
        assert user.active in user.characters
        
        # fields[1] = "missing_char" doesn't exist in characters, so should fall back to active
        fields = ["!r", "missing_char", "1d20"]

        await roll_handler.handle(mock_message, guild_data, user, fields)

        # Should still work with fallback to active character
        assert len(mock_message.channel._sent_messages) > 0


class TestRollHandlerErrorPaths:
    """Tests for RollHandler error handling paths."""

    @pytest.mark.asyncio
    async def test_invalid_stat_error_path(self, mock_message, guild_data, user_with_character, roll_handler) -> None:
        """Test handling InvalidStatError path - using a stat that triggers the error."""
        # Use "strength" which is a valid stat, but let's test with an actual invalid target
        # The InvalidStatError is actually caught in get_character_roll when target isn't found
        # For this test, we just verify the error handling works
        fields = ["!r", "grog", "not_a_valid_skill"]

        await roll_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_d20_roll_syntax_error_path(self, mock_message, guild_data, user_with_character) -> None:
        """Test handling d20 RollSyntaxError path."""
        with patch("bot.handlers.roll.d20") as mock_d20:
            # Create a RollSyntaxError that inherits from Exception for the catch chain
            class RollSyntaxError(Exception):
                pass
            mock_d20.RollSyntaxError = RollSyntaxError
            # Use a valid target (str) so it gets past validation, then make roll fail
            mock_d20.roll.side_effect = RollSyntaxError("Invalid syntax")
            handler = RollHandler(RollService())
            fields = ["!r", "grog", "str"]  # Valid stat target

            await handler.handle(mock_message, guild_data, user_with_character, fields)

            # Should hit line 55: "Invalid dice notation: {ex}"
            assert len(mock_message.channel._sent_messages) > 0
            msg = mock_message.channel._sent_messages[0].lower()
            assert "invalid dice notation" in msg

    @pytest.mark.asyncio
    async def test_dnd_roller_error_path(self, mock_message, guild_data, user_with_character) -> None:
        """Test handling DNDRollerError path."""
        with patch("bot.handlers.roll.d20") as mock_d20:
            from bot.exceptions import DNDRollerError
            # Make d20.roll raise DNDRollerError (not caught by more specific handlers)
            mock_d20.roll.side_effect = DNDRollerError("Test DNDRollerError")
            mock_d20.RollSyntaxError = type("RollSyntaxError", (Exception,), {})
            handler = RollHandler(RollService())
            fields = ["!r", "grog", "1d20"]

            await handler.handle(mock_message, guild_data, user_with_character, fields)

            # Should hit line 57-58: logger.exception + "Error: {ex}"
            assert len(mock_message.channel._sent_messages) > 0
            msg = mock_message.channel._sent_messages[0].lower()
            assert "error:" in msg

    @pytest.mark.asyncio
    async def test_unexpected_error_path(self, mock_message, guild_data, user_with_character) -> None:
        """Test handling unexpected exception path."""
        with patch("bot.handlers.roll.d20") as mock_d20:
            # This mock makes roll fail in an unexpected way (not DNDRollerError or RollSyntaxError)
            mock_d20.roll.side_effect = RuntimeError("Unexpected!")
            mock_d20.RollSyntaxError = type("RollSyntaxError", (Exception,), {})
            handler = RollHandler(RollService())
            fields = ["!r", "grog", "1d20"]

            await handler.handle(mock_message, guild_data, user_with_character, fields)

            # Should hit line 60-61: logger.exception + "An unexpected error occurred..."
            assert len(mock_message.channel._sent_messages) > 0
            msg = mock_message.channel._sent_messages[0].lower()
            assert "unexpected error" in msg
