"""Unit tests for the models module."""

from __future__ import annotations

from bot.models import (
    SKILL_TO_STAT,
    Cache,
    Character,
    GuildData,
    ProficiencyLevel,
    Session,
    Stat,
    User,
)


class TestStat:
    """Tests for the Stat enum."""

    def test_all_returns_all_stat_values(self) -> None:
        """Test that Stat.all() returns all six ability scores."""
        result = Stat.all()
        assert result == ["str", "dex", "con", "int", "wis", "cha"]


class TestCharacter:
    """Tests for the Character dataclass."""

    def test_empty_creates_default_character(self) -> None:
        """Test that Character.empty() creates a character with level -7 and 10 in all stats."""
        character = Character.empty()
        assert character.level == -7
        for stat in Stat:
            assert character.stats[stat] == 10

    def test_get_stat_mod_for_10(self) -> None:
        """Test modifier calculation for score of 10."""
        character = Character.empty()
        assert character.get_stat_mod(Stat.STRENGTH) == 0

    def test_get_stat_mod_for_12(self) -> None:
        """Test modifier calculation for score of 12."""
        character = Character(level=1, stats={s: 10 for s in Stat})
        character.stats[Stat.STRENGTH] = 12
        assert character.get_stat_mod(Stat.STRENGTH) == 1

    def test_get_stat_mod_for_8(self) -> None:
        """Test modifier calculation for score of 8."""
        character = Character(level=1, stats={s: 10 for s in Stat})
        character.stats[Stat.STRENGTH] = 8
        assert character.get_stat_mod(Stat.STRENGTH) == -1

    def test_get_prof_mod_for_level_1(self) -> None:
        """Test proficiency bonus for level 1."""
        character = Character(level=1, stats={s: 10 for s in Stat})
        assert character.get_prof_mod() == 2

    def test_get_prof_mod_for_level_5(self) -> None:
        """Test proficiency bonus for level 5."""
        character = Character(level=5, stats={s: 10 for s in Stat})
        assert character.get_prof_mod() == 3

    def test_get_prof_mod_for_level_9(self) -> None:
        """Test proficiency bonus for level 9."""
        character = Character(level=9, stats={s: 10 for s in Stat})
        assert character.get_prof_mod() == 4

    def test_get_prof_mod_for_level_17(self) -> None:
        """Test proficiency bonus for level 17."""
        character = Character(level=17, stats={s: 10 for s in Stat})
        assert character.get_prof_mod() == 6

    def test_get_skill_mod_unproficient(self) -> None:
        """Test skill modifier for unproficient skill."""
        character = Character(level=1, stats={s: 10 for s in Stat})
        mod, level = character.get_skill_mod("athletics")
        assert mod == 0
        assert level == ProficiencyLevel.NONE

    def test_get_skill_mod_proficient(self) -> None:
        """Test skill modifier for proficient skill."""
        character = Character(
            level=1,
            stats={s: 10 for s in Stat},
            skill_prof=["athletics"],
        )
        mod, level = character.get_skill_mod("athletics")
        assert mod == 2
        assert level == ProficiencyLevel.PROFICIENT

    def test_get_skill_mod_expertise(self) -> None:
        """Test skill modifier for expertise."""
        character = Character(
            level=1,
            stats={s: 10 for s in Stat},
            skill_expertise=["athletics"],
        )
        mod, level = character.get_skill_mod("athletics")
        assert mod == 4
        assert level == ProficiencyLevel.EXPERTISE

    def test_get_skill_mod_half(self) -> None:
        """Test skill modifier for half proficiency (Jack of All Trades)."""
        character = Character(
            level=1,
            stats={s: 10 for s in Stat},
            jack_of_all_trades=True,
        )
        mod, level = character.get_skill_mod("athletics")
        assert mod == 1
        assert level == ProficiencyLevel.HALF

    def test_get_skill_mod_skill_half(self) -> None:
        """Test skill modifier for skill_half list."""
        character = Character(
            level=1,
            stats={s: 10 for s in Stat},
            skill_half=["athletics"],
        )
        mod, level = character.get_skill_mod("athletics")
        assert mod == 1
        assert level == ProficiencyLevel.HALF

    def test_get_skill_mod_unknown(self) -> None:
        """Test skill modifier for unknown skill returns 0."""
        character = Character.empty()
        mod, level = character.get_skill_mod("unknown_skill")
        assert mod == 0
        assert level == ProficiencyLevel.NONE

    def test_is_save_proficient(self) -> None:
        """Test saving throw proficiency check."""
        character = Character(
            level=1,
            stats={s: 10 for s in Stat},
            save_prof=[Stat.STRENGTH],
        )
        assert character.is_save_proficient(Stat.STRENGTH) is True
        assert character.is_save_proficient(Stat.DEXTERITY) is False

    def test_clear_proficiencies(self) -> None:
        """Test clearing all proficiency lists."""
        character = Character(
            level=1,
            stats={s: 10 for s in Stat},
            save_prof=[Stat.STRENGTH],
            skill_prof=["athletics"],
            skill_expertise=["perception"],
            skill_half=["acrobatics"],
            advantage=["strength"],
        )
        character.clear_proficiencies()
        assert character.save_prof == []
        assert character.skill_prof == []
        assert character.skill_expertise == []
        assert character.skill_half == []
        assert character.advantage == []

    def test_from_dict(self) -> None:
        """Test deserialization from dictionary."""
        data = {
            "level": 5,
            "stats": {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 8},
            "save_prof": ["str", "dex"],
            "skill_prof": ["athletics", "acrobatics"],
            "skill_expertise": ["perception"],
            "skill_half": [],
            "advantage": [],
            "ability_bonus": 0,
            "skill_bonus": 0,
            "jack_of_all_trades": False,
            "macros": {},
            "variables": {},
        }
        character = Character.from_dict(data)
        assert character.level == 5
        assert character.stats[Stat.STRENGTH] == 16
        assert character.save_prof == [Stat.STRENGTH, Stat.DEXTERITY]
        assert character.skill_prof == ["athletics", "acrobatics"]
        assert character.skill_expertise == ["perception"]

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        character = Character(
            level=5,
            stats={Stat.STRENGTH: 16, Stat.DEXTERITY: 14, Stat.CONSTITUTION: 14, Stat.INTELLIGENCE: 10, Stat.WISDOM: 12, Stat.CHARISMA: 8},
            save_prof=[Stat.STRENGTH, Stat.DEXTERITY],
            skill_prof=["athletics", "acrobatics"],
        )
        result = character.to_dict()
        assert result["level"] == 5
        assert result["stats"]["str"] == 16
        assert result["save_prof"] == ["str", "dex"]
        assert result["skill_prof"] == ["athletics", "acrobatics"]


