"""Roll command handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import d20

from bot.services.roll import RollService, RollModifiers
from models import Character, GuildData, User

if TYPE_CHECKING:
    import discord
    from discord import Message


class RollHandler:
    """Handler for dice roll commands (!r, !roll)."""

    def __init__(self, roll_service: RollService) -> None:
        self._roll_service = roll_service

    async def handle(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle dice roll commands."""
        fields = self._prepare_fields(fields, user)
        character = self._get_character(fields, user)

        modifiers = self._roll_service.parse_modifiers(fields[3:], character)
        roll_expr = await self._resolve_roll_expression(fields, character, modifiers)
        roll = d20.roll(roll_expr)

        summary = self._roll_service.generate_summary(fields[1], fields[2], modifiers, character.macros)
        await message.channel.send(f"{summary}:\n{str(roll)}")

    def _prepare_fields(self, fields: list[str], user: User) -> list[str]:
        """Prepare fields with character name if not specified."""
        if fields[1] not in user.characters:
            if user.active in user.characters:
                fields = fields[:1] + [user.active] + fields[1:]
            else:
                fields = fields[:1] + ["You"] + fields[1:]
        return fields

    def _get_character(self, fields: list[str], user: User) -> Character:
        """Get the character for the roll."""
        character = user.characters.get(fields[1])
        if character is None:
            if user.active in user.characters:
                fields = fields[:1] + [user.active] + fields[1:]
                character = user.characters.get(fields[1])
        return character or Character.empty()

    async def _resolve_roll_expression(self, fields: list[str], character: Character, modifiers: RollModifiers) -> str:
        """Resolve the roll expression, handling direct dice rolls vs character rolls."""
        try:
            return await self._roll_service.resolve_references(character, fields[2])
        except d20.RollError:
            return await self._roll_service.get_character_roll(character, fields[2], modifiers)
