"""Unit tests for the UtilityHandler."""

from __future__ import annotations

import pytest

from bot.handlers.utility import UtilityHandler
from bot.models import Character, GuildData, Stat, User


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
        stats={s: 10 for s in Stat},
    )
    return user


@pytest.fixture
def utility_handler():
    """Create a UtilityHandler."""
    return UtilityHandler()


class TestUtilityHandlerDistance:
    """Tests for the UtilityHandler distance command."""

    @pytest.mark.asyncio
    async def test_handle_distance_xy(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test distance calculation with x and y."""
        fields = ["!distance", "10", "20", "0"]

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_distance_insufficient_info(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test distance calculation with insufficient info (only one side)."""
        fields = ["!distance", "10", "0", "0"]  # Only x provided

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "wizard" in msg or "two sides" in msg

    @pytest.mark.asyncio
    async def test_handle_distance_xd(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test distance calculation with x and diagonal."""
        fields = ["!distance", "10", "0", "25"]

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_distance_yd(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test distance calculation with y and diagonal."""
        fields = ["!distance", "0", "20", "25"]

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_distance_all(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test distance calculation with all three sides."""
        fields = ["!distance", "10", "20", "25"]

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_distance_invalid(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test distance with invalid arguments."""
        fields = ["!distance", "a", "b", "c"]

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestUtilityHandlerFall:
    """Tests for the UtilityHandler fall command."""

    @pytest.mark.asyncio
    async def test_handle_fall_under_500(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test fall calculation for height under 500."""
        fields = ["!f", "100"]

        await utility_handler.handle_fall(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "100" in mock_message.channel._sent_messages[0]

    @pytest.mark.asyncio
    async def test_handle_fall_over_500(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test fall calculation for height over 500."""
        fields = ["!f", "600"]

        await utility_handler.handle_fall(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "600" in mock_message.channel._sent_messages[0]

    @pytest.mark.asyncio
    async def test_handle_fall_invalid(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test fall with invalid height."""
        fields = ["!f", "abc"]

        await utility_handler.handle_fall(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestUtilityHandlerHelp:
    """Tests for the UtilityHandler help command."""

    @pytest.mark.asyncio
    async def test_handle_help(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test help command."""
        fields = ["!help"]

        await utility_handler.handle_help(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) >= 3


class TestUtilityHandlerMacro:
    """Tests for the UtilityHandler macro command."""

    @pytest.mark.asyncio
    async def test_handle_macro_set(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test setting a macro."""
        fields = ["!macro", "set", "grog", "attack", "1d8+3"]

        await utility_handler.handle_macro(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_macro_delete(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test deleting a macro."""
        user_with_character.characters["grog"].macros["attack"] = "1d8+3"
        fields = ["!macro", "delete", "grog", "attack"]

        await utility_handler.handle_macro(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_macro_list(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test listing macros."""
        user_with_character.characters["grog"].macros["attack"] = "1d8+3"
        fields = ["!macro", "list", "grog"]

        await utility_handler.handle_macro(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_macro_help(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test macro help."""
        fields = ["!macro", "help"]

        await utility_handler.handle_macro(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestUtilityHandlerVariable:
    """Tests for the UtilityHandler variable command."""

    @pytest.mark.asyncio
    async def test_handle_variable_set(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test setting a variable."""
        fields = ["!variable", "set", "grog", "bless", "1d4"]

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_variable_delete(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test deleting a variable."""
        user_with_character.characters["grog"].variables["bless"] = "1d4"
        fields = ["!variable", "delete", "grog", "bless"]

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_variable_list(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test listing variables."""
        user_with_character.characters["grog"].variables["bless"] = "1d4"
        fields = ["!variable", "list", "grog"]

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_variable_help(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test variable help."""
        fields = ["!variable", "help"]

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestUtilityHandlerErrorPaths:
    """Tests for UtilityHandler error paths."""

    @pytest.mark.asyncio
    async def test_handle_distance_wrong_arg_count(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test handling distance with wrong number of arguments."""
        fields = ["!distance", "10", "20"]  # Only 3 args, needs 4

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "wrong number" in msg or "arguments" in msg

    @pytest.mark.asyncio
    async def test_handle_fall_wrong_arg_count(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test handling fall with wrong number of arguments."""
        fields = ["!f"]  # Missing height

        await utility_handler.handle_fall(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "wrong number" in msg or "arguments" in msg

    @pytest.mark.asyncio
    async def test_handle_distance_invalid_number(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test handling distance with invalid number format."""
        fields = ["!distance", "abc", "20", "0"]

        await utility_handler.handle_distance(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "invalid" in msg or "integer" in msg

    @pytest.mark.asyncio
    async def test_handle_macro_unknown_command(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test handling unknown macro command."""
        fields = ["!macro", "invalid_command"]

        await utility_handler.handle_macro(mock_message, guild_data, user_with_character, fields)

        # Unknown command returns early, no message sent
        assert len(mock_message.channel._sent_messages) == 0

    @pytest.mark.asyncio
    async def test_handle_macro_missing_args(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test handling macro with missing arguments."""
        fields = ["!macro", "set", "grog"]  # Missing macro name and value

        await utility_handler.handle_macro(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "missing" in msg

    @pytest.mark.asyncio
    async def test_handle_variable_unknown_command(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test handling unknown variable command."""
        fields = ["!variable", "invalid_command"]

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        # Unknown command returns early, no message sent
        assert len(mock_message.channel._sent_messages) == 0

    @pytest.mark.asyncio
    async def test_handle_macro_error_exception(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test handling exception in macro handler (IndexError path)."""
        # Not enough args triggers IndexError in variable handler
        fields = ["!variable", "set"]  # Not enough args

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_macro_no_character(self, mock_message, guild_data, utility_handler) -> None:
        """Test handling macro command with no active character."""
        user = User(name="testuser")
        user.active = ""  # No active character
        fields = ["!macro", "list"]  # No character specified

        await utility_handler.handle_macro(mock_message, guild_data, user, fields)

        # Should fail because no character is specified
        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_delete_macro_not_exists(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test deleting a macro that doesn't exist."""
        fields = ["!macro", "delete", "grog", "nonexistent_macro"]

        await utility_handler.handle_macro(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "no such macro" in msg or "doesn't exist" in msg

    @pytest.mark.asyncio
    async def test_list_variables_empty(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test listing variables when character has none."""
        user_with_character.characters["grog"].variables = {}  # No variables
        fields = ["!variable", "list", "grog"]

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_delete_variable_not_exists(self, mock_message, guild_data, user_with_character, utility_handler) -> None:
        """Test deleting a variable that doesn't exist."""
        user_with_character.characters["grog"].variables = {}  # No variables
        fields = ["!variable", "delete", "grog", "nonexistent"]

        await utility_handler.handle_variable(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "no such variable" in msg
