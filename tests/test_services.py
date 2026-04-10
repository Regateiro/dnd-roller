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

    def test_get_skill_stat_non_mapped(self) -> None:
        """Test get_skill_stat with non-mapped skill returns default."""
        result = self.service.get_skill_stat("unknown_skill")
        assert result == "wis"  # Default fallback

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


class TestResolveReferencesComprehensive:
    """Comprehensive tests for resolve_references method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = RollService()
        self.character = Character(
            level=5,
            stats={
                Stat.STRENGTH: 16,
                Stat.DEXTERITY: 14,
                Stat.CONSTITUTION: 14,
                Stat.INTELLIGENCE: 10,
                Stat.WISDOM: 12,
                Stat.CHARISMA: 8,
            },
            save_prof=[Stat.STRENGTH],
            skill_prof=["athletics"],
            skill_expertise=["perception"],
        )

    @pytest.mark.asyncio
    async def test_resolve_all_stats(self) -> None:
        """Test resolving all stat score references."""
        for stat in ["str", "dex", "con", "int", "wis", "cha"]:
            result = await self.service.resolve_references(self.character, f"${stat}")
            expected = {"str": "16", "dex": "14", "con": "14", "int": "10", "wis": "12", "cha": "8"}
            assert result == expected[stat], f"Failed for stat {stat}"

    @pytest.mark.asyncio
    async def test_resolve_all_stat_mods(self) -> None:
        """Test resolving all stat modifier references."""
        for stat in ["str", "dex", "con", "int", "wis", "cha"]:
            result = await self.service.resolve_references(self.character, f"${stat}_mod")
            expected = {"str": "3", "dex": "2", "con": "2", "int": "0", "wis": "1", "cha": "-1"}
            assert result == expected[stat], f"Failed for stat {stat}"

    @pytest.mark.asyncio
    async def test_resolve_multiple_references(self) -> None:
        """Test resolving multiple references in one string."""
        result = await self.service.resolve_references(
            self.character, "Level $level, prof $prof, str $str, mod $str_mod"
        )
        assert result == "Level 5, prof 3, str 16, mod 3"

    @pytest.mark.asyncio
    async def test_resolve_skill_references(self) -> None:
        """Test resolving skill references."""
        result = await self.service.resolve_references(self.character, "$athletics")
        assert result == "6"  # str mod (3) + prof (3)

    @pytest.mark.asyncio
    async def test_resolve_user_variable_simple(self) -> None:
        """Test resolving user-created variable with simple value."""
        self.character.variables["rage"] = "2"
        result = await self.service.resolve_references(self.character, "$rage")
        assert result == "2"

    @pytest.mark.asyncio
    async def test_resolve_user_variable_dice(self) -> None:
        """Test resolving user-created variable with dice notation."""
        self.character.variables["bless"] = "1d4"
        result = await self.service.resolve_references(self.character, "$bless")
        assert result == "1d4"

    @pytest.mark.asyncio
    async def test_resolve_user_variable_with_reference(self) -> None:
        """Test resolving user-created variable with reference (not recursively resolved)."""
        self.character.variables["mod"] = "$str_mod"
        result = await self.service.resolve_references(self.character, "$mod")
        assert result == "$str_mod"  # Variables replaced but not recursively resolved

    @pytest.mark.asyncio
    async def test_resolve_user_variable_complex_expression(self) -> None:
        """Test resolving user-created variable with complex expression (not recursively resolved)."""
        self.character.variables["weapon_damage"] = "1d8+$str_mod"
        result = await self.service.resolve_references(self.character, "$weapon_damage")
        assert result == "1d8+$str_mod"  # Variables replaced but not recursively resolved

    @pytest.mark.asyncio
    async def test_resolve_mixed_references(self) -> None:
        """Test resolving mixed builtin and user references (direct, not via user variable)."""
        # Direct reference in string resolves all builtins
        result = await self.service.resolve_references(
            self.character, "Level $level, prof $prof, str $str, mod $str_mod"
        )
        assert result == "Level 5, prof 3, str 16, mod 3"

    @pytest.mark.asyncio
    async def test_resolve_user_variable_not_recursive(self) -> None:
        """Test that user variables are not recursively resolved."""
        # User variable containing $str_mod stays as-is because user variables
        # are resolved after the initial pass, so $str_mod inside a user variable
        # is not re-processed
        self.character.variables["attack_roll"] = "1d20+$str_mod+$prof"
        result = await self.service.resolve_references(self.character, "$attack_roll")
        assert result == "1d20+$str_mod+$prof"  # Not recursively resolved


class TestGetCharacterRollComprehensive:
    """Comprehensive tests for get_character_roll method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = RollService()
        self.character = Character(
            level=5,
            stats={
                Stat.STRENGTH: 16,
                Stat.DEXTERITY: 14,
                Stat.CONSTITUTION: 14,
                Stat.INTELLIGENCE: 10,
                Stat.WISDOM: 12,
                Stat.CHARISMA: 8,
            },
            save_prof=[Stat.STRENGTH],
            skill_prof=["athletics"],
            skill_expertise=["perception"],
        )

    @pytest.mark.asyncio
    async def test_roll_stat_all_abilities(self) -> None:
        """Test rolling all ability stats."""
        for stat in ["str", "dex", "con", "int", "wis", "cha"]:
            modifiers = RollModifiers()
            result = await self.service.get_character_roll(self.character, stat, modifiers)
            expected_mods = {"str": "3", "dex": "2", "con": "2", "int": "0", "wis": "1", "cha": "-1"}
            assert result == f"1d20+{expected_mods[stat]}", f"Failed for stat {stat}"

    @pytest.mark.asyncio
    async def test_roll_skill_with_proficiency(self) -> None:
        """Test rolling a proficient skill."""
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "athletics", modifiers)
        assert result == "1d20+3+3"  # str mod + prof

    @pytest.mark.asyncio
    async def test_roll_skill_with_expertise(self) -> None:
        """Test rolling an expertise skill."""
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "perception", modifiers)
        assert result == "1d20+1+6"  # wis mod + expertise (prof * 2 = 6)

    @pytest.mark.asyncio
    async def test_roll_save_proficient(self) -> None:
        """Test rolling a proficient saving throw."""
        modifiers = RollModifiers(save=True)
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "1d20+3+3"  # str mod + prof

    @pytest.mark.asyncio
    async def test_roll_save_non_proficient(self) -> None:
        """Test rolling a non-proficient saving throw."""
        modifiers = RollModifiers(save=True)
        result = await self.service.get_character_roll(self.character, "dex", modifiers)
        assert result == "1d20+2"  # dex mod only

    @pytest.mark.asyncio
    async def test_roll_macro_simple(self) -> None:
        """Test rolling a simple macro."""
        self.character.macros["sword"] = "1d8"
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "sword", modifiers)
        assert result == "1d8"

    @pytest.mark.asyncio
    async def test_roll_macro_with_reference(self) -> None:
        """Test rolling a macro with stat reference."""
        self.character.macros["attack"] = "1d8+$str_mod"
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "attack", modifiers)
        assert result == "1d8+3"

    @pytest.mark.asyncio
    async def test_roll_macro_with_prof_reference(self) -> None:
        """Test rolling a macro with proficiency reference."""
        self.character.macros["spell_attack"] = "1d20+$int_mod+$prof"
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "spell_attack", modifiers)
        assert result == "1d20+0+3"

    @pytest.mark.asyncio
    async def test_roll_macro_with_level_reference(self) -> None:
        """Test rolling a macro with level reference."""
        self.character.macros["mystic"] = "1d6+$level"
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "mystic", modifiers)
        assert result == "1d6+5"

    @pytest.mark.asyncio
    async def test_roll_macro_with_variable(self) -> None:
        """Test rolling a macro with variable reference."""
        self.character.variables["bless"] = "1d4"
        self.character.macros["blessed_attack"] = "1d20+$str_mod+$bless"
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "blessed_attack", modifiers)
        assert result == "1d20+3+1d4"

    @pytest.mark.asyncio
    async def test_roll_with_advantage(self) -> None:
        """Test rolling with advantage."""
        modifiers = RollModifiers(mode=RollMode.ADVANTAGE)
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "2d20kh1+3"

    @pytest.mark.asyncio
    async def test_roll_with_disadvantage(self) -> None:
        """Test rolling with disadvantage."""
        modifiers = RollModifiers(mode=RollMode.DISADVANTAGE)
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "2d20kl1+3"

    @pytest.mark.asyncio
    async def test_roll_with_triple_advantage(self) -> None:
        """Test rolling with triple advantage."""
        modifiers = RollModifiers(mode=RollMode.TRIPLE_ADVANTAGE)
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "3d20kh1+3"

    @pytest.mark.asyncio
    async def test_roll_with_crit(self) -> None:
        """Test rolling with crit (on a macro with weapon dice)."""
        self.character.macros["greatsword"] = "2d6"
        modifiers = RollModifiers(crit=True)
        result = await self.service.get_character_roll(self.character, "greatsword", modifiers)
        assert result == "4d6"

    @pytest.mark.asyncio
    async def test_roll_with_variable_modifier(self) -> None:
        """Test rolling with variable as modifier."""
        self.character.variables["bless"] = "1d4"
        modifiers = RollModifiers(vars=["bless"])
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "1d20+3+1d4"

    @pytest.mark.asyncio
    async def test_roll_with_multiple_variables(self) -> None:
        """Test rolling with multiple variable modifiers."""
        self.character.variables["bless"] = "1d4"
        self.character.variables["rage"] = "2"
        modifiers = RollModifiers(vars=["bless", "rage"])
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "1d20+3+1d4+2"

    @pytest.mark.asyncio
    async def test_roll_with_ability_bonus(self) -> None:
        """Test rolling with ability bonus."""
        self.character.ability_bonus = 2
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "1d20+3+2"

    @pytest.mark.asyncio
    async def test_roll_with_skill_bonus(self) -> None:
        """Test rolling with skill bonus."""
        self.character.skill_bonus = 1
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "athletics", modifiers)
        assert result == "1d20+3+3+1"

    @pytest.mark.asyncio
    async def test_roll_advantage_on_skill(self) -> None:
        """Test rolling skill with advantage."""
        modifiers = RollModifiers(mode=RollMode.ADVANTAGE)
        result = await self.service.get_character_roll(self.character, "athletics", modifiers)
        assert result == "2d20kh1+3+3"

    @pytest.mark.asyncio
    async def test_roll_save_with_advantage(self) -> None:
        """Test rolling saving throw with advantage."""
        modifiers = RollModifiers(save=True, mode=RollMode.ADVANTAGE)
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "2d20kh1+3+3"

    @pytest.mark.asyncio
    async def test_roll_with_character_advantage(self) -> None:
        """Test rolling with character-configured advantage."""
        self.character.advantage.append("str")
        modifiers = RollModifiers()
        result = await self.service.get_character_roll(self.character, "str", modifiers)
        assert result == "2d20kh1+3"


