"""Tests for deprecated type_name parameter."""

import warnings

import pytest

from type_bridge import TypeFlags


class TestDeprecatedTypeName:
    """Test deprecation warning for type_name parameter."""

    def test_type_name_parameter_shows_deprecation_warning(self):
        """Test that using type_name parameter triggers a DeprecationWarning."""
        with pytest.warns(DeprecationWarning, match="type_name.*deprecated.*Use 'name' instead"):
            TypeFlags(type_name="test")

    def test_type_name_parameter_still_works(self):
        """Test that type_name parameter still functions correctly."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            flags = TypeFlags(type_name="my_type")
            assert flags.name == "my_type"

    def test_name_parameter_no_warning(self):
        """Test that using name parameter does not trigger a warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Convert all warnings to errors
            flags = TypeFlags(name="test")
            assert flags.name == "test"

    def test_type_name_takes_precedence(self):
        """Test that type_name takes precedence over name for backward compatibility."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            flags = TypeFlags(name="new_name", type_name="old_name")
            assert flags.name == "old_name"
