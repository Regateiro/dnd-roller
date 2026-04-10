"""Main Discord client for the D&D Roller bot."""

from __future__ import annotations

import configparser
import json
import logging
import os
from typing import TYPE_CHECKING

import discord

from bot.handlers import CharacterHandler, RollHandler, SessionHandler, UtilityHandler
from bot.models import Cache, GuildData, User
from bot.services import RollService, SessionService

if TYPE_CHECKING:
    from discord import Message

logging.basicConfig(
    filename="/var/log/dnd-roller.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s : %(name)s : %(levelname)s : %(message)s",
)

config = configparser.ConfigParser()
config.read(f"{os.getenv('HOME')}/.config/dnd-roller/config.ini")


class DNDRollerClient(discord.Client):
    """Discord Client for D&D dice rolling and character management."""

    _COMMANDS = {
        "!r": "roll",
        "!roll": "roll",
        "!character": "character",
        "!char": "character",
        "!c": "character",
        "!m": "macro",
        "!macro": "macro",
        "!v": "variable",
        "!var": "variable",
        "!variable": "variable",
        "!session": "session",
        "!s": "session",
        "!distance": "distance",
        "!d": "distance",
        "!fall": "fall",
        "!f": "fall",
        "!h": "help",
        "!help": "help",
    }

    _COMMAND_HANDLERS = {
        "roll": "handle",
        "character": "handle",
        "session": "handle",
        "macro": "handle_macro",
        "variable": "handle_variable",
        "distance": "handle_distance",
        "fall": "handle_fall",
        "help": "handle_help",
    }

    def __init__(self, app_intents: discord.Intents) -> None:
        """Initialize the D&D Roller bot."""
        super().__init__(intents=app_intents)

        self._roll_service = RollService()
        self._session_service = SessionService()

        self._roll_handler = RollHandler(self._roll_service)
        self._character_handler = CharacterHandler()
        self._session_handler = SessionHandler(self._session_service)
        self._utility_handler = UtilityHandler()

        self._handlers = {
            "roll": self._roll_handler,
            "character": self._character_handler,
            "session": self._session_handler,
            "macro": self._utility_handler,
            "variable": self._utility_handler,
            "distance": self._utility_handler,
            "fall": self._utility_handler,
            "help": self._utility_handler,
        }

        self.cache = self._load_cache()

    def _load_cache(self) -> Cache:
        """Load the cache from disk or create a new one."""
        try:
            storage_path = f"{config['General']['Storage']}/cache.json"
            with open(storage_path, "rt", encoding="utf-8") as fd:
                return Cache.from_dict(json.load(fd))
        except FileNotFoundError:
            return Cache()

    def _save_cache(self) -> None:
        """Save the cache to disk."""
        with open(f"{config['General']['Storage']}/cache.json", "wt", encoding="utf-8") as fd:
            json.dump(self.cache.to_dict(), fd)

    async def on_ready(self) -> None:
        """Called when the bot has successfully connected to Discord."""
        logging.info("Logged on as {0}!".format(self.user))

    async def on_message(self, message: Message) -> None:
        """Handle incoming Discord messages and process bot commands."""
        if not message.content.startswith("!"):
            return

        if message.author.id == self.user.id:
            return

        try:
            guild_id = str(message.guild.id) if message.guild else "None"
            author_id = str(message.author.id)

            guild_data = self.cache.get_or_create_guild(guild_id)
            user = self.cache.get_or_create_user(guild_id, author_id, str(message.author.display_name))

            fields = message.content.lower().split(" ")
            command = fields[0]

            await self._dispatch_command(command, message, guild_data, user, fields)
        except Exception as ex:
            logging.exception(ex)
        finally:
            self._save_cache()

    async def _dispatch_command(
        self,
        command: str,
        message: Message,
        guild_data: GuildData,
        user: User,
        fields: list[str],
    ) -> None:
        """Dispatch command to the appropriate handler."""
        handler_name = self._COMMANDS.get(command)
        if handler_name is None:
            return

        handler_obj = self._handlers.get(handler_name)
        method_name = self._COMMAND_HANDLERS.get(handler_name)
        if handler_obj and method_name:
            handler = getattr(handler_obj, method_name)
            await handler(message, guild_data, user, fields)


def create_client() -> DNDRollerClient:
    """Create and configure the Discord client."""
    intents = discord.Intents.default()
    intents.message_content = True
    return DNDRollerClient(intents)


def run_bot() -> None:
    """Run the Discord bot."""
    client = create_client()
    token = config["Discord"]["Token"]
    client.run(token)
