"""Unit tests for the commands module."""

from __future__ import annotations

from bot.commands import (
    CHARACTER_COMMAND_ALIASES,
    CHARACTER_UPDATE_ALIASES,
    MACRO_COMMAND_ALIASES,
    ROLL_MODIFIER_ALIASES,
    SESSION_COMMAND_ALIASES,
    VARIABLE_COMMAND_ALIASES,
    CommandHandler,
    CommandRegistry,
    RollMode,
    get_roll_mode,
    resolve_command_alias,
)


class TestRollMode:
    """Tests for the RollMode enum."""

    def test_normal_value(self) -> None:
        """Test NORMAL mode has correct value."""
        assert RollMode.NORMAL == "n"

    def test_advantage_value(self) -> None:
        """Test ADVANTAGE mode has correct value."""
        assert RollMode.ADVANTAGE == "a"

    def test_triple_advantage_value(self) -> None:
        """Test TRIPLE_ADVANTAGE mode has correct value."""
        assert RollMode.TRIPLE_ADVANTAGE == "ta"

    def test_disadvantage_value(self) -> None:
        """Test DISADVANTAGE mode has correct value."""
        assert RollMode.DISADVANTAGE == "d"


class TestResolveCommandAlias:
    """Tests for the resolve_command_alias function."""

    def test_resolve_create_alias_create(self) -> None:
        """Test resolving 'create' alias returns 'create'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "create") == "create"

    def test_resolve_create_alias_c(self) -> None:
        """Test resolving 'c' alias returns 'create'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "c") == "create"

    def test_resolve_delete_alias_d(self) -> None:
        """Test resolving 'd' alias returns 'delete'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "d") == "delete"

    def test_resolve_update_alias_u(self) -> None:
        """Test resolving 'u' alias returns 'update'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "u") == "update"

    def test_resolve_active_alias_a(self) -> None:
        """Test resolving 'a' alias returns 'active'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "a") == "active"

    def test_resolve_info_alias_show(self) -> None:
        """Test resolving 'show' alias returns 'info'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "show") == "info"

    def test_resolve_info_alias_i(self) -> None:
        """Test resolving 'i' alias returns 'info'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "i") == "info"

    def test_resolve_info_alias_s(self) -> None:
        """Test resolving 's' alias returns 'info'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "s") == "info"

    def test_resolve_list_alias_l(self) -> None:
        """Test resolving 'l' alias returns 'list'."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "l") == "list"

    def test_resolve_unknown_returns_none(self) -> None:
        """Test resolving unknown alias returns None."""
        assert resolve_command_alias(CHARACTER_COMMAND_ALIASES, "unknown") is None

    def test_resolve_macro_set(self) -> None:
        """Test resolving macro 'set' alias."""
        assert resolve_command_alias(MACRO_COMMAND_ALIASES, "set") == "set"

    def test_resolve_macro_s(self) -> None:
        """Test resolving macro 's' alias."""
        assert resolve_command_alias(MACRO_COMMAND_ALIASES, "s") == "set"

    def test_resolve_variable_set(self) -> None:
        """Test resolving variable 'set' alias uses macro aliases."""
        assert resolve_command_alias(VARIABLE_COMMAND_ALIASES, "set") == "set"

    def test_resolve_session_weekday_w(self) -> None:
        """Test resolving session 'w' alias."""
        assert resolve_command_alias(SESSION_COMMAND_ALIASES, "w") == "weekday"

    def test_resolve_session_schedule_s(self) -> None:
        """Test resolving session 's' alias."""
        assert resolve_command_alias(SESSION_COMMAND_ALIASES, "s") == "schedule"

    def test_resolve_session_cancel_c(self) -> None:
        """Test resolving session 'c' alias."""
        assert resolve_command_alias(SESSION_COMMAND_ALIASES, "c") == "cancel"

    def test_resolve_session_available_a(self) -> None:
        """Test resolving session 'a' alias."""
        assert resolve_command_alias(SESSION_COMMAND_ALIASES, "a") == "available"

    def test_resolve_session_unavailable_u(self) -> None:
        """Test resolving session 'u' alias."""
        assert resolve_command_alias(SESSION_COMMAND_ALIASES, "u") == "unavailable"

    def test_resolve_session_list_l(self) -> None:
        """Test resolving session 'l' alias."""
        assert resolve_command_alias(SESSION_COMMAND_ALIASES, "l") == "list"

    def test_resolve_session_next_n(self) -> None:
        """Test resolving session 'n' alias."""
        assert resolve_command_alias(SESSION_COMMAND_ALIASES, "n") == "next"

    def test_resolve_character_update_main(self) -> None:
        """Test resolving character update 'main' alias."""
        assert resolve_command_alias(CHARACTER_UPDATE_ALIASES, "main") == "main"

    def test_resolve_character_update_saves(self) -> None:
        """Test resolving character update 'saves' alias."""
        assert resolve_command_alias(CHARACTER_UPDATE_ALIASES, "saves") == "saves"

    def test_resolve_character_update_bonus(self) -> None:
        """Test resolving character update 'bonus' alias."""
        assert resolve_command_alias(CHARACTER_UPDATE_ALIASES, "bonus") == "bonus"

    def test_resolve_character_update_skills(self) -> None:
        """Test resolving character update 'skills' alias."""
        assert resolve_command_alias(CHARACTER_UPDATE_ALIASES, "skills") == "skills"

    def test_resolve_character_update_expertise(self) -> None:
        """Test resolving character update 'expertise' alias."""
        assert resolve_command_alias(CHARACTER_UPDATE_ALIASES, "expertise") == "expertise"

    def test_resolve_character_update_half(self) -> None:
        """Test resolving character update 'half' alias."""
        assert resolve_command_alias(CHARACTER_UPDATE_ALIASES, "half") == "half"

    def test_resolve_character_update_advantage_adv(self) -> None:
        """Test resolving character update 'adv' alias."""
        assert resolve_command_alias(CHARACTER_UPDATE_ALIASES, "adv") == "advantage"

    def test_resolve_roll_save(self) -> None:
        """Test resolving roll 'save' alias."""
        assert resolve_command_alias(ROLL_MODIFIER_ALIASES, "save") == "save"

    def test_resolve_roll_save_s(self) -> None:
        """Test resolving roll 's' alias."""
        assert resolve_command_alias(ROLL_MODIFIER_ALIASES, "s") == "save"

    def test_resolve_roll_crit(self) -> None:
        """Test resolving roll 'crit' alias."""
        assert resolve_command_alias(ROLL_MODIFIER_ALIASES, "crit") == "crit"

    def test_resolve_roll_crit_critical(self) -> None:
        """Test resolving roll 'critical' alias."""
        assert resolve_command_alias(ROLL_MODIFIER_ALIASES, "critical") == "crit"

    def test_resolve_roll_advantage(self) -> None:
        """Test resolving roll 'advantage' alias."""
        assert resolve_command_alias(ROLL_MODIFIER_ALIASES, "advantage") == "advantage"

    def test_resolve_roll_adv(self) -> None:
        """Test resolving roll 'adv' alias."""
        assert resolve_command_alias(ROLL_MODIFIER_ALIASES, "adv") == "advantage"


class TestGetRollMode:
    """Tests for the get_roll_mode function."""

    def test_get_a(self) -> None:
        """Test 'a' returns ADVANTAGE."""
        assert get_roll_mode("a") == RollMode.ADVANTAGE

    def test_get_adv(self) -> None:
        """Test 'adv' returns ADVANTAGE."""
        assert get_roll_mode("adv") == RollMode.ADVANTAGE

    def test_get_advantage(self) -> None:
        """Test 'advantage' returns ADVANTAGE."""
        assert get_roll_mode("advantage") == RollMode.ADVANTAGE

    def test_get_ta(self) -> None:
        """Test 'ta' returns TRIPLE_ADVANTAGE."""
        assert get_roll_mode("ta") == RollMode.TRIPLE_ADVANTAGE

    def test_get_tadv(self) -> None:
        """Test 'tadv' returns TRIPLE_ADVANTAGE."""
        assert get_roll_mode("tadv") == RollMode.TRIPLE_ADVANTAGE

    def test_get_tadvantage(self) -> None:
        """Test 'tadvantage' returns TRIPLE_ADVANTAGE."""
        assert get_roll_mode("tadvantage") == RollMode.TRIPLE_ADVANTAGE

    def test_get_d(self) -> None:
        """Test 'd' returns DISADVANTAGE."""
        assert get_roll_mode("d") == RollMode.DISADVANTAGE

    def test_get_dis(self) -> None:
        """Test 'dis' returns DISADVANTAGE."""
        assert get_roll_mode("dis") == RollMode.DISADVANTAGE

    def test_get_disadvantage(self) -> None:
        """Test 'disadvantage' returns DISADVANTAGE."""
        assert get_roll_mode("disadvantage") == RollMode.DISADVANTAGE

    def test_get_invalid_returns_none(self) -> None:
        """Test invalid mode returns None."""
        assert get_roll_mode("invalid") is None

    def test_get_n_returns_none(self) -> None:
        """Test 'n' (normal) returns None since it's default."""
        assert get_roll_mode("n") is None


