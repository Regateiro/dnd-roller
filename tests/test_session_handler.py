"""Unit tests for the SessionHandler."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from bot.handlers.session import SessionHandler
from bot.models import Character, GuildData, Stat, User
from bot.services.session import SessionService


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
    """Create guild data with weekday set for faster tests."""
    data = GuildData()
    data.sessions.wday = 0  # Monday - set for faster session lookup
    return data


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
def session_handler():
    """Create a SessionHandler."""
    return SessionHandler(SessionService())


class TestSessionHandler:
    """Tests for the SessionHandler class."""

    @pytest.mark.asyncio
    async def test_handle_help(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test handling the help command."""
        fields = ["!session", "help"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_weekday(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test setting the weekday."""
        fields = ["!session", "weekday", "monday"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_schedule(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test scheduling a session."""
        fields = ["!session", "schedule", "2025-06-15"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_cancel(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling a session."""
        fields = ["!session", "cancel", "2025-06-15"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_available(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test setting user available."""
        fields = ["!session", "available", "2025-06-15"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_unavailable(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test setting user unavailable."""
        fields = ["!session", "unavailable", "2025-06-15"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_list(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test listing sessions."""
        fields = ["!session", "list"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_next(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test showing next session."""
        fields = ["!session", "next"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestSessionHandlerErrors:
    """Tests for SessionHandler error handling."""

    @pytest.mark.asyncio
    async def test_handle_invalid_date(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test handling invalid date format."""
        fields = ["!session", "schedule", "invalid-date"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_handle_invalid_weekday(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test handling invalid weekday."""
        fields = ["!session", "weekday", "invalid_day"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestSessionHandlerBranches:
    """Tests for SessionHandler branch coverage."""

    @pytest.mark.asyncio
    async def test_schedule_on_existing_day(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test scheduling on a day that already has a session."""
        guild_data.sessions.wday = 5  # Friday
        # Use a far future date to avoid collision with other tests
        future_date = "2030-06-06"  # Friday
        fields = ["!session", "schedule", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # First call schedules the session
        assert len(mock_message.channel._sent_messages) > 0
        # Reset messages for second call
        mock_message.channel._sent_messages.clear()

        # Second call should detect existing session
        fields = ["!session", "schedule", future_date]
        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "already have a session" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_schedule_adds_extra_session(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test scheduling on a non-default day adds extra session."""
        guild_data.sessions.wday = 0  # Monday
        # Use a future date - get next Tuesday (not Monday)
        today = datetime.now()
        days_until_tuesday = (1 - today.weekday()) % 7
        next_tuesday = today + timedelta(days=days_until_tuesday if days_until_tuesday > 0 else 7)
        future_tuesday = next_tuesday.strftime("%Y-%m-%d")
        fields = ["!session", "schedule", future_tuesday]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "scheduled" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_cancel_extra_session(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling an extra session."""
        guild_data.sessions.on.append("2025-06-15")
        fields = ["!session", "cancel", "2025-06-15"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_cancel_regular_session(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling a regular session day."""
        guild_data.sessions.wday = 5  # Friday
        fields = ["!session", "cancel", "2025-06-06"]  # Friday

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_schedule_past_date(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test scheduling a past date."""
        fields = ["!session", "schedule", "2020-01-01"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        assert "time" in mock_message.channel._sent_messages[0].lower()

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_session(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling a session that doesn't exist."""
        fields = ["!session", "cancel", "2025-06-15"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0


class TestSessionHandlerErrorPaths:
    """Tests for SessionHandler error handling paths."""

    @pytest.mark.asyncio
    async def test_invalid_date_error_path(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test handling InvalidDateError path."""
        fields = ["!session", "schedule", "invalid-date"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "invalid" in msg or "date" in msg

    @pytest.mark.asyncio
    async def test_value_error_path(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test handling ValueError path."""
        # Patch parse_date to raise ValueError
        original_parse_date = session_handler._session_service.parse_date

        def mock_parse_date(date_str):
            raise ValueError("Invalid value")

        session_handler._session_service.parse_date = mock_parse_date
        fields = ["!session", "schedule", "2025-06-15"]

        try:
            await session_handler.handle(mock_message, guild_data, user_with_character, fields)
        finally:
            session_handler._session_service.parse_date = original_parse_date

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "invalid" in msg

    @pytest.mark.asyncio
    async def test_unexpected_error_path(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test handling unexpected exception path."""
        # Patch _handle_internal to raise an unexpected exception
        original_handle = session_handler._handle_internal

        async def mock_handle(message, guild_data, user, fields):
            raise RuntimeError("Unexpected error!")

        session_handler._handle_internal = mock_handle

        try:
            fields = ["!session", "list"]
            await session_handler.handle(mock_message, guild_data, user_with_character, fields)
        finally:
            session_handler._handle_internal = original_handle

        assert len(mock_message.channel._sent_messages) > 0
        msg = mock_message.channel._sent_messages[0].lower()
        assert "unexpected" in msg


class TestSessionHandlerBranchesExtra:
    """Tests for SessionHandler additional branch coverage."""

    @pytest.mark.asyncio
    async def test_unknown_command_returns_early(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test that unknown session command returns early with no message."""
        fields = ["!session", "invalid_command"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Unknown command returns early, no message sent
        assert len(mock_message.channel._sent_messages) == 0

    @pytest.mark.asyncio
    async def test_schedule_removes_from_off(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test that scheduling removes date from off list."""
        guild_data.sessions.wday = 0  # Monday
        guild_data.sessions.off.append("2025-06-02")  # Monday
        future_date = "2030-06-02"
        fields = ["!session", "schedule", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Should have removed from off
        assert "2025-06-02" not in guild_data.sessions.off

    @pytest.mark.asyncio
    async def test_cancel_regular_session(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling a regular session day (not extra)."""
        guild_data.sessions.wday = 0  # Monday
        # User is unavailable on a Monday
        user_with_character.unavailability.append("2030-06-01")  # Monday
        fields = ["!session", "cancel", "2030-06-01"]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_available_user(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test setting user available - message is sent."""
        guild_data.sessions.wday = 0  # Monday
        # Use date that is actually a session day (Monday June 2, 2030)
        future_date = "2030-06-02"  # Monday
        fields = ["!session", "available", future_date]
        user_with_character.unavailability.append(future_date)

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Message should be sent (either case)
        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_available_user_not_session_day(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test setting user available on non-session day."""
        guild_data.sessions.wday = 0  # Monday
        # Use a Friday (not a session day)
        future_date = "2030-06-06"  # Friday
        fields = ["!session", "available", future_date]
        user_with_character.unavailability.append(future_date)

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Should say not a session day
        msg = mock_message.channel._sent_messages[0].lower()
        assert "do not recall" in msg or "session" in msg

    @pytest.mark.asyncio
    async def test_unavailable_user(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test setting user unavailable on session day."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2030-06-02"  # Monday
        fields = ["!session", "unavailable", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Message should be sent
        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_unavailable_user_not_session_day(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test setting user unavailable on non-session day."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2030-06-06"  # Friday (not Monday)
        fields = ["!session", "unavailable", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Should say not a session day
        msg = mock_message.channel._sent_messages[0].lower()
        assert "do not recall" in msg or "session" in msg

    @pytest.mark.asyncio
    async def test_cancel_extra_session(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling an extra session from the 'on' list."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2030-06-02"  # Monday
        guild_data.sessions.on.append(future_date)  # Add as extra session
        fields = ["!session", "cancel", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert future_date not in guild_data.sessions.on
        msg = mock_message.channel._sent_messages[0].lower()
        assert "extra" in msg

    @pytest.mark.asyncio
    async def test_cancel_regular_session_already_off(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling a regular session that is already in the off list."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2025-06-02"  # Monday

        # Set up: NOT in on list, IS in off list
        guild_data.sessions.off = [future_date]
        guild_data.sessions.on = []  # Not in extra sessions

        fields = ["!session", "cancel", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Should hit the case where it's a regular session day, already in off list
        assert len(mock_message.channel._sent_messages) > 0

    @pytest.mark.asyncio
    async def test_schedule_adds_and_removes_from_off(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test scheduling removes date from off list."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2025-06-09"  # Monday (different from previous test)
        guild_data.sessions.off.append(future_date)  # Date was previously unavailable
        fields = ["!session", "schedule", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        # Should have removed from off
        assert future_date not in guild_data.sessions.off

    @pytest.mark.asyncio
    async def test_cancel_regular_session_cancelled(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling a regular session (adds to off list)."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2025-06-16"  # Monday
        # Not in on list, not in off list
        fields = ["!session", "cancel", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert future_date in guild_data.sessions.off
        msg = mock_message.channel._sent_messages[0].lower()
        assert "sunday" in msg or "cancelled" in msg

    @pytest.mark.asyncio
    async def test_available_user_already_available(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test available when user was already available (not in unavailability)."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2025-06-23"  # Monday
        # User is NOT in unavailability list
        assert future_date not in user_with_character.unavailability
        fields = ["!session", "available", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        msg = mock_message.channel._sent_messages[0].lower()
        assert "glad" in msg or "couldn't" in msg

    @pytest.mark.asyncio
    async def test_unavailable_user_already_unavailable(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test unavailable when user was already unavailable."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2025-06-30"  # Monday
        user_with_character.unavailability.append(future_date)
        assert future_date in user_with_character.unavailability
        fields = ["!session", "unavailable", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        msg = mock_message.channel._sent_messages[0].lower()
        assert "know" in msg or "we know" in msg

    @pytest.mark.asyncio
    async def test_schedule_remove_extra_from_off(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test scheduling removes from off list when not regular session day."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2030-07-05"  # Saturday (not Monday)
        guild_data.sessions.off.append(future_date)
        fields = ["!session", "schedule", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert future_date not in guild_data.sessions.off

    @pytest.mark.asyncio
    async def test_cancel_regular_session_still_on(self, mock_message, guild_data, user_with_character, session_handler) -> None:
        """Test canceling still shows message even when session already in off."""
        guild_data.sessions.wday = 0  # Monday
        future_date = "2030-07-13"  # Monday
        guild_data.sessions.off.append(future_date)
        fields = ["!session", "cancel", future_date]

        await session_handler.handle(mock_message, guild_data, user_with_character, fields)

        assert len(mock_message.channel._sent_messages) > 0
