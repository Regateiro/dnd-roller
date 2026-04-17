"""Unit tests for the CharacterHandler."""

from __future__ import annotations

import pytest

from bot.handlers.character import CharacterHandler
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
def character_handler():
    """Create a CharacterHandler."""
    return CharacterHandler()


class TestCharacterHandler:
    """Tests for the CharacterHandler class."""

    @pytest.mark.asyncio
    async def test_handle_help(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling the help command."""
        fields = ["!character", "help"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_create_character(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test creating a new character."""
        fields = ["!character", "create", "newguy", "3", "10", "12", "14", "12", "10", "8", "|", "str", "|", "athletics", "|", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "newguy" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_create_duplicate_character(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test creating a duplicate character."""
        fields = ["!character", "create", "grog", "3", "10", "12", "14", "12", "10", "8", "|", "|", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "already exists" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_delete_character(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test deleting a character."""
        fields = ["!character", "delete", "grog"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "removed" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_delete_nonexistent_character(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test deleting a nonexistent character."""
        fields = ["!character", "delete", "nonexistent"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "no such character" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_set_active(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test setting active character."""
        user_with_character.characters["other"] = Character(
            level=1,
            stats={s: 10 for s in Stat},
        )
        fields = ["!character", "active", "other"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "other" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_active_display(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test displaying active character."""
        fields = ["!character", "active"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_character_info(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test getting character info."""
        fields = ["!character", "info", "grog"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_list_characters(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test listing characters."""
        fields = ["!character", "list"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "grog" in mock_message.channel._sent_messages[0].lower()


class TestCharacterHandlerUpdates:
    """Tests for CharacterHandler update commands."""

    @pytest.mark.asyncio
    async def test_handle_update_main(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating main stats."""
        fields = ["!character", "update", "grog", "main", "6", "14", "14", "12", "10", "8", "10"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "updated" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_update_saves(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating saving throws."""
        fields = ["!character", "update", "grog", "saves", "str", "dex", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_update_bonus(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating bonuses."""
        fields = ["!character", "update", "grog", "bonus", "2", "1"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_update_skills(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating skill proficiencies."""
        fields = ["!character", "update", "grog", "skills", "athletics", "perception", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_update_expertise(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating skill expertise."""
        fields = ["!character", "update", "grog", "expertise", "perception", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_update_advantage(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating advantage conditions."""
        fields = ["!character", "update", "grog", "advantage", "str", "athletics"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestCharacterHandlerErrors:
    """Tests for CharacterHandler error handling."""

    @pytest.mark.asyncio
    async def test_handle_invalid_stat(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling invalid stat in saves."""
        fields = ["!character", "update", "grog", "saves", "invalid_stat", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "invalid" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_invalid_skill(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling invalid skill."""
        fields = ["!character", "update", "grog", "skills", "invalid_skill", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "invalid" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_handle_missing_fields(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling missing fields for create."""
        fields = ["!character", "create"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestCharacterHandlerErrorPaths:
    """Tests for CharacterHandler error handling paths."""

    @pytest.mark.asyncio
    async def test_invalid_stat_error_path(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling InvalidStatError path."""
        fields = ["!character", "update", "grog", "saves", "invalid_stat", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "invalid" in msg

    @pytest.mark.asyncio
    async def test_invalid_skill_error_path(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling InvalidSkillError path."""
        fields = ["!character", "update", "grog", "skills", "invalid_skill", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "invalid" in msg

    @pytest.mark.asyncio
    async def test_value_error_path(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling ValueError path."""
        fields = ["!character", "update", "grog", "main", "not_a_number", "10", "10", "10", "10", "10", "10"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "invalid" in msg

    @pytest.mark.asyncio
    async def test_unexpected_error_path(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling unexpected exception path."""
        with pytest.MonkeyPatch.context() as mp:
            # Patch _handle_internal to raise an unexpected exception
            async def mock_handle(message, user, fields):
                raise RuntimeError("Unexpected error!")

            mp.setattr(character_handler, "_handle_internal", mock_handle)

            fields = ["!character", "list"]

            await character_handler.handle(mock_message, guild_data, user_with_character, fields)

            assert len(mock_message.channel._sent_messages) > 0
            msg = mock_message.channel._sent_messages[0].lower()
            assert "unexpected" in msg


class TestCharacterHandlerBranches:
    """Tests for CharacterHandler branch coverage."""

    @pytest.mark.asyncio
    async def test_unknown_command_returns_early(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test that unknown character command returns early with no message."""
        fields = ["!character", "invalid_command"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Unknown command returns early, no message sent
        assert len(mock_message.channel._sent_messages) == 0

    @pytest.mark.asyncio
    async def test_invalid_character_data_error_path(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling InvalidCharacterDataError path."""
        # Trigger the error path by having _handle_internal raise it
        async def mock_internal(message, user, fields):
            from bot.exceptions import InvalidCharacterDataError
            raise InvalidCharacterDataError("Test error")

        character_handler._handle_internal = mock_internal
        fields = ["!character", "list"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_value_error_in_create_character(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test ValueError in _create_character raises InvalidCharacterDataError."""
        # Try to create a character with invalid stats (non-integer)
        fields = ["!character", "create", "newguy", "not_a_level", "10", "12", "14", "12", "10", "8", "|", "|", "|", "|", "|"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Should get an error message about invalid character data
        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_invalid_stat_error_path(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling InvalidStatError path was removed."""
        async def mock_internal(message, user, fields):
            from bot.exceptions import InvalidSkillError
            raise InvalidSkillError("strength")

        original_internal = character_handler._handle_internal
        character_handler._handle_internal = mock_internal

        try:
            fields = ["!character", "list"]
            await character_handler.handle(mock_message, guild_data, user_with_character, fields)

            assert len(mock_message.channel._sent_messages) > 0
            msg = mock_message.channel._sent_messages[0].lower()
            assert "invalid skill" in msg or "invalid" in msg
        finally:
            character_handler._handle_internal = original_internal

    @pytest.mark.asyncio
    async def test_invalid_skill_error_path(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test handling InvalidSkillError path."""
        # Make _handle_internal raise InvalidSkillError
        async def mock_internal(message, user, fields):
            from bot.exceptions import InvalidSkillError
            raise InvalidSkillError("invalid_skill")

        original_internal = character_handler._handle_internal
        character_handler._handle_internal = mock_internal

        try:
            fields = ["!character", "list"]
            await character_handler.handle(mock_message, guild_data, user_with_character, fields)

            assert len(mock_message.channel._sent_messages) > 0
            msg = mock_message.channel._sent_messages[0].lower()
            assert "invalid skill" in msg or "invalid" in msg
        finally:
            character_handler._handle_internal = original_internal


class TestCharacterHandlerUpdate:
    """Tests for CharacterHandler update methods."""

    @pytest.mark.asyncio
    async def test_update_nonexistent_character(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating a character that doesn't exist."""
        fields = ["!character", "update", "nonexistent", "main", "5", "10", "10", "10", "10", "10", "10"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "no such character" in msg

    @pytest.mark.asyncio
    async def test_update_unknown_type(self, mock_message, guild_data, user_with_character, character_handler, monkeypatch) -> None:
        """Test updating with update type not in handler dict."""
        from bot.commands import CHARACTER_UPDATE_ALIASES
        # Add an alias that maps to a command NOT in update_handlers
        monkeypatch.setitem(CHARACTER_UPDATE_ALIASES, "missing_handler", ("missing",))
        fields = ["!character", "update", "grog", "missing"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "unknown update type" in msg

    @pytest.mark.asyncio
    async def test_create_character_invalid_skill(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test creating a character with an invalid skill raises error."""
        user_no_chars = User(name="test_no_char")
        fields = [
            "!character", "create", "badguy", "3",
            "10", "12", "14", "12", "10", "8",
            "|", "invalid_stat", "|"
        ]

        await character_handler.handle(mock_message, guild_data, user_no_chars, fields)
        assert len(mock_message.channel._sent_messages) > 0
        sent = mock_message.channel._sent_messages[0]
        assert "Invalid skill:" in sent
        assert "invalid_stat" in sent

    @pytest.mark.asyncio
    async def test_update_bonus_with_jack_of_all_trades(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating bonus with jack_of_all_trades parameter."""
        fields = ["!character", "update", "grog", "bonus", "2", "1", "true"]
        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert user_with_character.characters["grog"].jack_of_all_trades is True

    @pytest.mark.asyncio
    async def test_update_skills_success_no_trailing_delimiter(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating skills without a trailing delimiter succeeds."""
        fields = ["!character", "update", "grog", "skills", "athletics", "perception"]
        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        sent = mock_message.channel._sent_messages[0]
        assert "updated" in sent.lower()
        assert set(user_with_character.characters["grog"].skill_prof) == {"athletics", "perception"}

    @pytest.mark.asyncio
    async def test_update_advantage_unknown_skill(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating advantage with unknown skill."""
        user_with_character.characters["grog"] = Character(
            level=5,
            stats={
                Stat.STRENGTH: 16,
                Stat.DEXTERITY: 14,
                Stat.CONSTITUTION: 14,
                Stat.INTELLIGENCE: 10,
                Stat.WISDOM: 12,
                Stat.CHARISMA: 8,
            },
        )
        fields = ["!character", "update", "grog", "advantage", "unknown_skill"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "unknown ability/skill" in msg

    @pytest.mark.asyncio
    async def test_set_active_nonexistent(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test setting active character that doesn't exist."""
        user_with_character.active = ""
        fields = ["!character", "active", "nonexistent"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "no such character" in msg

    @pytest.mark.asyncio
    async def test_update_bonus_wrong_args(self, mock_message, guild_data, user_with_character, character_handler) -> None:
        """Test updating bonus with wrong number of arguments."""
        user_with_character.characters["grog"] = Character(
            level=5,
            stats={
                Stat.STRENGTH: 16,
                Stat.DEXTERITY: 14,
                Stat.CONSTITUTION: 14,
                Stat.INTELLIGENCE: 10,
                Stat.WISDOM: 12,
                Stat.CHARISMA: 8,
            },
        )
        fields = ["!character", "update", "grog", "bonus", "2"]

        await character_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "wrong number" in msg