class TestCommandHandler:
    """Tests for the CommandHandler dataclass."""

    def test_command_handler_creation(self) -> None:
        """Test CommandHandler stores handler and aliases."""
        def dummy_handler():
            pass

        handler = CommandHandler(dummy_handler, ("alias1", "alias2"))
        assert handler.handler is dummy_handler
        assert handler.aliases == ("alias1", "alias2")


class TestCommandRegistry:
    """Tests for the CommandRegistry class."""

    def test_registry_initializes_handlers(self) -> None:
        """Test registry initializes with all handlers."""

        class DummyHandler:
            async def handle(self, *args):
                pass

            async def handle_macro(self, *args):
                pass

            async def handle_variable(self, *args):
                pass

            async def handle_distance(self, *args):
                pass

            async def handle_fall(self, *args):
                pass

            async def handle_help(self, *args):
                pass

        registry = CommandRegistry(
            roll_handler=DummyHandler(),
            character_handler=DummyHandler(),
            session_handler=DummyHandler(),
            utility_handler=DummyHandler(),
        )
        assert registry._roll_handler is not None
        assert registry._character_handler is not None
        assert registry._session_handler is not None
        assert registry._utility_handler is not None


class FullDummyHandler:
    async def handle(self, *args):
        pass

    async def handle_macro(self, *args):
        pass

    async def handle_variable(self, *args):
        pass

    async def handle_distance(self, *args):
        pass

    async def handle_fall(self, *args):
        pass

    async def handle_help(self, *args):
        pass


class TestCommandRegistryGetHandler:
    """Tests for CommandRegistry.get_handler."""

    def test_get_handler_for_r(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!r")
        assert handler is not None

    def test_get_handler_for_roll(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!roll")
        assert handler is not None

    def test_get_handler_for_character(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!character")
        assert handler is not None

    def test_get_handler_for_macro(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!macro")
        assert handler is not None

    def test_get_handler_for_session(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!session")
        assert handler is not None

    def test_get_handler_for_distance(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!distance")
        assert handler is not None

    def test_get_handler_for_fall(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!fall")
        assert handler is not None

    def test_get_handler_for_help(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!help")
        assert handler is not None

    def test_get_handler_unknown_returns_none(self) -> None:
        registry = CommandRegistry(
            roll_handler=FullDummyHandler(),
            character_handler=FullDummyHandler(),
            session_handler=FullDummyHandler(),
            utility_handler=FullDummyHandler(),
        )
        handler = registry.get_handler("!unknown")
        assert handler is None