class TestParseModifiersComprehensive:
    """Comprehensive tests for parse_modifiers method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = RollService()
        self.character = Character(
            level=5,
            stats={s: 10 for s in Stat},
            save_prof=[],
            skill_prof=[],
        )

    def test_parse_multiple_modifiers(self) -> None:
        """Test parsing multiple modifiers at once."""
        self.character.variables["bless"] = "1d4"
        fields = ["save", "crit", "adv", "bless"]
        result = self.service.parse_modifiers(fields, self.character)
        assert result.save is True
        assert result.crit is True
        assert result.mode == RollMode.ADVANTAGE
        assert "bless" in result.vars

    def test_parse_disadvantage_variant(self) -> None:
        """Test parsing disadvantage variants."""
        for variant in ["dis", "disadvantage"]:
            fields = [variant]
            result = self.service.parse_modifiers(fields, self.character)
            assert result.mode == RollMode.DISADVANTAGE

    def test_parse_advantage_variants(self) -> None:
        """Test parsing advantage variants."""
        for variant in ["a", "adv", "advantage"]:
            fields = [variant]
            result = self.service.parse_modifiers(fields, self.character)
            assert result.mode == RollMode.ADVANTAGE

    def test_parse_triple_advantage_variants(self) -> None:
        """Test parsing triple advantage variants."""
        for variant in ["ta", "tadv", "tadvantage"]:
            fields = [variant]
            result = self.service.parse_modifiers(fields, self.character)
            assert result.mode == RollMode.TRIPLE_ADVANTAGE

    def test_parse_crit_variants(self) -> None:
        """Test parsing crit variants."""
        for variant in ["crit", "critical"]:
            fields = [variant]
            result = self.service.parse_modifiers(fields, self.character)
            assert result.crit is True


class TestGenerateSummaryComprehensive:
    """Comprehensive tests for generate_summary method."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.service = RollService()

    def test_summary_skill_with_underscore(self) -> None:
        """Test generating summary for skill with underscore."""
        modifiers = RollModifiers()
        result = self.service.generate_summary("Grog", "sleight_of_hand", modifiers, {})
        assert "sleight of hand" in result

    def test_summary_macro_with_vars(self) -> None:
        """Test generating summary with variables."""
        modifiers = RollModifiers(vars=["bless", "rage"])
        result = self.service.generate_summary("Grog", "str", modifiers, {})
        assert "bless" in result
        assert "rage" in result

    def test_summary_triple_advantage(self) -> None:
        """Test generating summary with triple advantage."""
        modifiers = RollModifiers(mode=RollMode.TRIPLE_ADVANTAGE)
        result = self.service.generate_summary("Grog", "str", modifiers, {})
        assert "triple advantage" in result

    def test_summary_macro_non_stat_skill(self) -> None:
        """Test generating summary for macro (not stat or skill)."""
        modifiers = RollModifiers()
        result = self.service.generate_summary("Grog", "fireball", modifiers, {"fireball": "8d6"})
        # fireball is not in stats or skills, so it goes to else branch
        assert "fireball" in result
