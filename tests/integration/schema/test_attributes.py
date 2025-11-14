"""Integration tests for schema attribute constraints."""

import pytest

from type_bridge import Entity, EntityFlags, Flag, Key, SchemaManager, String, Unique


@pytest.mark.integration
@pytest.mark.order(5)
def test_schema_with_unique_attributes(clean_db):
    """Test schema creation with unique attributes."""

    class Email(String):
        pass

    class Username(String):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user")
        email: Email = Flag(Key)
        username: Username = Flag(Unique)

    # Create and sync schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(User)
    schema_manager.sync_schema(force=True)

    # Verify schema
    schema_info = schema_manager.collect_schema_info()
    user_info = schema_info.entities["user"]

    # Check key and unique flags
    assert user_info.owns["Email"].is_key is True
    assert user_info.owns["Username"].is_unique is True
