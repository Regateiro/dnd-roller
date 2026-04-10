"""Character management command handler."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from str2bool import str2bool

from bot.commands import (
    CHARACTER_COMMAND_ALIASES,
    CHARACTER_UPDATE_ALIASES,
    HELP_ALIASES,
    resolve_command_alias,
)
from bot.exceptions import (
    InvalidCharacterDataError,
    InvalidSkillError,
)
from bot.models import (
    SKILL_TO_STAT,
    SKILLS,
    STAT_FULL_NAMES,
    Character,
    GuildData,
    Stat,
    User,
)
from bot.utils import strings

if TYPE_CHECKING:
    from discord import Message


logger = logging.getLogger(__name__)


class CharacterHandler:
    """Handler for character management commands (!character, !char, !c)."""

    def __init__(self) -> None:
        """Initialize the character handler."""
        self.stats: list[str] = Stat.all()
        self.skills: list[str] = SKILLS
        self._stat_short_map = {
            **{s: s for s in self.stats},
            "intelligence": "int",
            "charisma": "cha",
            "dexterity": "dex",
            "strength": "str",
            "constitution": "con",
            "wisdom": "wis",
        }

    async def handle(self, message: Message, guild_data: GuildData, user: User, fields: list[str]) -> None:
        """Handle character management commands.

        Args:
            message: The Discord message that triggered the command.
            guild_data: The guild data for the server.
            user: The user who sent the command.
            fields: The command fields parsed from the message.
        """
        try:
            await self._handle_internal(message, user, fields)
        except InvalidSkillError as ex:
            await message.channel.send(f"Invalid skill: {ex.skill}. Use a valid skill name.")
        except InvalidCharacterDataError as ex:
            await message.channel.send(str(ex))
        except ValueError as ex:
            logger.exception("Value error in character handler: %s", ex)
            await message.channel.send(f"Invalid input: {ex}. Use !help for correct format.")
        except Exception as ex:
            logger.exception("Unexpected error in character handler: %s", ex)
            await message.channel.send("An unexpected error occurred. Please try again.")

    async def _handle_internal(self, message: Message, user: User, fields: list[str]) -> None:
        """Internal handler that throws specific exceptions."""
        if len(fields) == 1 or fields[1] in HELP_ALIASES:
            await message.channel.send(strings.CHAR_HELP)
            return

        command = resolve_command_alias(CHARACTER_COMMAND_ALIASES, fields[1])
        if command is None:
            return

        handlers = {
            "create": self._create_character,
            "delete": self._delete_character,
            "update": self._update_character,
            "active": self._set_active_character,
            "info": self._get_character_info,
            "list": self._list_characters,
        }

        handler = handlers.get(command)
        if handler:
            response = await handler(user, fields)
            await message.channel.send(response)

    async def _create_character(self, user: User, fields: list[str]) -> str:
        """Create a new character.

        Args:
            user: The user creating the character.
            fields: The command fields containing character data.

        Returns:
            A message indicating success or failure.

        Raises:
            InvalidCharacterDataError: If the character data is invalid.
            ValueError: If required fields are missing or malformed.
        """
        if len(fields) < 10:
            raise InvalidCharacterDataError("Missing required fields for character creation. Use !help for format.")

        if fields[2] in user.characters:
            raise InvalidCharacterDataError(f"Character '{fields[2]}' already exists.")

        try:
            name = fields[2]
            character = Character(
                level=int(fields[3]),
                stats={
                    Stat.STRENGTH: int(fields[4]),
                    Stat.DEXTERITY: int(fields[5]),
                    Stat.CONSTITUTION: int(fields[6]),
                    Stat.INTELLIGENCE: int(fields[7]),
                    Stat.WISDOM: int(fields[8]),
                    Stat.CHARISMA: int(fields[9]),
                },
            )

            assert fields[10] == "|"
            idx = 11

            idx = self._parse_proficiency_list(fields, idx, self.stats, Stat, character.save_prof.append)
            idx = self._parse_proficiency_list(fields, idx, self.skills, lambda x: x, character.skill_prof.append)
            self._parse_proficiency_list(fields, idx, self.skills, lambda x: x, character.skill_expertise.append)

            user.characters[name] = character
            user.active = name
            return f"Character {name} created and set as default."
        except (ValueError, AssertionError) as e:
            raise InvalidCharacterDataError(f"Invalid character data: {e}. Use !help for correct format.") from e

    def _parse_proficiency_list(
        self,
        fields: list[str],
        idx: int,
        valid_items: list[str],
        transform: Callable[..., str],
        append_fn: Callable[[str], None],
    ) -> int:
        """Parse a list of proficiency items until the next delimiter.

        Args:
            fields: The command fields.
            idx: Current index in fields.
            valid_items: List of valid item names.
            transform: Function to transform valid item names.
            append_fn: Function to append parsed items.

        Returns:
            The updated index after parsing.

        Raises:
            InvalidSkillError: If an invalid skill is encountered.
        """
        while fields[idx] != "|":
            item = fields[idx]
            if item in valid_items:
                append_fn(transform(item))
            else:
                raise InvalidSkillError(item)
            idx += 1
        return idx + 1

    async def _delete_character(self, user: User, fields: list[str]) -> str:
        """Delete a character.

        Args:
            user: The user deleting the character.
            fields: The command fields.

        Returns:
            A message indicating success or that the character doesn't exist.
        """
        if user.characters.pop(fields[2], None):
            return f"Removed character {fields[2].capitalize()}. You may need to set a new active character."
        return "No such character exists for you."

    async def _update_character(self, user: User, fields: list[str]) -> str:
        """Update various aspects of a character.

        Args:
            user: The user updating the character.
            fields: The command fields.

        Returns:
            A message indicating success or the error.
        """
        if fields[2] not in user.characters:
            return "No such character exists for you."

        character = user.characters[fields[2]]
        idx = 4

        command = resolve_command_alias(CHARACTER_UPDATE_ALIASES, fields[3])
        if command is None:
            return f"Unknown update type: {fields[3]}"

        update_handlers = {
            "main": (self._update_main, idx),
            "saves": (self._update_saves, idx),
            "bonus": (self._update_bonus, idx),
            "skills": (self._update_skill_list, idx, "skill_prof"),
            "expertise": (self._update_skill_list, idx, "skill_expertise"),
            "half": (self._update_skill_list, idx, "skill_half"),
            "advantage": (self._update_advantage, idx),
        }

        handler_info = update_handlers.get(command)
        if handler_info is None:
            return f"Unknown update type: {fields[3]}"

        handler = handler_info[0]
        return await handler(character, fields, *handler_info[1:])

    async def _update_main(self, character: Character, fields: list[str], idx: int) -> str:
        """Update main character stats.

        Args:
            character: The character to update.
            fields: The command fields.
            idx: The starting index for the new values.

        Returns:
            A message indicating success.
        """
        character.level = int(fields[idx])
        character.stats = {
            Stat.STRENGTH: int(fields[idx + 1]),
            Stat.DEXTERITY: int(fields[idx + 2]),
            Stat.CONSTITUTION: int(fields[idx + 3]),
            Stat.INTELLIGENCE: int(fields[idx + 4]),
            Stat.WISDOM: int(fields[idx + 5]),
            Stat.CHARISMA: int(fields[idx + 6]),
        }
        return "Character main stats updated."

    async def _update_saves(self, character: Character, fields: list[str], idx: int) -> str:
        """Update saving throw proficiencies.

        Args:
            character: The character to update.
            fields: The command fields.
            idx: The starting index for the proficiency list.

        Returns:
            A message indicating success or error.
        """
        return await self._update_proficiency_list(
            character.save_prof,
            fields,
            idx,
            self.stats,
            Stat,
            "stat",
        )

    async def _update_skill_list(self, character: Character, fields: list[str], idx: int, attr: str) -> str:
        """Update a skill proficiency list.

        Args:
            character: The character to update.
            fields: The command fields.
            idx: The starting index for the proficiency list.
            attr: The attribute name to update (skill_prof, skill_expertise, etc.).

        Returns:
            A message indicating success or error.
        """
        prof_list = getattr(character, attr)
        return await self._update_proficiency_list(
            prof_list,
            fields,
            idx,
            self.skills,
            str,
            "skill",
        )

    async def _update_proficiency_list(
        self,
        prof_list: list[str],
        fields: list[str],
        idx: int,
        valid_items: list[str],
        transform: Callable[..., str],
        item_type: str,
    ) -> str:
        """Generic method to update a proficiency list.

        Args:
            prof_list: The proficiency list to update.
            fields: The command fields.
            idx: The starting index.
            valid_items: List of valid item names.
            transform: Function to transform valid item names.
            item_type: The type of item ("stat" or "skill").

        Returns:
            A message indicating success or error.
        """
        prof_list.clear()
        while idx < len(fields):
            item = fields[idx]
            if item in valid_items:
                prof_list.append(transform(item))
            else:
                return f"Error: unknown {item_type} {item}."
            idx += 1
        return f"Character {item_type}s updated."

    async def _update_bonus(self, character: Character, fields: list[str], idx: int) -> str:
        """Update ability and skill bonuses.

        Args:
            character: The character to update.
            fields: The command fields.
            idx: The starting index for the bonus values.

        Returns:
            A message indicating success or error.
        """
        if len(fields) == 6:
            character.ability_bonus = int(fields[idx])
            character.skill_bonus = int(fields[idx + 1])
        elif len(fields) == 7:
            character.ability_bonus = int(fields[idx])
            character.skill_bonus = int(fields[idx + 1])
            character.jack_of_all_trades = str2bool(fields[idx + 2])
        else:
            return "Error: Wrong number of arguments. Expected general save and check bonus."
        return "Character bonuses updated."

    async def _update_advantage(self, character: Character, fields: list[str], idx: int) -> str:
        """Update advantage conditions.

        Args:
            character: The character to update.
            fields: The command fields.
            idx: The starting index for the advantage list.

        Returns:
            A message indicating success or error.
        """
        character.advantage.clear()
        while idx < len(fields):
            target = self._stat_short_map.get(fields[idx], fields[idx])
            if target in (self.skills + self.stats):
                character.advantage.append(target)
            else:
                return f"Error: unknown ability/skill {fields[idx]}."
            idx += 1
        return "Character advantage updated."

    async def _set_active_character(self, user: User, fields: list[str]) -> str:
        """Set or display active character.

        Args:
            user: The user setting the active character.
            fields: The command fields.

        Returns:
            A message indicating success or the current active character.
        """
        if len(fields) == 2:
            return f"You current active character is {user.active.capitalize()}."
        if fields[2] in user.characters:
            user.active = fields[2]
            return f"{fields[2].capitalize()} set as the active character."
        return "No such character exists for you."

    async def _get_character_info(self, user: User, fields: list[str]) -> str:
        """Get formatted character information.

        Args:
            user: The user requesting character info.
            fields: The command fields.

        Returns:
            A formatted string with character information.
        """
        name = fields[2] if len(fields) > 2 and fields[2] in user.characters else user.active
        character = user.characters[name]
        prof_mod = character.get_prof_mod()

        lines = [
            "```",
            f"Name: {name.capitalize()}",
            f"Level: {character.level}",
            f"Proficiency: {prof_mod}",
            f"Ability Check Bonus: {character.ability_bonus}",
            f"Skill Check Bonus: {character.skill_bonus}",
            f"Jack of All Trades: {character.jack_of_all_trades}",
            "",
        ]

        for stat in self.stats:
            fullstat = STAT_FULL_NAMES.get(Stat(stat), stat)
            stat_enum = Stat(stat)
            score = character.stats[stat_enum]
            mod = character.get_stat_mod(stat_enum) + character.ability_bonus
            if stat_enum in character.save_prof:
                lines.append(f"{fullstat.capitalize():15}: {score:2} ({mod}/{mod + prof_mod}) ✓")
            else:
                lines.append(f"{fullstat.capitalize():15}: {score:2} ({mod}/{mod})")

        lines.append("")

        for skill in self.skills:
            stat = SKILL_TO_STAT.get(skill, Stat.WISDOM).value
            pretty_skill = " ".join(skill.split("_")).title()
            mod, prof_indicator = character.get_skill_mod(skill)
            mod += character.skill_bonus
            adv_mod = 5 if skill in character.advantage else 0
            lines.append(f"{pretty_skill:15}: {mod:2} ({stat}/{10 + mod + adv_mod}) {prof_indicator.value}")

        lines.append("```")
        return "\n".join(lines)

    async def _list_characters(self, user: User, fields: list[str]) -> str:
        """List all user characters.

        Args:
            user: The user listing their characters.
            fields: The command fields.

        Returns:
            A message listing all characters.
        """
        characters = [c.capitalize() for c in user.characters.keys()]
        return f"Your characters are: {characters}."
