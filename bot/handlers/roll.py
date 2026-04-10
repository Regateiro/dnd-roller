"""Roll command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import d20

from bot.exceptions import DNDRollerError, InvalidRollExpressionError, InvalidStatError
from bot.models import Character, GuildData, User
from bot.services.roll import RollModifiers, RollService

if TYPE_CHECKING:
    from discord import Message


logger = logging.getLogger(__name__)


class RollHandler:
    """Handler for dice roll commands (!r, !roll)."""

    def __init__(self, roll_service: RollService) -> None:
        """Initialize the roll handler.

        Args:
            roll_service: The roll service for resolving dice rolls.
        """
        self._roll_service = roll_service

    async def handle(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle dice roll commands.

        Args:
            message: The Discord message that triggered the command.
            guild_data: The guild data for the server.
            user: The user who sent the command.
            fields: The command fields parsed from the message.
        """
        try:
            fields = self._prepare_fields(fields, user)
            character = self._get_character(fields, user)
            modifiers = self._roll_service.parse_modifiers(fields[3:], character)
            roll_expr = await self._resolve_roll_expression(fields, character, modifiers)
            roll = d20.roll(roll_expr)
            summary = self._roll_service.generate_summary(fields[1], fields[2], modifiers, character.macros)

            await message.channel.send(f"{summary}:\n{str(roll)}")
        except InvalidStatError as ex:
            await message.channel.send(f"Invalid target: {ex.stat}. Use a valid stat or skill name.")
        except InvalidRollExpressionError as ex:
            await message.channel.send(f"Invalid roll expression: {ex.expression}")
        except d20.RollSyntaxError as ex:
            await message.channel.send(f"Invalid dice notation: {ex}")
        except DNDRollerError as ex:
            logger.exception("D&D Roller error in roll handler: %s", ex)
            await message.channel.send(f"Error: {ex}")
        except Exception as ex:
            logger.exception("Unexpected error in roll handler: %s", ex)
            await message.channel.send("An unexpected error occurred while rolling. Please try again.")

    def _prepare_fields(self, fields: list[str], user: User) -> list[str]:
        """Prepare fields with character name if not specified.

        Args:
            fields: The command fields.
            user: The user who sent the command.

        Returns:
            The fields with character name filled in if needed.
        """
        if fields[1] not in user.characters:
            if user.active in user.characters:
                fields = fields[:1] + [user.active] + fields[1:]
            else:
                fields = fields[:1] + ["You"] + fields[1:]
        return fields

    def _get_character(self, fields: list[str], user: User) -> Character:
        """Get the character for the roll.

        Args:
            fields: The command fields.
            user: The user who sent the command.

        Returns:
            The Character object, or an empty character if none found.
        """
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
        """Resolve the roll expression, handling direct dice rolls vs character rolls.

        Args:
            fields: The command fields.
            character: The character performing the roll.
            modifiers: The roll modifiers.

        Returns:
            The resolved roll expression string.
        """
        try:
            # First try to resolve as a direct dice expression (e.g., "2d6+3")
            formula = await self._roll_service.resolve_references(character, fields[2])
            d20.roll(formula)  # Validate the formula
            return formula
        except d20.RollSyntaxError:
            # If it's not valid dice notation, treat it as a character roll target
            return await self._roll_service.get_character_roll(character, formula, modifiers)
