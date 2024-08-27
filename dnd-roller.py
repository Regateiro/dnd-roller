import configparser
import json
import math
import os
import re
import calendar
import logging
from datetime import datetime, timedelta

import d20
import discord
from dateutil.parser import parse
from discord import Message

logging.basicConfig(filename='/var/log/dnd-roller.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s : %(message)s')

config = configparser.ConfigParser()
config.read(
    f"{os.getenv('HOME', 'root')}/.config/dnd-roller/config.ini"
)
help_msg_1 = (
    'Available Commands (can be shorthanded to the first letter):\n'
    '```'
    '!roll <dice>                                                   # Roll the dice using dice notation\n'
    '!roll [<character>] <skill|macro> [crit] [save] [a|ta|d] [var] # Roll a character\'s stat, save or skill check\n'
    '\n'
    '!distance <ground> <vertical> <diagonal>                       # Calculates distances (use 0 to indicate the one to calculate)\n'
    '\n'
    '!f <height>                                                    # Calculates how long to hit the ground while free-falling\n'
    '\n'
    '!character                                                     # Manage user characters\n'
    '  - list                                                       # List all your characters\n'
    '  - active [<character>]                                       # Sets the active character (shows the current one if omited)\n'
    '  - info [<character>]                                         # Shows a character information\n'
    '  - show [<character>]                                         # Alias for info (see info)\n'
    '  - create <character> <full_template>                         # Create/Overwrite a character\n'
    '  - update <character> main <main_template>                    # Update the character\'s main stats\n'
    '  - update <character> saves <saves_template>                  # Update the character\'s save proficiencies\n'
    '  - update <character> skills <skills_template>                # Update the character\'s skill proficiencies\n'
    '  - update <character> expertise <expertise_template>          # Update the character\'s skill expertise\n'
    '  - delete <character>                                         # Delete a character\n'
    '  - help                                                       # Show more detailed help\n'
    '```'
)
help_msg_2 = (
    'Advanced Commands (can be shorthanded to the first letter):\n'
    '```'
    '!macro                                          # Manage character macros\n'
    '  - set [<character>] <name> <dice>             # Set a macro using dice notation for a character\n'
    '  - delete [<character>] <name>                 # Delete a macro from a character\n'
    '  - list [<character>]                          # List all the macros for a character\n'
    '  - help                                        # Show more detailed help\n'
    '\n'
    '!variable                                       # Manage character variables to use as modifiers\n'
    '  - set [<character>] <name> <value>            # Set a variable value for a character\n'
    '  - delete [<character>] <name>                 # Delete a variable from a character\n'
    '  - list [<character>]                          # List all the variables for a character\n'
    '  - help                                        # Show more detailed help\n'
    '```'
)
char_help = (
    '```'
    'Main Template:\n'
    ' - <level> <strength> <dexterity> <constitution> <intelligence> <wisdom> <charisma>\n'
    ' - Example: \'!character update Urso main 3 16 12 14 6 10 6\'\n'
    '\n'
    'Saves Proficiency Template:\n'
    ' - [save] [save]...\n'
    ' - Available Saves: str, dex, con, int, wis, cha\n'
    ' - Example: \'!character update Urso saves str con\'\n'
    '\n'
    'Skill Proficiency Template:\n'
    ' - [skill] [skill]...\n'
    ' - Available Saves: acrobatics, animal_handling, arcana, athletics, deception, '
    'history, insight, intimidation, investigation, medicine, nature, perception, performance, '
    'persuasion, religion, sleight_of_hand, stealth, survival\n'
    ' - Example: \'!character update Urso skills athletics nature stealth survival\'\n'
    '\n'
    'Skill Expertise Template:\n'
    ' - [skill] [skill]...\n'
    ' - Available Saves: acrobatics, animal_handling, arcana, athletics, deception,'
    'history, insight, intimidation, investigation, medicine, nature, perception, performance'
    'persuasion, religion, sleight_of_hand, stealth, survival\n'
    ' - Example: \'!character update Urso expertise perception\'\n'
    '\n'
    'Bonus Template:\n'
    ' - <save bonus> <check bonus>\n'
    ' - Example: \'!character update Urso bonus 1 2\'\n'
    '\n'
    'Full Template:\n'
    ' - <main_stats> | <saves> | <skills> | <expertises>\n'
    ' - Example: !character create Urso 3 16 12 14 6 10 6 | str con | athletics nature stealth survival | perception\n'
    '```'
)
vars_help = (
    '```'
    'Variable/Macro names can be any single word, however the following words will not function properly:\n'
    ' - a, ta, adv, tadv, advantage, tadvantage, d, dis, disadvantage, crit, save, and any stat or skill name\n\n'
    'Variable/Macro values can include:\n'
    ' - Simple Bonuses:      2             # (Example: !v set rage 2)\n'
    ' - Dice Notation:       1d4           # (Example: !v set bless 1d4)\n'
    ' - Special References:  $ref          # (Example: !v set kol $cha_mod)\n'
    ' - Mix of the Above:    1d4+$ref      # (Example: !v set kol 1d4+$cha_mod)\n\n'
    'Special References:\n'
    ' - Level:               $level\n'
    ' - Proficiency Bonus:   $prof\n'
    ' - Ability Scores:      $<score>      # (Example: $str)\n'
    ' - Ability Modifiers:   $<score>_mod  # (Example: $wis_mod)\n'
    ' - Skills:              $<skill>      # (Example: $insight)\n\n'
    '```'
)
session_help = (
    'Available Session Management Commands (can be shorthanded to the first letter):\n'
    '```'
    '!session                          # Manage server\'s sessions.\n'
    '  - weekday <monday|tuesday|...>  # Sets the default weekday for sessions.\n'
    '  - list                          # List all the currently scheduled sessions and player unavailabilities.\n'
    '  - next                          # List the next scheduled session and player unavailabilities.\n'
    '  - schedule <YYYY-MM-DD>         # Schedule a session for the given date.\n'
    '  - cancel  <YYYY-MM-DD>          # Cancel a session scheduled for the given date.\n'
    '  - available  <YYYY-MM-DD>       # Set a player as available for a given session. This is the default setting.\n'
    '  - unavailable <YYYY-MM-DD>      # Set a player as unavailable for a given session.\n'
    '  - help                          # Show this help.\n'
    '```'
)

