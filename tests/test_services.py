"""Unit tests for the roll service."""

from __future__ import annotations

import pytest

from bot.commands import RollMode
from bot.models import Character, Stat
from bot.services.roll import RollModifiers, RollService


class TestRollService:
    """Tests for the RollService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = RollService()
        self.character = Character(
            level=5,
            stats={Stat.STRENGTH: 16, Stat.DEXTERITY: 14, Stat.CONSTITUTION: 14, Stat.INTELLIGENCE: 10, Stat.WISDOM: 12, Stat.CHARISMA: 8},
            save_prof=[Stat.STRENGTH],
            skill_prof=["athletics"],
            skill_expertise=["perception"],
        )

    @pytest.mark.asyncio
    async def test_resolve_references_level(self) -> None:
        """Test resolving $level reference."""
        result = await self.service.resolve_references(self.character, "check $level")
        assert result == "check 5"

    @pytest.mark.asyncio
    async def test_resolve_references_prof(self) -> None:
        """Test resolving $prof reference."""
        result = await self.service.resolve_references(self.character, "check $prof")
        assert result == "check 3"

    @pytest.mark.asyncio
    async def test_resolve_references_stat(self) -> None:
        """Test resolving $str_stat and $str reference."""
        result1 = await self.service.resolve_references(self.character, "$str_mod+1")
        result2 = await self.service.resolve_references(self.character, "$str+1")
        assert result1 == "3+1"  # (16/2) - 5 = 3
        assert result2 == "16+1"

    @pytest.mark.asyncio
    async def test_resolve_references_skill(self) -> None:
        """Test resolving $skill reference."""
        result = await self.service.resolve_references(self.character, "$athletics")
        assert result == "6"  # str mod (3) + prof (3) = 6

    @pytest.mark.asyncio
    async def test_resolve_references_variable(self) -> None:
        """Test resolving variable reference."""
        self.character.variables["bonus"] = "2"
        result = await self.service.resolve_references(self.character, "$bonus")
        assert result == "2"

    @pytest.mark.asyncio
    async def test_get_character_roll_stat(self) -> None:
        """Test generating character roll for ability stat."""
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "1d20+3"  # str mod

    @pytest.mark.asyncio
    async def test_get_character_roll_stat_save(self) -> None:
        """Test generating character roll for saving throw."""
        modifiers = RollModifiers(save=True)
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "1d20+3+3"  # str mod + prof

    @pytest.mark.asyncio
    async def test_get_character_roll_skill(self) -> None:
        """Test generating character roll for skill."""
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "athletics", modifiers)
        assert result == "1d20+3+3"  # str mod (3) + prof (3) = 6

    @pytest.mark.asyncio
    async def test_get_character_roll_skill_expertise(self) -> None:
        """Test generating character roll for expertise skill."""
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "perception", modifiers)
        assert result == "1d20+1+6"  # wis mod (1) + expertise (6) = 7

    @pytest.mark.asyncio
    async def test_get_character_roll_with_ability_bonus(self) -> None:
        """Test generating character roll with ability bonus."""
        self.character.ability_bonus = 2
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "1d20+3+2"

    @pytest.mark.asyncio
    async def test_get_character_roll_with_skill_bonus(self) -> None:
        """Test generating character roll with skill bonus."""
        self.character.skill_bonus = 1
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "athletics", modifiers)
        assert result == "1d20+3+3+1"

    @pytest.mark.asyncio
    async def test_get_character_roll_macro(self) -> None:
        """Test generating character roll from macro."""
        self.character.macros["attack"] = "1d8+$str_mod"
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "attack", modifiers)
        assert result == "1d8+3"  # 1d8 + str mod (3)

    @pytest.mark.asyncio
    async def test_generate_summary_stat(self) -> None:
        """Test generating summary for stat roll."""
        modifiers = RollModifiers(save=True)
        result = self.service.generate_summary("Grog", "str", modifiers, {})
        assert result == "Grog rolled for a(n) strength save"

    @pytest.mark.asyncio
    async def test_generate_summary_skill(self) -> None:
        """Test generating summary for skill roll."""
        modifiers = RollModifiers()
        result = self.service.generate_summary("Grog", "athletics", modifiers, {})
        assert result == "Grog rolled for a(n) athletics check"

    @pytest.mark.asyncio
    async def test_generate_summary_macro(self) -> None:
        """Test generating summary for macro roll."""
        modifiers = RollModifiers()
        result = self.service.generate_summary("Grog", "attack", modifiers, {"attack": "1d8"})
        assert result == "Grog rolled using the macro attack"

    @pytest.mark.asyncio
    async def test_generate_summary_advantage(self) -> None:
        """Test generating summary with advantage."""
        modifiers = RollModifiers(mode=RollMode.ADVANTAGE)
        result = self.service.generate_summary("Grog", "str", modifiers, {})
        assert result == "Grog rolled for a(n) strength check with advantage"

    @pytest.mark.asyncio
    async def test_generate_summary_disadvantage(self) -> None:
        """Test generating summary with disadvantage."""
        modifiers = RollModifiers(mode=RollMode.DISADVANTAGE)
        result = self.service.generate_summary("Grog", "str", modifiers, {})
        assert result == "Grog rolled for a(n) strength check with disadvantage"

    @pytest.mark.asyncio
    async def test_generate_summary_variables(self) -> None:
        """Test generating summary with variables."""
        modifiers = RollModifiers(vars=["bonus"])
        result = self.service.generate_summary("Grog", "str", modifiers, {})
        assert result == "Grog rolled for a(n) strength check with bonus"

    def test_parse_modifiers_basic(self) -> None:
        """Test parsing basic modifiers."""
        fields = ["save"]
        result = self.service.parse_modifiers(fields, self.character)
        assert result.save is True
        assert result.mode == RollMode.NORMAL

    def test_parse_modifiers_crit(self) -> None:
        """Test parsing crit modifier."""
        fields = ["crit"]
        result = self.service.parse_modifiers(fields, self.character)
        assert result.crit is True

    def test_parse_modifiers_advantage(self) -> None:
        """Test parsing advantage modifier."""
        fields = ["advantage"]
        result = self.service.parse_modifiers(fields, self.character)
        assert result.mode == RollMode.ADVANTAGE

    def test_parse_modifiers_disadvantage(self) -> None:
        """Test parsing disadvantage modifier."""
        fields = ["dis"]
        result = self.service.parse_modifiers(fields, self.character)
        assert result.mode == RollMode.DISADVANTAGE

    def test_parse_modifiers_triple_advantage(self) -> None:
        """Test parsing triple advantage modifier."""
        fields = ["ta"]
        result = self.service.parse_modifiers(fields, self.character)
        assert result.mode == RollMode.TRIPLE_ADVANTAGE

    def test_parse_modifiers_variable(self) -> None:
        """Test parsing variable modifier."""
        self.character.variables["bless"] = "1d4"
        fields = ["bless"]
        result = self.service.parse_modifiers(fields, self.character)
        assert "bless" in result.vars

    def test_get_skill_stat(self) -> None:
        """Test getting ability stat for skill."""
        assert self.service.get_skill_stat("arcana") == "int"
        assert self.service.get_skill_stat("athletics") == "str"
        assert self.service.get_skill_stat("persuasion") == "cha"

    def test_is_ability_stat(self) -> None:
        """Test checking if string is ability stat."""
        assert self.service.is_ability_stat("int") is True
        assert self.service.is_ability_stat("strength") is True
        assert self.service.is_ability_stat("athletics") is False


class TestRollModifiers:
    """Tests for the RollModifiers dataclass."""

    def test_default_values(self) -> None:
        """Test default modifier values."""
        modifiers = RollModifiers()
        assert modifiers.mode == RollMode.NORMAL
        assert modifiers.save is False
        assert modifiers.crit is False
        assert modifiers.vars == []

    def test_with_mode(self) -> None:
        """Test RollModifiers with mode."""
        modifiers = RollModifiers(mode=RollMode.ADVANTAGE)
        assert modifiers.mode == RollMode.ADVANTAGE

    def test_with_save(self) -> None:
        """Test RollModifiers with save."""
        modifiers = RollModifiers(save=True)
        assert modifiers.save is True

    def test_with_crit(self) -> None:
        """Test RollModifiers with crit."""
        modifiers = RollModifiers(crit=True)
        assert modifiers.crit is True

    def test_with_vars(self) -> None:
        """Test RollModifiers with vars."""
        modifiers = RollModifiers(vars=["bonus", "bless"])
        assert modifiers.vars == ["bonus", "bless"]
