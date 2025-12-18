"""Unit tests for IID extraction from TypeDB results."""

import pytest

from type_bridge.session import _extract_iid_from_string


class TestExtractIidFromString:
    """Tests for _extract_iid_from_string helper function."""

    def test_extracts_iid_from_entity_string(self):
        """Test extracting IID from entity string representation."""
        s = "Entity(person: 0x1e00000000000000000000)"
        iid = _extract_iid_from_string(s)
        assert iid == "0x1e00000000000000000000"

    def test_extracts_iid_from_relation_string(self):
        """Test extracting IID from relation string representation."""
        s = "Relation(employment: 0x2f00000000000000000001)"
        iid = _extract_iid_from_string(s)
        assert iid == "0x2f00000000000000000001"

    def test_extracts_iid_from_concept_row_format(self):
        """Test extracting IID from ConceptRow string format."""
        s = "|  $e: Entity(test_entity: 0x1e00000000000000000000)  |"
        iid = _extract_iid_from_string(s)
        assert iid == "0x1e00000000000000000000"

    def test_returns_none_for_no_iid(self):
        """Test returns None when no IID is present."""
        s = "Some string without an IID"
        iid = _extract_iid_from_string(s)
        assert iid is None

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string."""
        iid = _extract_iid_from_string("")
        assert iid is None

    def test_extracts_first_iid_from_multiple(self):
        """Test extracts first IID when multiple are present."""
        s = "Entity(person: 0xaaa) Relation(emp: 0xbbb)"
        iid = _extract_iid_from_string(s)
        assert iid == "0xaaa"

    def test_extracts_iid_with_uppercase_hex(self):
        """Test extracts IID with uppercase hex characters."""
        s = "Entity(person: 0x1E00ABCDEF000000000000)"
        iid = _extract_iid_from_string(s)
        assert iid == "0x1E00ABCDEF000000000000"

    def test_extracts_iid_with_mixed_case_hex(self):
        """Test extracts IID with mixed case hex characters."""
        s = "Entity(person: 0x1e00AbCdEf000000000000)"
        iid = _extract_iid_from_string(s)
        assert iid == "0x1e00AbCdEf000000000000"