class TestSkillToStat:
    """Tests for SKILL_TO_STAT mapping."""

    def test_athletics_maps_to_strength(self) -> None:
        """Test that athletics maps to STRENGTH."""
        assert SKILL_TO_STAT["athletics"] == Stat.STRENGTH

    def test_arcana_maps_to_intelligence(self) -> None:
        """Test that arcana maps to INTELLIGENCE."""
        assert SKILL_TO_STAT["arcana"] == Stat.INTELLIGENCE

    def test_perception_maps_to_wisdom(self) -> None:
        """Test that perception maps to WISDOM."""
        assert SKILL_TO_STAT["perception"] == Stat.WISDOM

    def test_persuasion_maps_to_charisma(self) -> None:
        """Test that persuasion maps to CHARISMA."""
        assert SKILL_TO_STAT["persuasion"] == Stat.CHARISMA


class TestUserRoundtrip:
    """Tests for User serialization roundtrip."""

    def test_user_to_dict_and_back(self) -> None:
        """Test User survives to_dict -> from_dict roundtrip."""
        original = User(name="TestUser", active="Grog", unavailability=["2024-01-01"])
        dict_data = original.to_dict()
        restored = User.from_dict(dict_data)
        assert restored.name == original.name
        assert restored.active == original.active
        assert restored.unavailability == original.unavailability


class TestSessionRoundtrip:
    """Tests for Session serialization roundtrip."""

    def test_session_to_dict_and_back(self) -> None:
        """Test Session survives to_dict -> from_dict roundtrip."""
        original = Session(on=["2024-01-01"], off=["2024-01-08"], wday=0)
        dict_data = original.to_dict()
        restored = Session.from_dict(dict_data)
        assert restored.on == original.on
        assert restored.off == original.off
        assert restored.wday == original.wday


class TestGuildDataRoundtrip:
    """Tests for GuildData serialization roundtrip."""

    def test_guild_data_to_dict_and_back(self) -> None:
        """Test GuildData survives to_dict -> from_dict roundtrip."""
        original = GuildData()
        original.sessions.wday = 0
        dict_data = original.to_dict()
        restored = GuildData.from_dict(dict_data)
        assert restored.sessions.wday == original.sessions.wday


class TestCacheRoundtrip:
    """Tests for Cache methods."""

    def test_cache_to_dict_and_back(self) -> None:
        """Test Cache survives to_dict -> from_dict roundtrip."""
        original = Cache()
        original.get_or_create_guild("guild1")
        dict_data = original.to_dict()
        restored = Cache.from_dict(dict_data)
        assert "guild1" in restored.data


class TestCacheGetOrCreate:
    """Tests for Cache get_or_create methods."""

    def test_get_or_create_guild_new(self) -> None:
        """Test creating a new guild."""
        cache = Cache()
        cache.get_or_create_guild("new_guild")
        assert "new_guild" in cache.data

    def test_get_or_create_guild_existing(self) -> None:
        """Test getting an existing guild."""
        cache = Cache()
        guild1 = cache.get_or_create_guild("guild1")
        guild2 = cache.get_or_create_guild("guild1")
        assert guild1 is guild2

    def test_get_or_create_user_new(self) -> None:
        """Test creating a new user."""
        cache = Cache()
        cache.get_or_create_guild("guild1")
        user = cache.get_or_create_user("guild1", "user123", "TestUser")
        assert user.name == "TestUser"
        assert "user123" in cache.data["guild1"].users

    def test_get_or_create_user_existing(self) -> None:
        """Test getting an existing user."""
        cache = Cache()
        cache.get_or_create_guild("guild1")
        user1 = cache.get_or_create_user("guild1", "user123", "TestUser")
        user2 = cache.get_or_create_user("guild1", "user123", "NewName")
        # User exists, so name is not updated (gets existing user)
        assert user1 is user2
