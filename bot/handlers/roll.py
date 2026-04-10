"""Roll command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import d20

from bot.services.roll import RollService, RollModifiers
from bot.models import Character, GuildData, User

if TYPE_CHECKING:
    import discord
    from discord import Message


logger = logging.getLogger(__name__)


class RollHandler:
    """Handler for dice roll commands (!r, !roll)."""

    def __init__(self, roll_service: RollService) -> None:
        self._roll_service = roll_service

    async def handle(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle dice roll commands."""
        logger.debug(f"handle called: fields=%s, user.active='%s', user.characters=%s", fields, user.active, list(user.characters.keys()))

        try:
            fields = self._prepare_fields(fields, user)
            logger.debug("after _prepare_fields: fields=%s", fields)

            character = self._get_character(fields, user)
            logger.debug("got character: %s", character)

            modifiers = self._roll_service.parse_modifiers(fields[3:], character)
            logger.debug("modifiers: %s", modifiers)

            roll_expr = await self._resolve_roll_expression(fields, character, modifiers)
            logger.debug("resolved roll_expr: %s", roll_expr)

            roll = d20.roll(roll_expr)
            logger.debug("roll result: %s", roll)

            summary = self._roll_service.generate_summary(fields[1], fields[2], modifiers, character.macros)
            logger.debug("summary: %s", summary)

            await message.channel.send(f"{summary}:\n{str(roll)}")
        except Exception as ex:
            logger.exception("Error in roll handler: %s", ex)
            await message.channel.send(f"Error rolling: {ex}")

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

    async def _resolve_roll_expression(
        self,
        fields: list[str],
        character: Character,
        modifiers: RollModifiers,
    ) -> str:
        """Resolve the roll expression, handling direct dice rolls vs character rolls."""
        try:
            return await self._roll_service.resolve_references(character, fields[2])
        except d20.RollError:
            return await self._roll_service.get_character_roll(character, fields[2], modifiers)
