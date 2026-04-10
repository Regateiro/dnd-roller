"""Unit tests for the session service."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from bot.models import GuildData, User
from bot.services.session import SessionService


class TestSessionService:
    """Tests for the SessionService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = SessionService()

    def test_parse_date(self) -> None:
        """Test parsing date string."""
        result = self.service.parse_date("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_format_date(self) -> None:
        """Test formatting date."""
        date = datetime(2024, 1, 15)
        result = self.service.format_date(date)
        assert result == "2024-01-15"

    def test_is_session_day_weekday_match(self) -> None:
        """Test session day when weekday matches and not cancelled."""
        guild_data = GuildData()
        guild_data.sessions.wday = 0  # Monday
        date = datetime(2024, 1, 1)  # This is a Monday
        assert self.service.is_session_day(date, guild_data) is True

    def test_is_session_day_weekday_mismatch(self) -> None:
        """Test session day when weekday doesn't match."""
        guild_data = GuildData()
        guild_data.sessions.wday = 0  # Monday
        date = datetime(2024, 1, 2)  # This is a Tuesday
        assert self.service.is_session_day(date, guild_data) is False

    def test_is_session_day_cancelled(self) -> None:
        """Test session day when weekday matches but cancelled."""
        guild_data = GuildData()
        guild_data.sessions.wday = 0
        guild_data.sessions.off = ["2024-01-01"]
        date = datetime(2024, 1, 1)
        assert self.service.is_session_day(date, guild_data) is False

    def test_is_session_day_extra_scheduled(self) -> None:
        """Test session day when extra session scheduled."""
        guild_data = GuildData()
        guild_data.sessions.wday = 0
        guild_data.sessions.on = ["2024-01-02"]
        date = datetime(2024, 1, 2)
        assert self.service.is_session_day(date, guild_data) is True

    def test_get_missing_players_none(self) -> None:
        """Test no missing players."""
        guild_data = GuildData()
        user = User(name="TestUser")
        guild_data.users["user1"] = user
        result = self.service.get_missing_players("2024-01-01", guild_data)
        assert result == []

    def test_get_missing_players_some(self) -> None:
        """Test some missing players."""
        guild_data = GuildData()
        user1 = User(name="Player1")
        user2 = User(name="Player2")
        user1.unavailability = ["2024-01-01"]
        guild_data.users["user1"] = user1
        guild_data.users["user2"] = user2
        result = self.service.get_missing_players("2024-01-01", guild_data)
        assert "Player1" in result
        assert "Player2" not in result

    def test_clean_sessions_removes_old_on(self) -> None:
        """Test cleaning removes old sessions."""
        guild_data = GuildData()
        guild_data.sessions.on = ["2020-01-01"]
        user = User(name="TestUser")
        user.unavailability = ["2020-01-01"]
        guild_data.users["user1"] = user
        self.service.clean_sessions(guild_data, user)
        assert guild_data.sessions.on == []
        assert user.unavailability == []

    def test_clean_sessions_keeps_future(self) -> None:
        """Test cleaning keeps future sessions."""
        future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        guild_data = GuildData()
        guild_data.sessions.on = [future]
        user = User(name="TestUser")
        user.unavailability = [future]
        guild_data.users["user1"] = user
        self.service.clean_sessions(guild_data, user)
        assert future in guild_data.sessions.on
        assert future in user.unavailability

    def test_get_upcoming_sessions(self) -> None:
        """Test getting upcoming sessions."""
        guild_data = GuildData()
        guild_data.sessions.wday = 0
        sessions = self.service.get_upcoming_sessions(guild_data, count=2)
        assert len(sessions) == 2
        for datestr, missing in sessions:
            assert datestr is not None
            assert isinstance(missing, list)

    def test_get_next_session(self) -> None:
        """Test getting next session."""
        guild_data = GuildData()
        guild_data.sessions.wday = 0
        result = self.service.get_next_session(guild_data)
        assert result is not None
        datestr, missing = result
        assert datestr is not None
        assert isinstance(missing, list)

    def test_get_next_session_no_sessions(self) -> None:
        """Test getting next session when none configured."""
        guild_data = GuildData()
        guild_data.sessions.wday = -1
        result = self.service.get_next_session(guild_data)
        assert result is None
