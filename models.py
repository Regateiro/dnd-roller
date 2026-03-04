"""Data models for the D&D Roller bot."""

from __future__ import annotations

import math
from enum import Enum
from typing import Any


class Stat(str, Enum):
    """Enum representing the six ability scores in D&D."""

    STRENGTH = "str"
    DEXTERITY = "dex"
    CONSTITUTION = "con"
    INTELLIGENCE = "int"
    WISDOM = "wis"
    CHARISMA = "cha"

    @classmethod
    def all(cls) -> list[str]:
        """Return all stat values as a list of strings."""
        return [s.value for s in cls]


# List of all skills in D&D 5e
SKILLS = [
    "acrobatics",
    "animal_handling",
    "arcana",
    "athletics",
    "deception",
    "history",
    "insight",
    "intimidation",
    "investigation",
    "medicine",
    "nature",
    "perception",
    "performance",
    "persuasion",
    "religion",
    "sleight_of_hand",
    "stealth",
    "survival",
]

# Mapping of each skill to its associated ability score
SKILL_TO_STAT: dict[str, Stat] = {
    "acrobatics": Stat.DEXTERITY,
    "animal_handling": Stat.WISDOM,
    "arcana": Stat.INTELLIGENCE,
    "athletics": Stat.STRENGTH,
    "deception": Stat.CHARISMA,
    "history": Stat.INTELLIGENCE,
    "insight": Stat.WISDOM,
    "intimidation": Stat.CHARISMA,
    "investigation": Stat.INTELLIGENCE,
    "medicine": Stat.WISDOM,
    "nature": Stat.INTELLIGENCE,
    "perception": Stat.WISDOM,
    "performance": Stat.CHARISMA,
    "persuasion": Stat.CHARISMA,
    "religion": Stat.INTELLIGENCE,
    "sleight_of_hand": Stat.DEXTERITY,
    "stealth": Stat.DEXTERITY,
    "survival": Stat.WISDOM,
}

# Full names for stats (e.g., "str" -> "strength")
STAT_FULL_NAMES: dict[Stat, str] = {
    Stat.STRENGTH: "strength",
    Stat.DEXTERITY: "dexterity",
    Stat.CONSTITUTION: "constitution",
    Stat.INTELLIGENCE: "intelligence",
    Stat.WISDOM: "wisdom",
    Stat.CHARISMA: "charisma",
}

# Reverse mapping (e.g., "strength" -> "str")
STAT_SHORT_NAMES: dict[str, str] = {v: k for k, v in STAT_FULL_NAMES.items()}


