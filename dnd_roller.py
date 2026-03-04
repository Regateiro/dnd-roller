"""Main DnD Roller Bot App"""

import calendar
import configparser
import json
import logging
import math
import os
import re
from datetime import datetime, timedelta

import d20
import discord
from dateutil.parser import parse
from discord import Message
from str2bool import str2bool

from models import (
    SKILL_TO_STAT,
    SKILLS,
    STAT_FULL_NAMES,
    STAT_SHORT_NAMES,
    Cache,
    Character,
    GuildData,
    Stat,
    User,
)
from utils import strings

logging.basicConfig(filename="/var/log/dnd-roller.log", encoding="utf-8", level=logging.DEBUG, format="%(asctime)s : %(message)s")

config = configparser.ConfigParser()
config.read(f"{os.getenv('HOME')}/.config/dnd-roller/config.ini")


class DNDRoller(discord.Client):
    """Discord Client for D&D dice rolling and character management.

    This class extends discord.Client to provide a bot that can handle
    dice rolls, character management, session scheduling, and various
    D&D-related commands in Discord servers.
    """

    def __init__(self, app_intents) -> None:
        """Initialize the D&D Roller bot.

        Args:
            app_intents: Discord intents required for the bot's functionality.
        """
        super().__init__(intents=app_intents)

        try:
            with open(f"{config['General']['Storage']}/cache.json", "rt", encoding="utf-8") as fd:
                self.cache = Cache.from_dict(json.load(fd))
        except FileNotFoundError:
            self.cache = Cache()

        self.stats: list[str] = Stat.all()
        self.skills: list[str] = SKILLS

    async def on_ready(self) -> None:
        """Called when the bot has successfully connected to Discord.

        Logs a message indicating the bot is ready and logged in.
        """
        logging.info("Logged on as {0}!".format(self.user))

    async def on_message(self, message: Message) -> None:
        """Handle incoming Discord messages and process bot commands.

        Processes messages that start with '!' and handles various D&D-related
        commands including dice rolls, character management, session scheduling,
        and utility functions.

        Args:
            message: The Discord message object containing the command.
        """
        if not message.content.startswith("!"):
            return

        try:
            if message.guild:
                guild = str(message.guild.id)
            else:
                guild = "None"

            author: str = f"{str(message.author.id)}"
            guild_data = self.cache.get_or_create_guild(guild)
            user = self.cache.get_or_create_user(guild, author, str(message.author.display_name))

            fields = message.content.lower().split(" ")
            command = fields[0]

            handlers = {
                "!r": self._handle_roll,
                "!roll": self._handle_roll,
                "!character": self._handle_character,
                "!char": self._handle_character,
                "!c": self._handle_character,
                "!m": self._handle_macro,
                "!macro": self._handle_macro,
                "!v": self._handle_variable,
                "!var": self._handle_variable,
                "!variable": self._handle_variable,
                "!session": self._handle_session,
                "!s": self._handle_session,
                "!distance": self._handle_distance,
                "!d": self._handle_distance,
                "!fall": self._handle_fall,
                "!f": self._handle_fall,
                "!h": self._handle_help,
                "!help": self._handle_help,
            }

            handler = handlers.get(command)
            if handler:
                await handler(message, guild_data, user, fields)
        except Exception as ex:
            logging.exception(ex)
        finally:
            with open(f"{config['General']['Storage']}/cache.json", "wt", encoding="utf-8") as fd:
                json.dump(self.cache.to_dict(), fd)

    async def _handle_roll(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle dice roll commands (!r, !roll).

        Parses roll expressions and applies character stats, proficiencies,
        and modifiers (advantage, disadvantage, etc.).
        """
        if fields[1] not in user.characters:
            if user.active in user.characters:
                fields = fields[:1] + [user.active] + fields[1:]
            else:
                fields = fields[:1] + ["You"] + fields[1:]

        character = user.characters.get(fields[1])
        if character is None:
            if user.active in user.characters:
                fields = fields[:1] + [user.active] + fields[1:]
                character = user.characters.get(fields[1])
            if character is None:
                character = Character.empty()

        modifiers = {
            "mode": "n",
            "save": False,
            "crit": False,
            "vars": [],
        }

        try:
            roll = d20.roll(await self._resolve_references(character, fields[2]))
        except d20.RollError:
            for field in fields[3:]:
                if field == "save":
                    modifiers["save"] = True
                elif field in ["crit", "critical"]:
                    modifiers["crit"] = True
                elif field in ["a", "adv", "advantage"]:
                    modifiers["mode"] = "a"
                elif field in ["ta", "tadv", "tadvantage"]:
                    modifiers["mode"] = "ta"
                elif field in ["d", "dis", "disadvantage"]:
                    modifiers["mode"] = "d"
                elif field in character.variables.keys():
                    modifiers["vars"].append(field)

            roll = d20.roll(await self._get_character_roll(character, fields[2], modifiers))

        summary: str = f"{await self._generate_roll_summary(fields[1], fields[2], modifiers, character.macros)}:\n"
        await message.channel.send(f"{summary}{str(roll)}")

    async def _handle_character(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle character management commands (!character, !char, !c).

        Supports creating, deleting, updating, listing characters,
        and setting the active character.
        """
        if len(fields) == 1 or fields[1] == "help" or fields[1] == "h":
            await message.channel.send(strings.CHAR_HELP)

        elif fields[1] == "create" or fields[1] == "c":
            await message.channel.send(await self._create_character(user, fields))

        elif fields[1] == "delete" or fields[1] == "d":
            await message.channel.send(await self._delete_character(user, fields))

        elif fields[1] == "update" or fields[1] == "u":
            await message.channel.send(await self._update_character(user, fields))

        elif fields[1] == "active" or fields[1] == "a":
            if len(fields) == 2:
                await message.channel.send(f"You current active character is {user.active.capitalize()}.")
            elif fields[2] in user.characters:
                user.active = fields[2]
                await message.channel.send(f"{fields[2].capitalize()} set as the active character.")
            else:
                await message.channel.send("No such character exists for you.")

        elif fields[1] in ("info", "show", "i", "s"):
            await message.channel.send(await self._get_character(user, fields))

        elif fields[1] == "list" or fields[1] == "l":
            characters = [c.capitalize() for c in user.characters.keys()]
            await message.channel.send(f"Your characters are: {characters}.")

    async def _handle_macro(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle macro commands (!m, !macro).

        Macros are saved dice roll expressions that can be reused
        (e.g., !macro set fireball 8d6).
        """
        if len(fields) == 1 or fields[1] == "help" or fields[1] == "h":
            await message.channel.send(strings.VARS_HELP)

        if len(fields) == 2:
            fields.append(user.active)

        if fields[2] not in user.characters:
            fields = fields[:2] + [user.active] + fields[2:]

        if fields[1] == "set" or fields[1] == "s":
            await message.channel.send(await self._set_macro(user, fields))

        elif fields[1] == "delete" or fields[1] == "d":
            await message.channel.send(await self._delete_macro(user, fields))

        elif fields[1] == "list" or fields[1] == "l":
            await message.channel.send(await self._get_macros(user, fields))

    async def _handle_variable(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle variable commands (!v, !var, !variable).

        Variables are numeric values that can be referenced in macros
        using $variable_name syntax.
        """
        if len(fields) == 1 or fields[1] == "help" or fields[1] == "h":
            await message.channel.send(strings.VARS_HELP)

        if len(fields) == 2:
            fields.append(user.active)

        if fields[2] not in user.characters:
            fields = fields[:2] + [user.active] + fields[2:]

        if fields[1] == "set" or fields[1] == "s":
            await message.channel.send(await self._set_variable(user, fields))

        elif fields[1] == "delete" or fields[1] == "h":
            await message.channel.send(await self._delete_variable(user, fields))

        elif fields[1] == "list" or fields[1] == "l":
            await message.channel.send(await self._get_variables(user, fields))

    async def _handle_session(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle session management commands (!session, !s).

        Supports scheduling sessions, cancelling, marking availability,
        and listing upcoming sessions.
        """
        await self._clean_sessions(guild_data, user)

        if len(fields) == 1 or fields[1] == "help" or fields[1] == "h":
            await message.channel.send(strings.SESSION_HELP)

        elif fields[1] == "weekday" or fields[1] == "w":
            day: int = [x.lower() for x in list(calendar.day_name)].index(fields[2].lower())
            guild_data.sessions.wday = day
            await message.channel.send(f"Default session weekday set to {calendar.day_name[guild_data.sessions.wday]}.")

        elif fields[1] == "schedule" or fields[1] == "s":
            date: datetime = parse(fields[2])
            if date.date() >= date.now().date():
                datestr: str = date.strftime("%Y-%m-%d")
                if datestr in guild_data.sessions.on or (date.weekday() == guild_data.sessions.wday and datestr not in guild_data.sessions.off):
                    await message.channel.send("We already have a session on that day.")
                else:
                    if date.weekday() != guild_data.sessions.wday:
                        guild_data.sessions.on.append(datestr)

                    if datestr in guild_data.sessions.off:
                        guild_data.sessions.off.remove(datestr)

                    await message.channel.send(f"Session scheduled to {datestr} :tada:")
            else:
                await message.channel.send("I'm also eager, but even I cannot go back in time.")

        elif fields[1] == "cancel" or fields[1] == "c":
            date: datetime = parse(fields[2])
            datestr: str = date.strftime("%Y-%m-%d")
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

        elif fields[1] == "available" or fields[1] == "a":
            date: datetime = parse(fields[2])
            datestr: str = date.strftime("%Y-%m-%d")
            if datestr in guild_data.sessions.on or date.weekday() == guild_data.sessions.wday:
                if datestr in user.unavailability:
                    user.unavailability.remove(datestr)
                    await message.channel.send("Glad to see you can make it!")
                else:
                    await message.channel.send("Didn't know you couldn't make it, but I'm glad to see you can make it!")
            else:
                await message.channel.send("I do not recall a session scheduled for that day.")

        elif fields[1] == "unavailable" or fields[1] == "u":
            date: datetime = parse(fields[2])
            datestr: str = date.strftime("%Y-%m-%d")
            if datestr in guild_data.sessions.on or date.weekday() == guild_data.sessions.wday:
                if datestr not in user.unavailability:
                    user.unavailability.append(datestr)
                    await message.channel.send("If we play, we'll try not to kill your character.")
                else:
                    await message.channel.send("We know :(")
            else:
                await message.channel.send("I do not recall a session scheduled for that day.")

        elif fields[1] == "list" or fields[1] == "l":
            await message.channel.send("Next four scheduled sessions:")

            reported = 0
            date: datetime = datetime.now()
            while reported != 4:
                datestr: str = date.strftime("%Y-%m-%d")
                if (date.weekday() == guild_data.sessions.wday and datestr not in guild_data.sessions.off) or datestr in guild_data.sessions.on:
                    await message.channel.send(
                        f"""**{datestr}** - Missing players: {[
                            guild_data.users[u].name
                            for u in guild_data.users.keys()
                            if datestr in guild_data.users[u].unavailability
                        ]}"""
                    )
                    reported: int = reported + 1
                date += timedelta(days=1)

        elif fields[1] == "next" or fields[1] == "n":
            await message.channel.send("Next scheduled session:")

            reported = False
            date: datetime = datetime.now()
            while not reported:
                datestr: str = date.strftime("%Y-%m-%d")
                if (date.weekday() == guild_data.sessions.wday and datestr not in guild_data.sessions.off) or datestr in guild_data.sessions.on:
                    await message.channel.send(
                        f"""**{datestr}** - Missing players: {[
                            guild_data.users[u].name
                            for u in guild_data.users.keys()
                            if datestr in guild_data.users[u].unavailability
                        ]}"""
                    )
                    reported = True
                date += timedelta(days=1)

    async def _handle_distance(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle distance calculation commands (!distance, !d).

        Calculates movement distance using the Pythagorean theorem
        for diagonal movement in D&D 5e (5ft grid).
        """
        if len(fields) == 4:
            x = int(fields[1])
            y = int(fields[2])
            d = int(fields[3])

            if x and y and d:
                await message.channel.send("So you already know all three sides? Why are you asking me then? Kids these days...")
            elif x and y:
                d: int = math.ceil(math.sqrt(math.pow(x, 2) + math.pow(y, 2)) / 5) * 5
                await message.channel.send(f"Moving `{x}ft` on the ground and `{y}ft` vertically costs `{d}ft` of total movement.")
            elif x and d:
                y: int = math.floor(math.sqrt(math.pow(d, 2) - math.pow(x, 2)) / 5) * 5
                await message.channel.send(f"Moving `{d}ft` diagonally and `{x}ft` on the ground allows you to move `{y}ft` vertically.")
            elif y and d:
                x: int = math.floor(math.sqrt(math.pow(d, 2) - math.pow(y, 2)) / 5) * 5
                await message.channel.send(f"Moving `{d}ft` diagonally and `{y}ft` vertically allows you to move `{x}ft` on the ground.")
            else:
                await message.channel.send("I need to know the length of two sides to calculate the third, I'm not a wizard...")
        else:
            await message.channel.send("Received too few or too many arguments, please check the help command for instructions.")

    async def _handle_fall(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle fall damage commands (!fall, !f).

        Calculates fall damage and time to hit the ground based on height.
        D&D 5e rule: 1d6 damage per 10ft fallen.
        """
        if len(fields) == 2:
            height = int(fields[1])
            if height < 500:
                time: float = round(math.sqrt(height * 36 / 500.0), 2)
            else:
                time: float = round(height * 6 / 500.0, 2)
            rounds: float = round(time / 6, 2)
            await message.channel.send(f"Falling from `{height}ft` high will take `{time}s` to hit the ground, or `{rounds}` rounds.")
        else:
            await message.channel.send("Received too few or too many arguments, please check the help command for instructions.")

    async def _handle_help(self, message: Message, guild_data: GuildData, user: User, fields: list) -> None:
        """Handle help commands (!h, !help).

        Sends information about available commands to the user.
        """
        await message.channel.send(strings.HELP_MSG_1)
        await message.channel.send(strings.HELP_MSG_2)
        await message.channel.send(strings.SESSION_HELP)

    async def _clean_sessions(self, guild_data: GuildData, current_user: User) -> None:
        """Clean up expired sessions and unavailability entries.

        Removes sessions and user unavailability entries that are in the past
        to keep the cache clean and up-to-date.

        Args:
            guild_data: The guild data object.
            current_user: The current user object.
        """
        now: str = datetime.now().strftime("%Y-%m-%d")

        for session in [s for s in guild_data.sessions.on if s < now]:
            guild_data.sessions.on.remove(session)

        for session in [s for s in guild_data.sessions.off if s < now]:
            guild_data.sessions.off.remove(session)

        for user in guild_data.users.values():
            for session in [s for s in user.unavailability if s < now]:
                user.unavailability.remove(session)

    async def _create_character(self, user: User, fields: list) -> str:
        """Create a new character for a user.

        Parses the command fields to create a character with ability scores,
        saving throw proficiencies, skill proficiencies, and expertise.

        Args:
            user: The user object.
            fields: The command fields containing character creation data.

        Returns:
            A success or error message string.
        """
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

            while fields[idx] != "|":
                if fields[idx] in self.stats:
                    character.save_prof.append(Stat(fields[idx]))
                else:
                    return f"Error: unknown stat {fields[idx]}."
                idx: int = idx + 1
            idx: int = idx + 1

            while fields[idx] != "|":
                if fields[idx] in self.skills:
                    character.skill_prof.append(fields[idx])
                else:
                    return f"Error: unknown skill {fields[idx]}."
                idx: int = idx + 1
            idx: int = idx + 1

            while idx < len(fields):
                if fields[idx] in self.skills:
                    character.skill_expertise.append(fields[idx])
                else:
                    return f"Error: unknown skill {fields[idx]}."
                idx: int = idx + 1

            user.characters[name] = character
            user.active = name
            return f"Character {name} created and set as default."
        except Exception:
            return "Could not create the character, use !help for help."

    async def _delete_character(self, user: User, fields: list) -> str:
        """Delete a character from a user's character list.

        Args:
            user: The user object.
            fields: The command fields containing the character name to delete.

        Returns:
            A message indicating success or that the character doesn't exist.
        """
        if user.characters.pop(fields[2], None):
            return f"Removed character {fields[2].capitalize()}. You may need to set a new active character."
        return "No such character exists for you."

    async def _update_character(self, user: User, fields: list) -> str:
        """Update various aspects of a character.

        Can update main stats, saving throw proficiencies, skill proficiencies,
        expertise, bonuses, and advantage conditions.

        Args:
            user: The user object.
            fields: The command fields containing update information.

        Returns:
            A success or error message string.
        """
        if fields[2] in user.characters:
            character = user.characters[fields[2]]
            idx = 4

            if fields[3] == "main":
                character.level = int(fields[4])
                character.stats = {
                    Stat.STRENGTH: int(fields[5]),
                    Stat.DEXTERITY: int(fields[6]),
                    Stat.CONSTITUTION: int(fields[7]),
                    Stat.INTELLIGENCE: int(fields[8]),
                    Stat.WISDOM: int(fields[9]),
                    Stat.CHARISMA: int(fields[10]),
                }

            elif fields[3] == "saves":
                character.save_prof.clear()
                while idx < len(fields):
                    if fields[idx] in self.stats:
                        character.save_prof.append(Stat(fields[idx]))
                    else:
                        return f"Error: unknown stat {fields[idx]}."
                    idx: int = idx + 1

            elif fields[3] == "bonus":
                if len(fields) == 6:
                    character.ability_bonus = int(fields[4])
                    character.skill_bonus = int(fields[5])
                elif len(fields) == 7:
                    character.ability_bonus = int(fields[4])
                    character.skill_bonus = int(fields[5])
                    character.jack_of_all_trades = str2bool(fields[6])
                else:
                    return "Error: Wrong number of arguments. Expected general save and check bonus."

            elif fields[3] == "skills":
                character.skill_prof.clear()
                while idx < len(fields):
                    if fields[idx] in self.skills:
                        character.skill_prof.append(fields[idx])
                    else:
                        return f"Error: unknown skill {fields[idx]}."
                    idx: int = idx + 1

            elif fields[3] == "expertise":
                character.skill_expertise.clear()
                while idx < len(fields):
                    if fields[idx] in self.skills:
                        character.skill_expertise.append(fields[idx])
                    else:
                        return f"Error: unknown skill {fields[idx]}."
                    idx: int = idx + 1

            elif fields[3] == "half":
                character.skill_half.clear()
                while idx < len(fields):
                    if fields[idx] in self.skills:
                        character.skill_half.append(fields[idx])
                    else:
                        return f"Error: unknown skill {fields[idx]}."
                    idx: int = idx + 1

            elif fields[3] == "adv" or fields[3] == "advantage":
                character.advantage.clear()
                while idx < len(fields):
                    target: str = await self._get_stat_shortname(fields[idx])
                    if target in (self.skills + self.stats):
                        character.advantage.append(target)
                    else:
                        return f"Error: unknown ability/skill {fields[idx]}."
                    idx: int = idx + 1

            user.characters[fields[2]] = character
            return f"Character {fields[2]} was updated."
        return "No such character exists for you."

    async def _set_macro(self, user: User, fields: list) -> str:
        """Set a macro for a character.

        Args:
            user: The user object.
            fields: Command fields containing character name, macro name, and dice expression.

        Returns:
            A success message string.
        """
        character = user.characters[fields[2]]
        character.macros[fields[3]] = fields[4]
        return f"Added macro {fields[3]} to {fields[2].capitalize()}."

    async def _delete_macro(self, user: User, fields: list) -> str:
        """Delete a macro from a character.

        Args:
            user: The user object.
            fields: Command fields containing character name and macro name.

        Returns:
            A success or error message string.
        """
        character = user.characters[fields[2]]
        if character.macros.pop(fields[3], None):
            return f"Removed macro {fields[3]} from {fields[2].capitalize()}."
        return f"No such macro exists on {fields[2].capitalize()}."

    async def _get_macros(self, user: User, fields: list) -> str:
        """Get all macros for a character.

        Args:
            user: The user object.
            fields: Command fields containing character name.

        Returns:
            A formatted string listing all macros for the character.
        """
        character = user.characters[fields[2]]
        macros: list[str] = [f"{m}[{character.macros[m]}]" for m in character.macros.keys()]
        return f"{fields[2].capitalize()} has the following macros: {macros}."

    async def _set_variable(self, user: User, fields: list) -> str:
        """Set a variable for a character.

        Args:
            user: The user object.
            fields: Command fields containing character name, variable name, and value.

        Returns:
            A success message string.
        """
        character = user.characters[fields[2]]
        character.variables[fields[3]] = fields[4]
        return f"Added variable {fields[3]} to {fields[2].capitalize()}."

    async def _delete_variable(self, user: User, fields: list) -> str:
        """Delete a variable from a character.

        Args:
            user: The user object.
            fields: Command fields containing character name and variable name.

        Returns:
            A success or error message string.
        """
        character = user.characters[fields[2]]
        if character.variables.pop(fields[3], None):
            return f"Removed variable {fields[3]} from {fields[2].capitalize()}."
        return f"No such variable exists on {fields[2].capitalize()}."

    async def _get_variables(self, user: User, fields: list) -> str:
        """Get all variables for a character.

        Args:
            user: The user object.
            fields: Command fields containing character name.

        Returns:
            A formatted string listing all variables for the character.
        """
        character = user.characters[fields[2]]
        variables: list[str] = [f"{v}[{character.variables[v]}]" for v in character.variables.keys()]
        return f"{fields[2].capitalize()} has the following variables: {variables}."

    async def _get_character(self, user: User, fields: list) -> str:
        """Get formatted character information.

        Displays detailed information about a character including stats,
        proficiencies, skills, and other attributes.

        Args:
            user: The user object.
            fields: Command fields, optionally containing character name.

        Returns:
            A formatted string containing character information.
        """
        msg = "```\n"
        if len(fields) > 2 and fields[2] in user.characters:
            name = fields[2]
        else:
            name = user.active

        character = user.characters[name]
        prof_mod: int = character.get_prof_mod()

        msg: str = f"{msg}Name: {name.capitalize()}\n"
        msg: str = f"{msg}Level: {character.level}\n"
        msg: str = f"{msg}Proficiency: {prof_mod}\n"
        msg: str = f"{msg}Ability Check Bonus: {character.ability_bonus}\n"
        msg: str = f"{msg}Skill Check Bonus: {character.skill_bonus}\n"
        msg: str = f"{msg}Jack of All Trades: {character.jack_of_all_trades}\n"

        msg: str = msg + "\n"

        for stat in self.stats:
            fullstat: str = STAT_FULL_NAMES.get(Stat(stat), stat)
            stat_enum = Stat(stat)
            score = character.stats[stat_enum]
            mod = character.get_stat_mod(stat_enum) + character.ability_bonus
            if stat_enum in character.save_prof:
                fstr: str = "%15s: %2s (%s/%s) ✓" % (fullstat.capitalize(), score, mod, mod + prof_mod)
                msg: str = f"{msg}{fstr}\n"
            else:
                fstr: str = "%15s: %2s (%s/%s)" % (fullstat.capitalize(), score, mod, mod)
                msg: str = f"{msg}{fstr}\n"

        msg: str = msg + "\n"

        for skill in self.skills:
            stat: str = SKILL_TO_STAT.get(skill, Stat.WISDOM).value
            pretty_skill: str = " ".join(skill.split("_")).title()
            mod, prof_indicator = character.get_skill_mod(skill)
            mod = mod + character.skill_bonus
            adv_mod: int = 5 if skill in character.advantage else 0
            fstr: str = "%15s: %2s (%s|%s) %s" % (pretty_skill, mod, stat, 10 + mod + adv_mod, prof_indicator)
            msg: str = f"{msg}{fstr}\n"

        msg: str = msg + "```"

        return msg

    async def _get_skill_stat(self, skill: str) -> str:
        """Get the ability stat associated with a skill.

        Args:
            skill: The skill name (can be short or long form).

        Returns:
            The associated ability stat abbreviation.
        """
        if skill in ["int", "intelligence", "arcana", "history", "investigation", "nature", "religion"]:
            stat = "int"
        elif skill in ["cha", "charisma", "deception", "intimidation", "performance", "persuasion"]:
            stat = "cha"
        elif skill in ["dex", "dexterity", "acrobatics", "sleight_of_hand", "stealth"]:
            stat = "dex"
        elif skill in ["str", "strength", "athletics"]:
            stat = "str"
        elif skill in ["con", "constitution"]:
            stat = "con"
        else:
            stat = "wis"

        return stat

    async def _is_ability_stat(self, skill: str) -> bool:
        """Check if a string represents an ability stat.

        Args:
            skill: The string to check.

        Returns:
            True if the string is an ability stat, False otherwise.
        """
        return skill in ["int", "intelligence", "cha", "charisma", "dex", "dexterity", "str", "strength", "con", "constitution", "wis", "wisdom"]

    async def _get_character_roll(self, character: Character, target: str, modifiers: dict) -> str:
        """Generate a dice roll expression for a character.

        Creates a dice notation string based on the character's stats,
        proficiencies, and modifiers for the given target (skill/stat/macro).

        Args:
            character: The character object containing stats and proficiencies.
            target: The skill, stat, or macro to roll for.
            modifiers: Dictionary of modifiers (save, crit, etc.).

        Returns:
            A dice notation string ready for rolling.
        """
        stat_enum = Stat(target) if target in self.stats else SKILL_TO_STAT.get(target, Stat.WISDOM)

        if target in character.macros:
            roll: str = await self._resolve_references(character, character.macros[target])
        else:
            roll = "1d20"
            roll: str = f"{roll}+{character.get_stat_mod(stat_enum)}"

            if (modifiers["save"] and character.is_save_proficient(stat_enum)) or target in character.skill_prof:
                roll: str = f"{roll}+{character.get_prof_mod()}"

            if target in character.skill_expertise:
                roll: str = f"{roll}+{character.get_prof_mod() * 2}"

        if target in self.stats and character.ability_bonus != 0:
            roll: str = f"{roll}+{character.ability_bonus}"

        if target in self.skills and character.skill_bonus != 0:
            roll: str = f"{roll}+{character.skill_bonus}"

        for var in modifiers["vars"]:
            roll: str = f"{roll}+{await self._resolve_references(character, character.variables[var])}"

        if roll.startswith("1d20"):
            short_target = STAT_SHORT_NAMES.get(target, target)
            if modifiers["mode"] == "a" or short_target in character.advantage:
                roll: str = roll.replace("1d20", "2d20kh1", 1)
            elif modifiers["mode"] == "ta":
                roll: str = roll.replace("1d20", "3d20kh1", 1)
            elif modifiers["mode"] == "d":
                roll: str = roll.replace("1d20", "2d20kl1", 1)

        if modifiers["crit"]:
            roll: str = re.sub(r"([0-9]+)d(4|6|8|10|12)", lambda x: f"{int(x.group(1))*2}d{x.group(2)}", roll)

        return roll

    async def _resolve_references(self, character: Character, value: str) -> str:
        """Resolve variable and stat references in a string.

        Replaces placeholders like $str_mod, $level, $prof, etc. with
        their actual values from the character data.

        Args:
            character: The character object.
            value: The string containing references to resolve.

        Returns:
            The string with all references resolved to their values.
        """
        value = value.replace("$level", str(character.level))
        value = value.replace("$prof", str(character.get_prof_mod()))

        for stat in self.stats:
            stat_enum = Stat(stat)
            value = value.replace(f"${stat}_mod", str(character.get_stat_mod(stat_enum)))
            value = value.replace(f"${stat}", str(character.stats[stat_enum]))

        for skill in self.skills:
            mod, _ = character.get_skill_mod(skill)
            value = value.replace(f"${skill}", str(mod))

        for var in character.variables.keys():
            value = value.replace(f"${var}", str(character.variables[var]))

        return value

    async def _generate_roll_summary(self, character: str, target: str, modifiers: dict, macros: dict) -> str:
        """Generate a human-readable summary of a roll.

        Args:
            character: The character name.
            target: The skill/stat/macro being rolled.
            modifiers: Dictionary of modifiers applied.
            macros: Dictionary of character macros.

        Returns:
            A descriptive string summarizing the roll.
        """
        summary: str = f"{character.capitalize()} rolled"

        if target in macros:
            summary: str = f"{summary} using the macro {target}"
        elif target in self.stats:
            full_stat = STAT_FULL_NAMES.get(Stat(target), target)
            summary: str = f"{summary} for a(n) {full_stat}"
        elif target in self.skills:
            summary: str = f"{summary} for a(n) {target.replace('_', ' ')}"
        else:
            summary: str = f"{summary} {target}"

        if target in self.stats or target in self.skills:
            if modifiers["save"]:
                summary: str = f"{summary} save"
            else:
                summary: str = f"{summary} check"

        mods_str = " with"
        if modifiers["mode"] == "a":
            mods_str: str = f"{mods_str} advantage plus"
        if modifiers["mode"] == "ta":
            mods_str: str = f"{mods_str} triple advantage plus"
        elif modifiers["mode"] == "d":
            mods_str: str = f"{mods_str} disadvantage plus"

        for var in modifiers["vars"]:
            mods_str: str = f"{mods_str} {var} plus"

        return f"{summary}{mods_str[:-5]}"


intents = discord.Intents.default()
intents.message_content = True
client: DNDRoller = DNDRoller(intents)
client.run(config["Discord"]["Token"])
