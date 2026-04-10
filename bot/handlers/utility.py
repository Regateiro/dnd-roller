"""Utility command handlers (distance, fall, etc.)."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from bot.commands import (
    HELP_ALIASES,
    MACRO_COMMAND_ALIASES,
    VARIABLE_COMMAND_ALIASES,
    resolve_command_alias,
)
from bot.models import GuildData, User
from bot.utils import strings

if TYPE_CHECKING:
    from discord import Message


logger = logging.getLogger(__name__)


class UtilityHandler:
    """Handler for utility commands (distance, fall, help, macro, variable)."""

    async def handle_distance(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle distance calculation commands.

        Calculates the third side of a right triangle given two sides.

        Args:
            message: The Discord message that triggered the command.
            guild_data: The guild data for the server.
            user: The user who sent the command.
            fields: The command fields (should contain x, y, d values).
        """
        if len(fields) != 4:
            await message.channel.send("Received wrong number of arguments, please check the help command for instructions.")
            return

        try:
            x = int(fields[1])
            y = int(fields[2])
            d = int(fields[3])
        except ValueError:
            await message.channel.send("Invalid number format. Please use integers for distance values.")
            return

        if x and y and d:
            await message.channel.send("So you already know all three sides? Why are you asking me then? Kids these days...")
        elif x and y:
            distance = math.ceil(math.sqrt(x**2 + y**2) / 5) * 5
            await message.channel.send(f"Moving `{x}ft` on the ground and `{y}ft` vertically costs `{distance}ft` of total movement.")
        elif x and d:
            y_calc = math.floor(math.sqrt(d**2 - x**2) / 5) * 5
            await message.channel.send(f"Moving `{d}ft` diagonally and `{x}ft` on the ground allows you to move `{y_calc}ft` vertically.")
        elif y and d:
            x_calc = math.floor(math.sqrt(d**2 - y**2) / 5) * 5
            await message.channel.send(f"Moving `{d}ft` diagonally and `{y}ft` vertically allows you to move `{x_calc}ft` on the ground.")
        else:
            await message.channel.send("I need to know the length of two sides to calculate the third, I'm not a wizard...")

    async def handle_fall(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle fall damage commands.

        Calculates fall time and rounds based on height.

        Args:
            message: The Discord message that triggered the command.
            guild_data: The guild data for the server.
            user: The user who sent the command.
            fields: The command fields (should contain the height).
        """
        if len(fields) != 2:
            await message.channel.send("Received wrong number of arguments, please check the help command for instructions.")
            return

        try:
            height = int(fields[1])
        except ValueError:
            await message.channel.send("Invalid number format. Please use an integer for height.")
            return

        if height < 500:
            time_fall = round(math.sqrt(height * 36 / 500.0), 2)
        else:
            time_fall = round(height * 6 / 500.0, 2)
        rounds = round(time_fall / 6, 2)
        await message.channel.send(f"Falling from `{height}ft` high will take `{time_fall}s` to hit the ground, or `{rounds}` rounds.")

    async def handle_help(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle help commands.

        Args:
            message: The Discord message that triggered the command.
            guild_data: The guild data for the server.
            user: The user who sent the command.
            fields: The command fields.
        """
        await message.channel.send(strings.HELP_MSG_1)
        await message.channel.send(strings.HELP_MSG_2)
        await message.channel.send(strings.SESSION_HELP)

    async def handle_macro(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle macro commands.

        Args:
            message: The Discord message that triggered the command.
            guild_data: The guild data for the server.
            user: The user who sent the command.
            fields: The command fields.
        """
        if len(fields) == 1 or fields[1] in HELP_ALIASES:
            await message.channel.send(strings.VARS_HELP)
            return

        fields = self._prepare_fields(fields, user)

        command = resolve_command_alias(MACRO_COMMAND_ALIASES, fields[1])
        if command is None:
            return

        try:
            handlers = {
                "set": lambda: self._set_macro(user, fields),
                "delete": lambda: self._delete_macro(user, fields),
                "list": lambda: self._get_macros(user, fields),
            }

            handler = handlers.get(command)
            if handler:
                await message.channel.send(handler())
        except IndexError:
            await message.channel.send("Missing required arguments. Use !help for correct format.")
        except Exception as ex:
            logger.exception("Error in macro handler: %s", ex)
            await message.channel.send("An error occurred while managing macros.")

    async def handle_variable(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle variable commands.

        Args:
            message: The Discord message that triggered the command.
            guild_data: The guild data for the server.
            user: The user who sent the command.
            fields: The command fields.
        """
        if len(fields) == 1 or fields[1] in HELP_ALIASES:
            await message.channel.send(strings.VARS_HELP)
            return

        fields = self._prepare_fields(fields, user)

        command = resolve_command_alias(VARIABLE_COMMAND_ALIASES, fields[1])
        if command is None:
            return

        try:
            handlers = {
                "set": lambda: self._set_variable(user, fields),
                "delete": lambda: self._delete_variable(user, fields),
                "list": lambda: self._get_variables(user, fields),
            }

            handler = handlers.get(command)
            if handler:
                await message.channel.send(handler())
        except IndexError:
            await message.channel.send("Missing required arguments. Use !help for correct format.")
        except Exception as ex:
            logger.exception("Error in variable handler: %s", ex)
            await message.channel.send("An error occurred while managing variables.")

    def _prepare_fields(self, fields: list[str], user: User) -> list[str]:
        """Prepare fields with character name if not specified.

        Args:
            fields: The command fields.
            user: The user who sent the command.

        Returns:
            The fields with character name filled in if needed.
        """
        if len(fields) == 2:
            fields.append(user.active)

        if fields[2] not in user.characters:
            fields = fields[:2] + [user.active] + fields[2:]

        return fields

    def _set_macro(self, user: User, fields: list[str]) -> str:
        """Set a macro for a character.

        Args:
            user: The user setting the macro.
            fields: The command fields containing macro name and value.

        Returns:
            A message indicating success or failure.
        """
        character = user.characters[fields[2]]
        character.macros[fields[3]] = fields[4]
        return f"Added macro {fields[3]} to {fields[2].capitalize()}."

    def _delete_macro(self, user: User, fields: list[str]) -> str:
        """Delete a macro from a character.

        Args:
            user: The user deleting the macro.
            fields: The command fields containing macro name.

        Returns:
            A message indicating success or that the macro doesn't exist.
        """
        character = user.characters[fields[2]]
        if character.macros.pop(fields[3], None):
            return f"Removed macro {fields[3]} from {fields[2].capitalize()}."
        return f"No such macro exists on {fields[2].capitalize()}."

    def _get_macros(self, user: User, fields: list[str]) -> str:
        """Get all macros for a character.

        Args:
            user: The user requesting macros.
            fields: The command fields.

        Returns:
            A formatted string listing all macros.
        """
        character = user.characters[fields[2]]
        macros = [f"{m}[{character.macros[m]}]" for m in character.macros.keys()]
        return f"{fields[2].capitalize()} has the following macros: {macros}."

    def _set_variable(self, user: User, fields: list[str]) -> str:
        """Set a variable for a character.

        Args:
            user: The user setting the variable.
            fields: The command fields containing variable name and value.

        Returns:
            A message indicating success.
        """
        character = user.characters[fields[2]]
        character.variables[fields[3]] = fields[4]
        return f"Added variable {fields[3]} to {fields[2].capitalize()}."

    def _delete_variable(self, user: User, fields: list[str]) -> str:
        """Delete a variable from a character.

        Args:
            user: The user deleting the variable.
            fields: The command fields containing variable name.

        Returns:
            A message indicating success or that the variable doesn't exist.
        """
        character = user.characters[fields[2]]
        if character.variables.pop(fields[3], None):
            return f"Removed variable {fields[3]} from {fields[2].capitalize()}."
        return f"No such variable exists on {fields[2].capitalize()}."

    def _get_variables(self, user: User, fields: list[str]) -> str:
        """Get all variables for a character.

        Args:
            user: The user requesting variables.
            fields: The command fields.

        Returns:
            A formatted string listing all variables.
        """
        character = user.characters[fields[2]]
        variables = [f"{v}[{character.variables[v]}]" for v in character.variables.keys()]
        return f"{fields[2].capitalize()} has the following variables: {variables}."
