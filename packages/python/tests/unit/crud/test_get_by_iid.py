"""Unit tests for get_by_iid method validation."""

from unittest.mock import MagicMock, patch

import pytest

from type_bridge import Entity, Flag, Integer, Key, String, TypeFlags


class Name(String):
    pass


class Age(Integer):
    pass


class TestPerson(Entity):
    flags = TypeFlags(name="test_person")
    name: Name = Flag(Key)
    age: Age | None = None


class TestGetByIidValidation:
    """Tests for get_by_iid method parameter validation."""

    @patch("type_bridge.crud.entity.manager.ConnectionExecutor")
    def test_raises_on_empty_iid(self, mock_executor):
        """Test raises ValueError for empty IID."""
        from type_bridge.crud import EntityManager

        mock_connection = MagicMock()
        manager = EntityManager(mock_connection, TestPerson)

        with pytest.raises(ValueError, match="Invalid IID format"):
            manager.get_by_iid("")

    @patch("type_bridge.crud.entity.manager.ConnectionExecutor")
    def test_raises_on_invalid_iid_format(self, mock_executor):
        """Test raises ValueError for IID not starting with 0x."""
        from type_bridge.crud import EntityManager

        mock_connection = MagicMock()
        manager = EntityManager(mock_connection, TestPerson)

        with pytest.raises(ValueError, match="Invalid IID format"):
            manager.get_by_iid("1e00000000000000000000")

    @patch("type_bridge.crud.entity.manager.ConnectionExecutor")
    def test_raises_on_none_iid(self, mock_executor):
        """Test raises ValueError for None IID."""
        from type_bridge.crud import EntityManager

        mock_connection = MagicMock()
        manager = EntityManager(mock_connection, TestPerson)

        with pytest.raises(ValueError, match="Invalid IID format"):
            manager.get_by_iid(None)  # type: ignore

    @patch("type_bridge.crud.entity.manager.ConnectionExecutor")
    def test_accepts_valid_iid_format(self, mock_executor):
        """Test accepts valid IID format."""
        from type_bridge.crud import EntityManager

        mock_connection = MagicMock()
        mock_executor_instance = MagicMock()
        mock_executor_instance.execute.return_value = []
        mock_executor.return_value = mock_executor_instance

        manager = EntityManager(mock_connection, TestPerson)

        # Should not raise, just return None since no results
        result = manager.get_by_iid("0x1e00000000000000000000")
        assert result is None
