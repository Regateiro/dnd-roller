"""Session management command handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import calendar

from bot.commands import SESSION_COMMAND_ALIASES, HELP_ALIASES, resolve_command_alias
from bot.services.session import SessionService
from bot.models import GuildData, User
from bot.utils import strings

if TYPE_CHECKING:
    import discord
    from discord import Message


class SessionHandler:
    """Handler for session management commands (!session, !s)."""

    def __init__(self, session_service: SessionService) -> None:
        self._session_service = session_service

    async def handle(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle session management commands."""
        self._session_service.clean_sessions(guild_data, user)

        if len(fields) == 1 or fields[1] in HELP_ALIASES:
            await message.channel.send(strings.SESSION_HELP)
            return

        command = resolve_command_alias(SESSION_COMMAND_ALIASES, fields[1])
        if command is None:
            return

        handlers = {
            "weekday": self._handle_weekday,
            "schedule": self._handle_schedule,
            "cancel": self._handle_cancel,
            "available": self._handle_available,
            "unavailable": self._handle_unavailable,
            "list": self._handle_list,
            "next": self._handle_next,
        }

        handler = handlers.get(command)
        if handler:
            await handler(message, guild_data, user, fields)

    async def _handle_weekday(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Set the default session weekday."""
        day = [x.lower() for x in list(calendar.day_name)].index(fields[2].lower())
        guild_data.sessions.wday = day
        await message.channel.send(f"Default session weekday set to {calendar.day_name[guild_data.sessions.wday]}.")

    async def _handle_schedule(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Schedule a new session."""
        date = self._session_service.parse_date(fields[2])
        if date.date() < date.now().date():
            await message.channel.send("I'm also eager, but even I cannot go back in time.")
            return

        datestr = self._session_service.format_date(date)
        if self._session_service.is_session_day(date, guild_data):
            await message.channel.send("We already have a session on that day.")
            return

        if date.weekday() != guild_data.sessions.wday:
            guild_data.sessions.on.append(datestr)

        if datestr in guild_data.sessions.off:
            guild_data.sessions.off.remove(datestr)

        await message.channel.send(f"Session scheduled to {datestr} :tada:")

    async def _handle_cancel(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Cancel a session."""
        date = self._session_service.parse_date(fields[2])
        datestr = self._session_service.format_date(date)

        if datestr in guild_data.sessions.on:
            guild_data.sessions.on.remove(datestr)
            await message.channel.send("Extra session cancelled.")
        elif date.weekday() == guild_data.sessions.wday:
            if datestr not in guild_data.sessions.off:
                guild_data.sessions.off.append(datestr)
                await message.channel.send("Sunday session cancelled.")
            else:
                await message.channel.send("This Sunday session was already cancelled.")
        else:
            await message.channel.send("Could not find an extra session scheduled for that date.")

    async def _handle_available(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Mark user as available for a session."""
        date = self._session_service.parse_date(fields[2])
        datestr = self._session_service.format_date(date)

        if not self._session_service.is_session_day(date, guild_data):
            await message.channel.send("I do not recall a session scheduled for that day.")
            return

        if datestr in user.unavailability:
            user.unavailability.remove(datestr)
            await message.channel.send("Glad to see you can make it!")
        else:
            await message.channel.send("Didn't know you couldn't make it, but I'm glad to see you can make it!")

    async def _handle_unavailable(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Mark user as unavailable for a session."""
        date = self._session_service.parse_date(fields[2])
        datestr = self._session_service.format_date(date)

        if not self._session_service.is_session_day(date, guild_data):
            await message.channel.send("I do not recall a session scheduled for that day.")
            return

        if datestr not in user.unavailability:
            user.unavailability.append(datestr)
            await message.channel.send("If we play, we'll try not to kill your character.")
        else:
            await message.channel.send("We know :(")

    async def _handle_list(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """List upcoming sessions."""
        await message.channel.send("Next four scheduled sessions:")
        sessions = self._session_service.get_upcoming_sessions(guild_data)
        for datestr, missing in sessions:
            await message.channel.send(f"**{datestr}** - Missing players: {missing}")

    async def _handle_next(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Show next scheduled session."""
        await message.channel.send("Next scheduled session:")
        result = self._session_service.get_next_session(guild_data)
        if result:
            datestr, missing = result
            await message.channel.send(f"**{datestr}** - Missing players: {missing}")