class Character:
    """Represents a D&D character with stats, proficiencies, and custom data."""

    __slots__ = (
        "level",
        "stats",
        "save_prof",
        "skill_prof",
        "skill_expertise",
        "skill_half",
        "advantage",
        "ability_bonus",
        "skill_bonus",
        "jack_of_all_trades",
        "macros",
        "variables",
    )

    def __init__(
        self,
        level: int,
        stats: dict[Stat, int],
        save_prof: list[Stat] | None = None,
        skill_prof: list[str] | None = None,
        skill_expertise: list[str] | None = None,
        skill_half: list[str] | None = None,
        advantage: list[str] | None = None,
        ability_bonus: int = 0,
        skill_bonus: int = 0,
        jack_of_all_trades: bool = False,
        macros: dict[str, str] | None = None,
        variables: dict[str, str] | None = None,
    ):
        self.level = level
        self.stats = stats
        self.save_prof = save_prof or []
        self.skill_prof = skill_prof or []
        self.skill_expertise = skill_expertise or []
        self.skill_half = skill_half or []
        self.advantage = advantage or []
        self.ability_bonus = ability_bonus
        self.skill_bonus = skill_bonus
        self.jack_of_all_trades = jack_of_all_trades
        self.macros = macros or {}
        self.variables = variables or {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Character:
        """Create a Character from a dictionary (for JSON deserialization)."""
        return cls(
            level=data["level"],
            stats={Stat(k): v for k, v in data["stats"].items()},
            save_prof=[Stat(s) for s in data.get("save_prof", [])],
            skill_prof=data.get("skill_prof", []),
            skill_expertise=data.get("skill_expertise", []),
            skill_half=data.get("skill_half", []),
            advantage=data.get("advantage", []),
            ability_bonus=data.get("ability_bonus", 0),
            skill_bonus=data.get("skill_bonus", 0),
            jack_of_all_trades=data.get("jack_of_all_trades", False),
            macros=data.get("macros", {}),
            variables=data.get("variables", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the Character to a dictionary (for JSON serialization)."""
        return {
            "level": self.level,
            "stats": {k.value: v for k, v in self.stats.items()},
            "save_prof": [s.value for s in self.save_prof],
            "skill_prof": self.skill_prof,
            "skill_expertise": self.skill_expertise,
            "skill_half": self.skill_half,
            "advantage": self.advantage,
            "ability_bonus": self.ability_bonus,
            "skill_bonus": self.skill_bonus,
            "jack_of_all_trades": self.jack_of_all_trades,
            "macros": self.macros,
            "variables": self.variables,
        }

    @staticmethod
    def empty() -> Character:
        """Create a default character template (level -7 gives 0 proficiency bonus)."""
        return Character(
            level=-7,
            stats={s: 10 for s in Stat},
        )

    def get_stat_mod(self, stat: Stat) -> int:
        """Calculate the modifier for an ability score (floor((score-10)/2))."""
        return math.floor(self.stats[stat] / 2) - 5

    def get_prof_mod(self) -> int:
        """Calculate the proficiency bonus based on character level."""
        return math.floor((self.level - 1) / 4) + 2

    def get_skill_mod(self, skill: str) -> tuple[int, str]:
        """Calculate the modifier and proficiency indicator for a skill.

        Returns:
            A tuple of (modifier, proficiency_indicator) where indicator
            shows proficiency level (✓ = proficient, ✓✓ = expertise, ◐ = half, empty = none).
        """
        stat = SKILL_TO_STAT.get(skill)
        if not stat:
            return 0, ""

        base_mod = self.get_stat_mod(stat)

        if skill in self.skill_expertise:
            return base_mod + self.get_prof_mod() * 2, "✓✓"

        if skill in self.skill_prof:
            return base_mod + self.get_prof_mod(), "✓"

        if skill in self.skill_half:
            return base_mod + math.floor(self.get_prof_mod() * 0.5), "◐"

        if self.jack_of_all_trades:
            return base_mod + math.floor(self.get_prof_mod() * 0.5), "◐"

        return base_mod, ""

    def is_save_proficient(self, stat: Stat) -> bool:
        """Check if the character is proficient in a saving throw for this stat."""
        return stat in self.save_prof

    # Dict-like access methods for backward compatibility with JSON-based code
    def __getitem__(self, key: str) -> Any:
        return self.to_dict().__getitem__(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "level":
            self.level = value
        elif key == "stats":
            self.stats = {Stat(k): v for k, v in value.items()}
        elif key == "save_prof":
            self.save_prof = [Stat(s) for s in value]
        elif key == "skill_prof":
            self.skill_prof = value
        elif key == "skill_expertise":
            self.skill_expertise = value
        elif key == "skill_half":
            self.skill_half = value
        elif key == "advantage":
            self.advantage = value
        elif key == "ability_bonus":
            self.ability_bonus = value
        elif key == "skill_bonus":
            self.skill_bonus = value
        elif key == "jack_of_all_trades":
            self.jack_of_all_trades = value
        elif key == "macros":
            self.macros = value
        elif key == "variables":
            self.variables = value

    def keys(self):
        return self.to_dict().keys()

    def values(self):
        return self.to_dict().values()

    def items(self):
        return self.to_dict().items()

    def get(self, key: str, default=None):
        return self.to_dict().get(key, default)

    def pop(self, key: str, *args):
        return self.to_dict().pop(key, *args)

    def clear(self) -> None:
        self.save_prof.clear()
        self.skill_prof.clear()
        self.skill_expertise.clear()
        self.skill_half.clear()
        self.advantage.clear()

    def append(self, item: Any) -> None:
        pass


class User:
    """Represents a Discord user with their D&D characters."""

    __slots__ = ("name", "characters", "active", "unavailability")

    def __init__(
        self,
        name: str,
        characters: dict[str, Character] | None = None,
        active: str = "",
        unavailability: list[str] | None = None,
    ):
        self.name = name
        self.characters = characters or {}
        self.active = active
        self.unavailability = unavailability or []

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        return cls(
            name=data["name"],
            characters={k: Character.from_dict(v) for k, v in data.get("characters", {}).items()},
            active=data.get("active", ""),
            unavailability=data.get("unavailability", []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "active": self.active,
            "unavailability": self.unavailability,
        }

    def __getitem__(self, key: str) -> Any:
        if key == "name":
            return self.name
        if key == "characters":
            return self.characters
        if key == "active":
            return self.active
        if key == "unavailability":
            return self.unavailability
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "name":
            self.name = value
        elif key == "characters":
            self.characters = value
        elif key == "active":
            self.active = value
        elif key == "unavailability":
            self.unavailability = value

    def keys(self):
        return ["name", "characters", "active", "unavailability"]

    def values(self):
        return [self.name, self.characters, self.active, self.unavailability]

    def items(self):
        return [("name", self.name), ("characters", self.characters), ("active", self.active), ("unavailability", self.unavailability)]

    def get(self, key: str, default=None):
        if key in ("name", "characters", "active", "unavailability"):
            return getattr(self, key)
        return default

    def setdefault(self, key: str, default=None):
        if key not in ("name", "characters", "active", "unavailability"):
            return default
        if getattr(self, key, None) is None:
            setattr(self, key, default)
        return getattr(self, key)


class Session:
    """Represents scheduled D&D sessions for a Discord guild.

    Attributes:
        on: List of dates (YYYY-MM-DD) with extra sessions scheduled.
        off: List of dates (YYYY-MM-DD) where regular sessions are cancelled.
        wday: Default day of the week for regular sessions (0=Monday, 6=Sunday).
    """

    __slots__ = ("on", "off", "wday")

    def __init__(self, on: list[str] | None = None, off: list[str] | None = None, wday: int = -1):
        self.on = on or []
        self.off = off or []
        self.wday = wday

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        return cls(
            on=data.get("on", []),
            off=data.get("off", []),
            wday=data.get("wday", -1),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "on": self.on,
            "off": self.off,
            "wday": self.wday,
        }

    def __getitem__(self, key: str) -> Any:
        if key == "on":
            return self.on
        if key == "off":
            return self.off
        if key == "wday":
            return self.wday
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "on":
            self.on = value
        elif key == "off":
            self.off = value
        elif key == "wday":
            self.wday = value

    def get(self, key: str, default=None):
        if key in ("on", "off", "wday"):
            return getattr(self, key)
        return default

    def setdefault(self, key: str, default=None):
        if key not in ("on", "off", "wday"):
            return default
        if getattr(self, key, None) is None:
            setattr(self, key, default)
        return getattr(self, key)


class GuildData:
    """Represents all data associated with a Discord guild (server)."""

    __slots__ = ("users", "sessions")

    def __init__(self, users: dict[str, User] | None = None, sessions: Session | None = None):
        self.users = users or {}
        self.sessions = sessions or Session()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GuildData:
        return cls(
            users={k: User.from_dict(v) for k, v in data.get("users", {}).items()},
            sessions=Session.from_dict(data.get("sessions", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "users": {k: v.to_dict() for k, v in self.users.items()},
            "sessions": self.sessions.to_dict(),
        }

    def __getitem__(self, key: str) -> Any:
        if key == "users":
            return self.users
        if key == "sessions":
            return self.sessions
        raise KeyError(key)

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "users":
            self.users = value
        elif key == "sessions":
            self.sessions = value

    def get(self, key: str, default=None):
        if key in ("users", "sessions"):
            return getattr(self, key)
        return default

    def setdefault(self, key: str, default=None):
        if key not in ("users", "sessions"):
            return default
        if getattr(self, key, None) is None:
            setattr(self, key, default)
        return getattr(self, key)


class Cache:
    """Root cache object containing data for all guilds.

    This is the top-level container that holds all bot data,
    organized by guild ID.
    """

    __slots__ = ("data",)

    def __init__(self, data: dict[str, GuildData] | None = None):
        self.data = data or {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Cache:
        return cls(
            data={k: GuildData.from_dict(v) for k, v in data.items()},
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self.data.items()}

    def get_or_create_guild(self, guild_id: str) -> GuildData:
        if guild_id not in self.data:
            self.data[guild_id] = GuildData()
        return self.data[guild_id]

    def get_or_create_user(self, guild_id: str, user_id: str, name: str) -> User:
        guild = self.get_or_create_guild(guild_id)
        if user_id not in guild.users:
            guild.users[user_id] = User(name=name)
        return guild.users[user_id]

    def __getitem__(self, key: str) -> GuildData:
        return self.data[key]

    def __setitem__(self, key: str, value: GuildData) -> None:
        self.data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.data

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def setdefault(self, key: str, default=None):
        return self.data.setdefault(key, default)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()
