"""Data models for the D&D Roller bot."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
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


class ProficiencyLevel(str, Enum):
    """Proficiency level for skills."""

    NONE = ""
    HALF = "◐"
    PROFICIENT = "✓"
    EXPERTISE = "✓✓"


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

STAT_FULL_NAMES: dict[Stat, str] = {
    Stat.STRENGTH: "strength",
    Stat.DEXTERITY: "dexterity",
    Stat.CONSTITUTION: "constitution",
    Stat.INTELLIGENCE: "intelligence",
    Stat.WISDOM: "wisdom",
    Stat.CHARISMA: "charisma",
}

STAT_SHORT_NAMES: dict[str, str] = {v: k for k, v in STAT_FULL_NAMES.items()}


@dataclass
class Character:
    """Represents a D&D character with stats, proficiencies, and custom data."""

    level: int
    stats: dict[Stat, int]
    save_prof: list[Stat] = field(default_factory=list)
    skill_prof: list[str] = field(default_factory=list)
    skill_expertise: list[str] = field(default_factory=list)
    skill_half: list[str] = field(default_factory=list)
    advantage: list[str] = field(default_factory=list)
    ability_bonus: int = 0
    skill_bonus: int = 0
    jack_of_all_trades: bool = False
    macros: dict[str, str] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)

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
        return Character(level=-7, stats={s: 10 for s in Stat})

    def get_stat_mod(self, stat: Stat) -> int:
        """Calculate the modifier for an ability score (floor((score-10)/2))."""
        return math.floor(self.stats[stat] / 2) - 5

    def get_prof_mod(self) -> int:
        """Calculate the proficiency bonus based on character level."""
        return math.floor((self.level - 1) / 4) + 2

    def get_skill_mod(self, skill: str) -> tuple[int, ProficiencyLevel]:
        """Calculate the modifier and proficiency level for a skill."""
        stat = SKILL_TO_STAT.get(skill)
        if not stat:
            return 0, ProficiencyLevel.NONE

        base_mod = self.get_stat_mod(stat)

        if skill in self.skill_expertise:
            return base_mod + self.get_prof_mod() * 2, ProficiencyLevel.EXPERTISE

        if skill in self.skill_prof:
            return base_mod + self.get_prof_mod(), ProficiencyLevel.PROFICIENT

        if skill in self.skill_half:
            return base_mod + math.floor(self.get_prof_mod() * 0.5), ProficiencyLevel.HALF

        if self.jack_of_all_trades:
            return base_mod + math.floor(self.get_prof_mod() * 0.5), ProficiencyLevel.HALF

        return base_mod, ProficiencyLevel.NONE

    def is_save_proficient(self, stat: Stat) -> bool:
        """Check if the character is proficient in a saving throw for this stat."""
        return stat in self.save_prof

    def clear_proficiencies(self) -> None:
        """Clear all proficiency lists."""
        self.save_prof.clear()
        self.skill_prof.clear()
        self.skill_expertise.clear()
        self.skill_half.clear()
        self.advantage.clear()


@dataclass
class User:
    """Represents a Discord user with their D&D characters."""

    name: str
    characters: dict[str, Character] = field(default_factory=dict)
    active: str = ""
    unavailability: list[str] = field(default_factory=list)

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


@dataclass
class Session:
    """Represents scheduled D&D sessions for a Discord guild."""

    on: list[str] = field(default_factory=list)
    off: list[str] = field(default_factory=list)
    wday: int = -1

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


@dataclass
class GuildData:
    """Represents all data associated with a Discord guild (server)."""

    users: dict[str, User] = field(default_factory=dict)
    sessions: Session = field(default_factory=Session)

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


@dataclass
class Cache:
    """Root cache object containing data for all guilds."""

    data: dict[str, GuildData] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Cache:
        return cls(data={k: GuildData.from_dict(v) for k, v in data.items()})

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
