"""Dice rolling service for the D&D Roller bot."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from bot.commands import RollMode, get_roll_mode
from bot.models import (
    SKILL_TO_STAT,
    SKILLS,
    STAT_FULL_NAMES,
    STAT_SHORT_NAMES,
    Character,
    Stat,
)

logger = logging.getLogger(__name__)


@dataclass
class RollModifiers:
    """Modifiers applied to a roll."""

    mode: RollMode = RollMode.NORMAL
    save: bool = False
    crit: bool = False
    vars: list[str] = field(default_factory=list)


class RollService:
    """Service for resolving dice rolls and character roll expressions."""

    def __init__(self) -> None:
        self.stats: list[str] = Stat.all()
        self.skills: list[str] = SKILLS

    async def resolve_references(self, character: Character, value: str) -> str:
        """Resolve variable and stat references in a string."""
        value = value.replace("$level", str(character.level))
        value = value.replace("$prof", str(character.get_prof_mod()))

        for stat in self.stats:
            stat_enum = Stat(stat)
            value = value.replace(f"${stat}_mod", str(character.get_stat_mod(stat_enum)))
            value = value.replace(f"${stat}", str(character.stats[stat_enum]))

        logger.debug("after resolving stats: value=%s", value)
        for skill in self.skills:
            logger.debug("resolving skill reference: %s", skill)
            mod, _ = character.get_skill_mod(skill)
            value = value.replace(f"${skill}", str(mod))
        logger.debug("after resolving skill %s: value=%s", skill, value)

        for var in character.variables.keys():
            value = value.replace(f"${var}", str(character.variables[var]))

        return value

    async def get_character_roll(self, character: Character, target: str, modifiers: RollModifiers) -> str:
        """Generate a dice roll expression for a character."""
        stat_enum = Stat(target) if target in self.stats else SKILL_TO_STAT.get(target, Stat.WISDOM)

        if target in character.macros:
            roll = await self.resolve_references(character, character.macros[target])
        else:
            roll = "1d20"
            roll = f"{roll}+{character.get_stat_mod(stat_enum)}"

            if (modifiers.save and character.is_save_proficient(stat_enum)) or target in character.skill_prof:
                roll = f"{roll}+{character.get_prof_mod()}"

            if target in character.skill_expertise:
                roll = f"{roll}+{character.get_prof_mod() * 2}"

        if target in self.stats and character.ability_bonus != 0:
            roll = f"{roll}+{character.ability_bonus}"

        if target in self.skills and character.skill_bonus != 0:
            roll = f"{roll}+{character.skill_bonus}"

        for var in modifiers.vars:
            roll = f"{roll}+{await self.resolve_references(character, character.variables[var])}"

        if roll.startswith("1d20"):
            short_target = STAT_SHORT_NAMES.get(target, target)
            if modifiers.mode == RollMode.ADVANTAGE or short_target in character.advantage:
                roll = roll.replace("1d20", "2d20kh1", 1)
            elif modifiers.mode == RollMode.TRIPLE_ADVANTAGE:
                roll = roll.replace("1d20", "3d20kh1", 1)
            elif modifiers.mode == RollMode.DISADVANTAGE:
                roll = roll.replace("1d20", "2d20kl1", 1)

        if modifiers.crit:
            roll = re.sub(r"([0-9]+)d(4|6|8|10|12)", lambda x: f"{int(x.group(1))*2}d{x.group(2)}", roll)

        return roll

    def generate_summary(self, character: str, target: str, modifiers: RollModifiers, macros: dict[str, str]) -> str:
        """Generate a human-readable summary of a roll."""
        summary = f"{character.capitalize()} rolled"

        if target in macros:
            summary = f"{summary} using the macro {target}"
        elif target in self.stats:
            full_stat = STAT_FULL_NAMES.get(Stat(target), target)
            summary = f"{summary} for a(n) {full_stat}"
        elif target in self.skills:
            summary = f"{summary} for a(n) {target.replace('_', ' ')}"
        else:
            summary = f"{summary} {target}"

        if target in self.stats or target in self.skills:
            summary = f"{summary} {'save' if modifiers.save else 'check'}"

        mods_parts = []
        if modifiers.mode == RollMode.ADVANTAGE:
            mods_parts.append("advantage")
        elif modifiers.mode == RollMode.TRIPLE_ADVANTAGE:
            mods_parts.append("triple advantage")
        elif modifiers.mode == RollMode.DISADVANTAGE:
            mods_parts.append("disadvantage")

        mods_parts.extend(modifiers.vars)

        if mods_parts:
            summary = f"{summary} with {', '.join(mods_parts)}"

        return summary

    def parse_modifiers(self, fields: list[str], character: Character) -> RollModifiers:
        """Parse roll modifiers from command fields."""
        modifiers = RollModifiers()

        for f in fields:
            if f in ("save", "s"):
                modifiers.save = True
            elif f in ("crit", "critical"):
                modifiers.crit = True
            else:
                mode = get_roll_mode(f)
                if mode:
                    modifiers.mode = mode
                elif f in character.variables:
                    modifiers.vars.append(f)

        return modifiers

    def get_skill_stat(self, skill: str) -> str:
        """Get the ability stat associated with a skill."""
        skill_groups = {
            "int": ("int", "intelligence", "arcana", "history", "investigation", "nature", "religion"),
            "cha": ("cha", "charisma", "deception", "intimidation", "performance", "persuasion"),
            "dex": ("dex", "dexterity", "acrobatics", "sleight_of_hand", "stealth"),
            "str": ("str", "strength", "athletics"),
            "con": ("con", "constitution"),
        }
        for stat, skills in skill_groups.items():
            if skill in skills:
                return stat
        return "wis"

    def is_ability_stat(self, skill: str) -> bool:
        """Check if a string represents an ability stat."""
        ability_stats = {"int", "intelligence", "cha", "charisma", "dex", "dexterity", "str", "strength", "con", "constitution", "wis", "wisdom"}
        return skill in ability_stats
