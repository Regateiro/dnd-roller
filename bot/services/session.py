"""Session management service for the D&D Roller bot."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from dateutil.parser import parse

import calendar

if TYPE_CHECKING:
    from models import GuildData, User


class SessionService:
    """Service for managing D&D sessions."""

    def clean_sessions(self, guild_data: GuildData, current_user: User) -> None:
        """Clean up expired sessions and unavailability entries."""
        now = datetime.now().strftime("%Y-%m-%d")

        guild_data.sessions.on = [s for s in guild_data.sessions.on if s >= now]
        guild_data.sessions.off = [s for s in guild_data.sessions.off if s >= now]

        for user in guild_data.users.values():
            user.unavailability = [s for s in user.unavailability if s >= now]

    def parse_date(self, date_str: str) -> datetime:
        """Parse a date string into a datetime object."""
        return parse(date_str)

    def format_date(self, date: datetime) -> str:
        """Format a datetime object to YYYY-MM-DD string."""
        return date.strftime("%Y-%m-%d")

    def is_session_day(self, date: datetime, guild_data: GuildData) -> bool:
        """Check if a given date is a session day."""
        datestr = self.format_date(date)
        return (date.weekday() == guild_data.sessions.wday and datestr not in guild_data.sessions.off) or datestr in guild_data.sessions.on

    def get_missing_players(self, date: str, guild_data: GuildData) -> list[str]:
        """Get list of missing players for a given date."""
        return [
            guild_data.users[u].name
            for u in guild_data.users.keys()
            if date in guild_data.users[u].unavailability
        ]

    def get_upcoming_sessions(self, guild_data: GuildData, count: int = 4) -> list[tuple[str, list[str]]]:
        """Get upcoming sessions with missing players."""
        sessions = []
        date = datetime.now()
        while len(sessions) < count:
            datestr = self.format_date(date)
            if self.is_session_day(date, guild_data):
                sessions.append((datestr, self.get_missing_players(datestr, guild_data)))
            date += timedelta(days=1)
        return sessions

    def get_next_session(self, guild_data: GuildData) -> tuple[str, list[str]] | None:
        """Get the next scheduled session with missing players."""
        date = datetime.now()
        while True:
            datestr = self.format_date(date)
            if self.is_session_day(date, guild_data):
                return (datestr, self.get_missing_players(datestr, guild_data))
            date += timedelta(days=1)