class DNDRoller(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents)

        try:
            with open(f"{config['General']['Storage']}/cache.json", "rt") as fd:
                self.cache = json.load(fd)
        except:
            self.cache = {}

        self.stats = ['str', 'dex', 'con', 'int', 'wis', 'cha']
        self.skills = [
            'acrobatics', 'animal_handling', 'arcana', 'athletics', 'deception',
            'history', 'insight', 'intimidation', 'investigation', 'medicine',
            'nature', 'perception', 'performance', 'persuasion', 'religion',
            'sleight_of_hand', 'stealth', 'survival'
        ]

    async def on_ready(self):
        logging.info('Logged on as {0}!'.format(self.user))

    async def on_message(self, message: Message):
        # Filter out normal messages
        if message.content.startswith('!'):
            try:
                if message.guild:
                    guild = str(message.guild.id)
                else:
                    guild = "None"

                # Ensure the cache is initialized for the author
                author = f"{str(message.author.id)}"
                self.cache.setdefault(guild, {})
                self.cache[guild].setdefault('users', {})
                self.cache[guild].setdefault('sessions', {})
                self.cache[guild]['sessions'].setdefault('on', [])
                self.cache[guild]['sessions'].setdefault('off', [])
                self.cache[guild]['sessions'].setdefault('wday', -1)
                self.cache[guild]['users'].setdefault(author, {})
                self.cache[guild]['users'][author]['name'] = str(message.author.display_name)
                self.cache[guild]['users'][author].setdefault('characters', {})
                self.cache[guild]['users'][author].setdefault('unavailability', [])
                self.cache[guild]['users'][author].setdefault('active', '')
                fields = message.content.lower().split(' ')
                summary = ''

                # Process roll commands
                if fields[0] == '!r' or fields[0] == '!roll':
                    # If the character is missing from the roll command, add the active one
                    if fields[1] not in self.cache[guild]['users'][author]['characters'].keys():
                        if self.cache[guild]['users'][author]['active'] in self.cache[guild]['users'][author]['characters']:
                            fields = fields[:1] + [self.cache[guild]['users'][author]['active']] + fields[1:]
                        else:
                            fields = fields[:1] + ['You'] + fields[1:]

                    # Check if a character was passed to roll a stat/skill check or save
                    character = self.cache[guild]['users'][author]['characters'].get(fields[1], await self.create_empty_character())
                    modifiers = {
                        'mode': 'n',
                        'save': False,
                        'crit': False,
                        'vars': [],
                    }

                    try:
                        roll = d20.roll(await self.resolve_references(character, fields[2]))
                    except:
                        for field in fields[3:]:
                            if field == 'save':
                                modifiers['save'] = True
                            elif field in ['crit', 'critical']:
                                modifiers['crit'] = True
                            elif field in ['a', 'adv', 'advantage']:
                                modifiers['mode'] = 'a'
                            elif field in ['ta', 'tadv', 'tadvantage']:
                                modifiers['mode'] = 'ta'
                            elif field in ['d', 'dis', 'disadvantage']:
                                modifiers['mode'] = 'd'
                            elif field in character['variables'].keys():
                                modifiers['vars'].append(field)

                        roll = d20.roll(await self.get_character_roll(character, fields[2], modifiers))

                    summary = f"{await self.generate_roll_summary(fields[1], fields[2], modifiers, character['macros'])}:\n"
                    await message.channel.send(
                        f"{summary}{str(roll)}"
                    )

                # Process character commands
                elif fields[0] == '!character' or fields[0] == '!char' or fields[0] == '!c':
                    # Send character help if requested or no option selected
                    if len(fields) == 1 or fields[1] == 'help' or fields[1] == 'h':
                        await message.channel.send(char_help)

                    # Process create character command
                    elif fields[1] == 'create' or fields[1] == 'c':
                        await message.channel.send(
                            await self.create_character(guild, author, fields)
                        )

                    # Process delete character command
                    elif fields[1] == 'delete' or fields[1] == 'd':
                        await message.channel.send(
                            await self.delete_character(guild, author, fields)
                        )

                    # Process update character command
                    elif fields[1] == 'update' or fields[1] == 'u':
                        await message.channel.send(
                            await self.update_character(guild, author, fields)
                        )

                    # Process active character command
                    elif fields[1] == 'active' or fields[1] == 'a':
                        if len(fields) == 2:
                            await message.channel.send(f"You current active character is {self.cache[guild]['users'][author]['active'].capitalize()}.")
                        elif fields[2] in self.cache[guild]['users'][author]['characters'].keys():
                            self.cache[guild]['users'][author]['active'] = fields[2]
                            await message.channel.send(f'{fields[2].capitalize()} set as the active character.')
                        else:
                            await message.channel.send('No such character exists for you.')

                    # Process info character command
                    elif fields[1] == 'info' or fields[1] == 'show' or fields[1] == 'i' or fields[1] == 's':
                        await message.channel.send(
                            await self.get_character(guild, author, fields)
                        )

                    # Process info character command
                    elif fields[1] == 'list' or fields[1] == 'l':
                        characters = [c.capitalize() for c in self.cache[guild]['users'][author]['characters'].keys()]
                        await message.channel.send(
                            f"Your characters are: {characters}."
                        )

                # Process macro commands
                elif fields[0] == '!m' or fields[0] == '!macro':
                    # Send character help if requested or no option selected
                    if len(fields) == 1 or fields[1] == 'help' or fields[1] == 'h':
                        await message.channel.send(vars_help)

                    # Add the active character if missing from a 2 parameter command
                    if len(fields) == 2:
                        fields.append(self.cache[guild]['users'][author]['active'])

                    # If the character is missing from the macro command, add the active one
                    if fields[2] not in self.cache[guild]['users'][author]['characters'].keys():
                        fields = fields[:2] + [self.cache[guild]['users'][author]['active']] + fields[2:]

                    # Process set macro command
                    if fields[1] == 'set' or fields[1] == 's':
                        await message.channel.send(
                            await self.set_macro(guild, author, fields)
                        )

                    # Process delete macro command
                    elif fields[1] == 'delete' or fields[1] == 'd':
                        await message.channel.send(
                            await self.delete_macro(guild, author, fields)
                        )

                    # Process list macro command
                    elif fields[1] == 'list' or fields[1] == 'l':
                        await message.channel.send(
                            await self.get_macros(guild, author, fields)
                        )

                # Process vars commands
                elif fields[0] == '!v' or fields[0] == '!var' or fields[0] == '!variable':
                    # Send character help if requested or no option selected
                    if len(fields) == 1 or fields[1] == 'help' or fields[1] == 'h':
                        await message.channel.send(vars_help)

                    # Add the active character if missing from a 2 parameter command
                    if len(fields) == 2:
                        fields.append(self.cache[guild]['users'][author]['active'])
                            
                    # If the character is missing from the macro command, add the active one
                    if fields[2] not in self.cache[guild]['users'][author]['characters'].keys():
                        fields = fields[:2] + [self.cache[guild]['users'][author]['active']] + fields[2:]

                    # Process set variable command
                    if fields[1] == 'set' or fields[1] == 's':
                        await message.channel.send(
                            await self.set_variable(guild, author, fields)
                        )

                    # Process delete variable command
                    elif fields[1] == 'delete' or fields[1] == 'h':
                        await message.channel.send(
                            await self.delete_variable(guild, author, fields)
                        )

                    # Process list variable command
                    elif fields[1] == 'list' or fields[1] == 'l':
                        await message.channel.send(
                            await self.get_variables(guild, author, fields)
                        )

                # Process session commands
                elif fields[0] == '!session' or fields[0] == '!s':
                    await self.clean_sessions(guild)

                    # Send character help if requested or no option selected
                    if len(fields) == 1 or fields[1] == 'help' or fields[1] == 'h':
                        await message.channel.send(session_help)

                    elif fields[1] == 'weekday' or fields[1] == 'w':
                        day = [x.lower() for x in list(calendar.day_name)].index(fields[2].lower())
                        self.cache[guild]['sessions']['wday'] = day
                        await message.channel.send(
                            f"Default session weekday set to {calendar.day_name[self.cache[guild]['sessions']['wday']]}."
                        )

                    elif fields[1] == 'schedule' or fields[1] == 's':
                        date = parse(fields[2])
                        if date.date() >= date.now().date():
                            datestr = date.strftime('%Y-%m-%d')
                            if datestr in self.cache[guild]['sessions']['on'] or (
                                date.weekday() == self.cache[guild]['sessions']['wday'] and datestr not in self.cache[guild]['sessions']['off']
                            ):
                                await message.channel.send(
                                    f"We already have a session on that day."
                                )
                            else:
                                if date.weekday() != self.cache[guild]['sessions']['wday']:
                                    self.cache[guild]['sessions']['on'].append(datestr)

                                if datestr in self.cache[guild]['sessions']['off']:
                                    self.cache[guild]['sessions']['off'].remove(datestr)

                                await message.channel.send(
                                    f"Session scheduled to {datestr} :tada:"
                                )
                        else:
                            await message.channel.send(
                                f"I'm also eager, but even I cannot go back in time."
                            )

                    elif fields[1] == 'cancel' or fields[1] == 'c':
                        date = parse(fields[2])
                        datestr = date.strftime('%Y-%m-%d')
                        if datestr in self.cache[guild]['sessions']['on']:
                            self.cache[guild]['sessions']['on'].remove(datestr)
                            await message.channel.send(f"Extra session cancelled.")
                        elif date.weekday() == self.cache[guild]['sessions']['wday']:
                            if datestr not in self.cache[guild]['sessions']['off']:
                                self.cache[guild]['sessions']['off'].append(datestr)
                                await message.channel.send(f"Sunday session cancelled.")
                            else:
                                await message.channel.send(f"This Sunday session was already cancelled.")
                        else:
                            await message.channel.send(
                                f"Could not find an extra session scheduled for that date."
                            )

                    elif fields[1] == 'available' or fields[1] == 'a':
                        date = parse(fields[2])
                        datestr = date.strftime('%Y-%m-%d')
                        if datestr in self.cache[guild]['sessions']['on'] or date.weekday() == self.cache[guild]['sessions']['wday']:
                            if datestr in self.cache[guild]['users'][author]['unavailability']:
                                self.cache[guild]['users'][author]['unavailability'].remove(datestr)
                                await message.channel.send(f"Glad to see you can make it!")
                            else:
                                await message.channel.send(f"Didn't know you couldn't make it, but I'm glad to see you can make it!")
                        else:
                            await message.channel.send(
                                f"I do not recall a session scheduled for that day."
                            )

                    elif fields[1] == 'unavailable' or fields[1] == 'u':
                        date = parse(fields[2])
                        datestr = date.strftime('%Y-%m-%d')
                        if datestr in self.cache[guild]['sessions']['on'] or date.weekday() == self.cache[guild]['sessions']['wday']:
                            if datestr not in self.cache[guild]['users'][author]['unavailability']:
                                self.cache[guild]['users'][author]['unavailability'].append(datestr)
                                await message.channel.send(f"If we play, we'll try not to kill your character.")
                            else:
                                await message.channel.send(f"We know :(")
                        else:
                            await message.channel.send(
                                f"I do not recall a session scheduled for that day."
                            )

                    elif fields[1] == 'list' or fields[1] == 'l':
                        await message.channel.send('Next four scheduled sessions:')

                        reported = 0
                        date = datetime.now()
                        while reported != 4:
                            datestr = date.strftime('%Y-%m-%d')
                            if (date.weekday() == self.cache[guild]['sessions']['wday'] and datestr not in self.cache[guild]['sessions']['off']) or datestr in self.cache[guild]['sessions']['on']:
                                await message.channel.send(
                                    f"**{datestr}** - Missing players: {[self.cache[guild]['users'][u]['name'] for u in self.cache[guild]['users'].keys() if datestr in self.cache[guild]['users'][u]['unavailability']]}"
                                )
                                reported = reported + 1
                            date += timedelta(days=1)

                    elif fields[1] == 'next' or fields[1] == 'n':
                        await message.channel.send('Next scheduled session:')

                        reported = False
                        date = datetime.now()
                        while not reported:
                            datestr = date.strftime('%Y-%m-%d')
                            if (date.weekday() == self.cache[guild]['sessions']['wday'] and datestr not in self.cache[guild]['sessions']['off']) or datestr in self.cache[guild]['sessions']['on']:
                                await message.channel.send(
                                    f"**{datestr}** - Missing players: {[self.cache[guild]['users'][u]['name'] for u in self.cache[guild]['users'].keys() if datestr in self.cache[guild]['users'][u]['unavailability']]}"
                                )
                                reported = True
                            date += timedelta(days=1)

                elif fields[0] == '!distance' or fields[0] == '!d':
                    if len(fields) == 4:
                        x = int(fields[1])
                        y = int(fields[2])
                        d = int(fields[3])
                        
                        if x and y and d:
                            await message.channel.send("So you already know all three sides? Why are you asking me then? Kids these days...")
                        if x and y:
                            d = math.ceil(math.sqrt(math.pow(x, 2) + math.pow(y, 2)) / 5) * 5
                            await message.channel.send(f"Moving `{x}ft` on the ground and `{y}ft` vertically costs `{d}ft` of total movement.")
                        elif x and d:
                            y = math.floor(math.sqrt(math.pow(d, 2) - math.pow(x, 2)) / 5) * 5
                            await message.channel.send(f"Moving `{d}ft` diagonally and `{x}ft` on the ground allows you to move `{y}ft` vertically.")
                        elif y and d:
                            x = math.floor(math.sqrt(math.pow(d, 2) - math.pow(y, 2)) / 5) * 5
                            await message.channel.send(f"Moving `{d}ft` diagonally and `{y}ft` vertically allows you to move `{x}ft` on the ground.")
                        else:
                            await message.channel.send("I need to know the length of two sides to calculate the third, I'm not a wizard...")
                            
                        
                        await message.channel.send(f"")
                    else:
                        await message.channel.send("Received too few or too many arguments, please check the help command for instructions.")

                elif fields[0] == '!fall' or fields[0] == '!f':
                    if len(fields) == 3:
                        height = int(fields[1])
                        if height < 500:
                            time = round(math.sqrt(height * 36 / 500.0), 2)
                        else:
                            time = round(height * 6 / 500.0, 2)
                        rounds = round(time / 6, 2)
                        await message.channel.send(f"Falling from `{height}ft` high will take `{time}s` to hit the ground, or `{rounds}` rounds.")
                    else:
                        await message.channel.send("Received too few or too many arguments, please check the help command for instructions.")

                # Process help command
                elif fields[0] == '!h' or fields[0] == '!help':
                    await message.channel.send(help_msg_1)
                    await message.channel.send(help_msg_2)
                    await message.channel.send(session_help)
            except Exception as ex:
                logging.exception(ex)
            finally:
                with open(f"{config['General']['Storage']}/cache.json", "wt") as fd:
                    json.dump(self.cache, fd)

    async def clean_sessions(self, guild: str) -> None:
        now = datetime.now().strftime('%Y-%m-%d')

        for session in [s for s in self.cache[guild]['sessions']['on'] if s < now]:
            self.cache[guild]['sessions']['on'].remove(session)

        for session in [s for s in self.cache[guild]['sessions']['off'] if s < now]:
            self.cache[guild]['sessions']['off'].remove(session)

        for user in [u for u in self.cache[guild]['users'].keys()]:
            for session in [s for s in self.cache[guild]['users'][user]['unavailability'] if s < now]:
                self.cache[guild]['users'][user]['unavailability'].remove(session)

    async def create_character(self, guild: str, author: str, fields: list) -> str:
        try:
            name = fields[2]
            character = {
                'level': int(fields[3]),
                'stats': {
                    'str': int(fields[4]),
                    'dex': int(fields[5]),
                    'con': int(fields[6]),
                    'int': int(fields[7]),
                    'wis': int(fields[8]),
                    'cha': int(fields[9]),
                },
                'save_prof': [],
                'skill_prof': [],
                'skill_expertise': [],
                'ability_bonus': 0,
                'skill_bonus': 0,
                'macros': {},
                'variables': {},
            }

            assert fields[10] == '|'
            idx = 11

            while fields[idx] != '|':
                if fields[idx] in self.stats:
                    character['save_prof'].append(fields[idx])
                else:
                    return f'Error: unknown stat {fields[idx]}.'
                idx = idx + 1
            idx = idx + 1

            while fields[idx] != '|':
                if fields[idx] in self.skills:
                    character['skill_prof'].append(fields[idx])
                else:
                    return f'Error: unknown skill {fields[idx]}.'
                idx = idx + 1
            idx = idx + 1

            while idx < len(fields):
                if fields[idx] in self.skills:
                    character['skill_expertise'].append(fields[idx])
                else:
                    return f'Error: unknown skill {fields[idx]}.'
                idx = idx + 1

            self.cache[guild]['users'][author]['characters'][name] = character
            self.cache[guild]['users'][author]['active'] = name
            return f'Character {name} created and set as default.'
        except:
            return 'Could not create the character, use !help for help.'

    async def delete_character(self, guild: str, author: str, fields: list) -> str:
        if self.cache[guild]['users'][author]['characters'].pop(fields[2], None):
            return f'Removed character {fields[2].capitalize()}. You may need to set a new active character.'
        else:
            return 'No such character exists for you.'

    async def update_character(self, guild: str, author: str, fields: list) -> str:
        if fields[2] in self.cache[guild]['users'][author]['characters'].keys():
            character = self.cache[guild]['users'][author]['characters'][fields[2]]
            idx = 4

            if fields[3] == 'main':
                character['level'] = int(fields[4])
                character['stats'] = {
                    'str': int(fields[5]),
                    'dex': int(fields[6]),
                    'con': int(fields[7]),
                    'int': int(fields[8]),
                    'wis': int(fields[9]),
                    'cha': int(fields[10]),
                }

            elif fields[3] == 'saves':
                character['save_prof'].clear()
                while idx < len(fields):
                    if fields[idx] in self.stats:
                        character['save_prof'].append(fields[idx])
                    else:
                        return f'Error: unknown stat {fields[idx]}.'
                    idx = idx + 1

            elif fields[3] == 'bonus':
                if len(fields) == 6:
                    character['ability_bonus'] = int(fields[4])
                    character['skill_bonus'] = int(fields[5])
                else:
                    return f'Error: Wrong number of arguments. Expected general save and check bonus.'

            elif fields[3] == 'skills':
                character['skill_prof'].clear()
                while idx < len(fields):
                    if fields[idx] in self.skills:
                        character['skill_prof'].append(fields[idx])
                    else:
                        return f'Error: unknown skill {fields[idx]}.'
                    idx = idx + 1

            elif fields[3] == 'expertise':
                character['skill_expertise'].clear()
                while idx < len(fields):
                    if fields[idx] in self.skills:
                        character['skill_expertise'].append(fields[idx])
                    else:
                        return f'Error: unknown skill {fields[idx]}.'
                    idx = idx + 1

            self.cache[guild]['users'][author]['characters'][fields[2]] = character
            return f'Character {fields[2]} was updated.'
        else:
            return f'No such character exists for you.'

    async def set_macro(self, guild: str, author: str, fields: list) -> str:
        character = self.cache[guild]['users'][author]['characters'][fields[2]]
        character['macros'][fields[3]] = fields[4]
        return f'Added macro {fields[3]} to {fields[2].capitalize()}.'

    async def delete_macro(self, guild: str, author: str, fields: list) -> str:
        character = self.cache[guild]['users'][author]['characters'][fields[2]]
        if character['macros'].pop(fields[3], None):
            return f'Removed macro {fields[3]} from {fields[2].capitalize()}.'
        else:
            return f'No such macro exists on {fields[2].capitalize()}.'

    async def get_macros(self, guild: str, author: str, fields: list) -> str:
        character = self.cache[guild]['users'][author]['characters'][fields[2]]
        macros = [f"{m}[{character['macros'][m]}]" for m in character['macros'].keys()]
        return f"{fields[2].capitalize()} has the following macros: {macros}."

    async def set_variable(self, guild: str, author: str, fields: list) -> str:
        character = self.cache[guild]['users'][author]['characters'][fields[2]]
        character['variables'][fields[3]] = fields[4]
        return f'Added variable {fields[3]} to {fields[2].capitalize()}.'

    async def delete_variable(self, guild: str, author: str, fields: list) -> str:
        character = self.cache[guild]['users'][author]['characters'][fields[2]]
        if character['variables'].pop(fields[3], None):
            return f'Removed variable {fields[3]} from {fields[2].capitalize()}.'
        else:
            return f'No such variable exists on {fields[2].capitalize()}.'

    async def get_variables(self, guild: str, author: str, fields: list) -> str:
        character = self.cache[guild]['users'][author]['characters'][fields[2]]
        variables = [f"{v}[{character['variables'][v]}]" for v in character['variables'].keys()]
        return f"{fields[2].capitalize()} has the following variables: {variables}."

    async def get_character(self, guild: str, author: str, fields: list) -> str:
        msg = '```\n'
        if len(fields) > 2 and fields[2] in self.cache[guild]['users'][author]['characters'].keys():
            name = fields[2]
        else:
            name = self.cache[guild]['users'][author]['active']

        character = self.cache[guild]['users'][author]['characters'][name]
        prof_mod = await self.get_character_prof_mod(character)

        msg = f"{msg}Name: {name.capitalize()}\n"
        msg = f"{msg}Level: {character['level']}\n"
        msg = f"{msg}Proficiency: {prof_mod}\n"
        msg = f"{msg}Ability Check Bonus: {character.get('ability_bonus', 0)}\n"
        msg = f"{msg}Skill Check Bonus: {character.get('skill_bonus', 0)}\n"

        msg = msg + "\n"

        for stat in self.stats:
            fullstat = await self.get_stat_fullname(stat)
            score = character['stats'][stat]
            mod = await self.get_character_stat_mod(character, stat) + character.get('ability_bonus', 0)
            if stat in character['save_prof']:
                fstr = '%15s: %2s (%s/%s) ✓'%(fullstat.capitalize(), score, mod, mod + prof_mod)
                msg = f"{msg}{fstr}\n"
            else:
                fstr = '%15s: %2s (%s/%s)'%(fullstat.capitalize(), score, mod, mod)
                msg = f"{msg}{fstr}\n"

        msg = msg + "\n"

        for skill in self.skills:
            stat = await self.get_skill_stat(skill)
            pretty_skill = ' '.join(skill.split('_')).title()
            mod, prof_indicator = await self.get_character_skill_mod(character, skill)
            mod = mod + character.get('skill_bonus', 0)
            fstr = '%15s: %2s (%s|%s) %s'%(pretty_skill, mod, stat, 10 + mod, prof_indicator)
            msg = f"{msg}{fstr}\n"

        msg = msg + "```"

        return msg

    async def get_skill_stat(self, skill: str) -> str:
        if skill in ['int', 'intelligence', 'arcana', 'history', 'investigation', 'nature', 'religion']:
            stat = 'int'
        elif skill in ['cha', 'charisma', 'deception', 'intimidation', 'performance', 'persuasion']:
            stat = 'cha'
        elif skill in ['dex', 'dexterity', 'acrobatics', 'sleight_of_hand', 'stealth']:
            stat = 'dex'
        elif skill in ['str', 'strength', 'athletics']:
            stat = 'str'
        elif skill in ['con', 'constitution']:
            stat = 'con'
        else:
            stat = 'wis'

        return stat

    async def is_ability_stat(self, skill: str) -> bool:
        return skill in ['int', 'intelligence', 'cha', 'charisma', 'dex', 'dexterity', 'str', 'strength', 'con', 'constitution', 'wis', 'wisdom']

    async def get_character_roll(self, character: dict, target: str, modifiers: dict) -> str:
        # If a macro was passed, roll that instead
        if target in character['macros']:
            roll = await self.resolve_references(character, character['macros'][target])
        else:
            # Determine the base die given the roll mode
            roll = '1d20'

            # Determine the relevant stat
            stat = await self.get_skill_stat(target)

            # Determine stat modifier for the roll
            roll = f"{roll}+{await self.get_character_stat_mod(character, stat)}"

            # Determine if proficiency applies
            if (modifiers['save'] and stat in character['save_prof']) or target in character['skill_prof']:
                roll = f"{roll}+{await self.get_character_prof_mod(character)}"

            # Determine if expertise applies
            if target in character['skill_expertise']:
                roll = f"{roll}+{await self.get_character_prof_mod(character) * 2}"

        # Add general save bonus if it is a save roll
        if await self.is_ability_stat(target) and character.get('ability_bonus', 0) != 0:
            roll = f"{roll}+{character['ability_bonus']}"

        # Add general check bonus if it is a check roll
        if target in self.skills and character.get('skill_bonus', 0) != 0:
            roll = f"{roll}+{character['skill_bonus']}"

        # Add other modifiers
        for var in modifiers['vars']:
            roll = f"{roll}+{await self.resolve_references(character, character['variables'][var])}"

        # Set advantage/disadvantage
        if roll.startswith('1d20'):
            if modifiers['mode'] == 'a':
                roll = roll.replace('1d20', '2d20kh1', 1)
            if modifiers['mode'] == 'ta':
                roll = roll.replace('1d20', '3d20kh1', 1)
            elif modifiers['mode'] == 'd':
                roll = roll.replace('1d20', '2d20kl1', 1)

        # Process crit by doubling all die
        if modifiers['crit']:
            roll = re.sub(r'([0-9]+)d(4|6|8|10|12)', lambda x: f'{int(x.group(1))*2}d{x.group(2)}', roll)

        return roll

    async def resolve_references(self, character: dict, value: str) -> str:
        # Run replace strings
        value = value.replace('$level', str(character['level']))
        value = value.replace('$prof', str(await self.get_character_prof_mod(character)))

        for stat in self.stats:
            value = value.replace(f'${stat}_mod', str(await self.get_character_stat_mod(character, stat)))
            value = value.replace(f'${stat}', str(character['stats'][stat]))

        for skill in self.skills:
            value = value.replace(f'${skill}', str(await self.get_character_skill_mod(character, skill)))

        # Replace variables
        for var in character['variables'].keys():
            value = value.replace(f'${var}', str(character['variables'][var]))

        return value

    async def get_character_stat_mod(self, character: dict, stat: str) -> int:
        return math.floor(character['stats'][stat] / 2) - 5

    async def get_character_skill_mod(self, character: dict, skill: str) -> tuple[int, str]:
        stat = await self.get_skill_stat(skill)

        if skill in character['skill_prof']:
            return await self.get_character_stat_mod(character, stat) + await self.get_character_prof_mod(character), "✓"

        if skill in character['skill_expertise']:
            return await self.get_character_stat_mod(character, stat) + await self.get_character_prof_mod(character) * 2, "✓✓"

        return await self.get_character_stat_mod(character, stat), ""

    async def get_character_prof_mod(self, character: dict) -> int:
        return math.floor((character['level'] - 1) / 4) + 2

    async def generate_roll_summary(self, character: str, target: str, modifiers: dict, macros: dict) -> str:
        summary = f'{character.capitalize()} rolled'

        # Determine what we are rolling
        if target in macros.keys():
            summary = f'{summary} using the macro {target}'
        elif target in self.stats:
            summary = f'{summary} for a(n) {await self.get_stat_fullname(target)}'
        elif target in self.skills:
            summary = f"{summary} for a(n) {target.replace('_', ' ')}"
        else:
            summary = f"{summary} {target}"

        # Only state that it is a save or a check if it is not a macro
        if target in self.stats or target in self.skills:
            if modifiers['save']:
                summary = f'{summary} save'
            else:
                summary = f'{summary} check'

        # Include wether advantage or disadvantage was used
        mods_str = ' with'
        if modifiers['mode'] == 'a':
            mods_str = f'{mods_str} advantage plus'
        if modifiers['mode'] == 'ta':
            mods_str = f'{mods_str} triple advantage plus'
        elif modifiers['mode'] == 'd':
            mods_str = f'{mods_str} disadvantage plus'

        # Add other modifiers that are being applied
        for var in modifiers['vars']:
            mods_str = f'{mods_str} {var} plus'

        return f'{summary}{mods_str[:-5]}'

    async def get_stat_fullname(self, stat: str) -> str:
        if stat == 'str':
            return 'strength'

        if stat == 'dex':
            return 'dexterity'

        if stat == 'con':
            return 'constitution'

        if stat == 'int':
            return 'intelligence'

        if stat == 'wis':
            return 'wisdom'

        if stat == 'cha':
            return 'charisma'

        return "unknown"

    async def create_empty_character(self) -> dict:
        return {
            'level': -7,  # 0 Prof Bonus
            'stats': {
                'str': 10,
                'dex': 10,
                'con': 10,
                'int': 10,
                'wis': 10,
                'cha': 10,
            },
            'save_prof': [],
            'skill_prof': [],
            'skill_expertise': [],
            'ability_bonus': 0,
            'skill_bonus': 0,
            'macros': {},
            'variables': {},
        }


intents = discord.Intents.default()
intents.message_content = True
client = DNDRoller(intents)
client.run(config['Discord']['Token'])
