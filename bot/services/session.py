"""Session management service for the D&D Roller bot."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from dateutil.parser import parse

from bot.exceptions import InvalidDateError

if TYPE_CHECKING:
    from bot.models import GuildData, User


class SessionService:
    """Service for managing D&D sessions."""

    def clean_sessions(self, guild_data: GuildData, current_user: User) -> None:
        """Clean up expired sessions and unavailability entries.

        Removes sessions and unavailability dates that are in the past.

        Args:
            guild_data: The guild data to clean.
            current_user: The current user (used for accessing user data).
        """
        now = datetime.now().strftime("%Y-%m-%d")

        guild_data.sessions.on = [s for s in guild_data.sessions.on if s >= now]
        guild_data.sessions.off = [s for s in guild_data.sessions.off if s >= now]

        for user in guild_data.users.values():
            user.unavailability = [s for s in user.unavailability if s >= now]

    def parse_date(self, date_str: str) -> datetime:
        """Parse a date string into a datetime object.

        Args:
            date_str: The date string to parse (e.g., "2024-01-15").

        Returns:
            A datetime object representing the parsed date.

        Raises:
            InvalidDateError: If the date string cannot be parsed.
        """
        try:
            return parse(date_str)
        except (ValueError, TypeError) as e:
            raise InvalidDateError(date_str) from e

    def format_date(self, date: datetime) -> str:
        """Format a datetime object to YYYY-MM-DD string.

        Args:
            date: The datetime object to format.

        Returns:
            A string in YYYY-MM-DD format.
        """
        return date.strftime("%Y-%m-%d")

    def is_session_day(self, date: datetime, guild_data: GuildData) -> bool:
        """Check if a given date is a session day.

        A date is a session day if it matches the guild's default weekday
        and is not in the cancelled list, or if it's in the special sessions list.

        Args:
            date: The date to check.
            guild_data: The guild data containing session configuration.

        Returns:
            True if the date is a session day, False otherwise.
        """
        datestr = self.format_date(date)
        return (date.weekday() == guild_data.sessions.wday and datestr not in guild_data.sessions.off) or datestr in guild_data.sessions.on

    def get_missing_players(self, date: str, guild_data: GuildData) -> list[str]:
        """Get list of missing players for a given date.

        Args:
            date: The date string (YYYY-MM-DD) to check.
            guild_data: The guild data containing user information.

        Returns:
            A list of user names who are unavailable for the session.
        """
        return [guild_data.users[u].name for u in guild_data.users.keys() if date in guild_data.users[u].unavailability]

    def get_upcoming_sessions(self, guild_data: GuildData, count: int = 4) -> list[tuple[str, list[str]]]:
        """Get upcoming sessions with missing players.

        Args:
            guild_data: The guild data containing session configuration.
            count: The number of upcoming sessions to retrieve (default: 4).

        Returns:
            A list of tuples containing (date_string, missing_players_list).
        """
        sessions = []
        date = datetime.now()
        while len(sessions) < count:
            datestr = self.format_date(date)
            if self.is_session_day(date, guild_data):
                sessions.append((datestr, self.get_missing_players(datestr, guild_data)))
            date += timedelta(days=1)
        return sessions

    def get_next_session(self, guild_data: GuildData) -> tuple[str, list[str]] | None:
        """Get the next scheduled session with missing players.

        Looks up to 30 days ahead for the next session.

        Args:
            guild_data: The guild data containing session configuration.

        Returns:
            A tuple of (date_string, missing_players_list) if a session exists,
            or None if no session is found within 30 days.
        """
        date = datetime.now()
        limit = date + timedelta(days=30)
        while date <= limit:
            datestr = self.format_date(date)
            if self.is_session_day(date, guild_data):
                return (datestr, self.get_missing_players(datestr, guild_data))
            date += timedelta(days=1)
        return None
