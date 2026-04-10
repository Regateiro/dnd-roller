"""Unit tests for the Discord client."""

from __future__ import annotations

from bot.client import DNDRollerClient


class TestDNDRollerClientMappings:
    """Tests for DNDRollerClient class command mappings."""

    def test_commands_mapping(self) -> None:
        """Test that command mappings are correctly defined."""
        assert DNDRollerClient._COMMANDS["!r"] == "roll"
        assert DNDRollerClient._COMMANDS["!roll"] == "roll"
        assert DNDRollerClient._COMMANDS["!character"] == "character"
        assert DNDRollerClient._COMMANDS["!char"] == "character"
        assert DNDRollerClient._COMMANDS["!c"] == "character"
        assert DNDRollerClient._COMMANDS["!m"] == "macro"
        assert DNDRollerClient._COMMANDS["!macro"] == "macro"
        assert DNDRollerClient._COMMANDS["!v"] == "variable"
        assert DNDRollerClient._COMMANDS["!var"] == "variable"
        assert DNDRollerClient._COMMANDS["!variable"] == "variable"
        assert DNDRollerClient._COMMANDS["!session"] == "session"
        assert DNDRollerClient._COMMANDS["!s"] == "session"
        assert DNDRollerClient._COMMANDS["!distance"] == "distance"
        assert DNDRollerClient._COMMANDS["!d"] == "distance"
        assert DNDRollerClient._COMMANDS["!fall"] == "fall"
        assert DNDRollerClient._COMMANDS["!f"] == "fall"
        assert DNDRollerClient._COMMANDS["!h"] == "help"
        assert DNDRollerClient._COMMANDS["!help"] == "help"

    def test_command_handlers_mapping(self) -> None:
        """Test that command handler mappings are correctly defined."""
        assert DNDRollerClient._COMMAND_HANDLERS["roll"] == "handle"
        assert DNDRollerClient._COMMAND_HANDLERS["character"] == "handle"
        assert DNDRollerClient._COMMAND_HANDLERS["session"] == "handle"
        assert DNDRollerClient._COMMAND_HANDLERS["macro"] == "handle_macro"
        assert DNDRollerClient._COMMAND_HANDLERS["variable"] == "handle_variable"
        assert DNDRollerClient._COMMAND_HANDLERS["distance"] == "handle_distance"
        assert DNDRollerClient._COMMAND_HANDLERS["fall"] == "handle_fall"
        assert DNDRollerClient._COMMAND_HANDLERS["help"] == "handle_help"

    def test_all_commands_have_handlers(self) -> None:
        """Test that all commands have corresponding handlers defined."""
        for command, handler_name in DNDRollerClient._COMMANDS.items():
            method_name = DNDRollerClient._COMMAND_HANDLERS.get(handler_name)
            assert method_name is not None, f"Command {command} has no handler method"


class TestCreateClient:
    """Tests for the create_client function."""

    def test_create_client_returns_dnd_roller_client(self) -> None:
        """Test that create_client returns a DNDRollerClient instance."""
        from unittest.mock import patch, MagicMock

        with patch("bot.client.DNDRollerClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            from bot.client import create_client
            create_client()

            mock_client_cls.assert_called_once()
