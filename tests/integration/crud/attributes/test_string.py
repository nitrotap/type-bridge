"""Integration tests for String attribute CRUD operations."""

import pytest

from type_bridge import Entity, EntityFlags, Flag, Integer, Key, SchemaManager, String


@pytest.mark.integration
@pytest.mark.order(31)
def test_string_insert(clean_db):
    """Test inserting entity with String attribute."""

    class Username(String):
        pass

    class Bio(String):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user_str")
        username: Username = Flag(Key)
        bio: Bio

    # Create schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(User)
    schema_manager.sync_schema(force=True)

    manager = User.manager(clean_db)

    # Insert user with String
    user = User(username=Username("alice"), bio=Bio("Python developer"))
    manager.insert(user)

    # Verify insertion
    results = manager.get(username="alice")
    assert len(results) == 1
    assert results[0].bio.value == "Python developer"


@pytest.mark.integration
@pytest.mark.order(32)
def test_string_fetch(clean_db):
    """Test fetching entity by String attribute."""

    class Username(String):
        pass

    class Bio(String):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user_str_fetch")
        username: Username = Flag(Key)
        bio: Bio

    # Create schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(User)
    schema_manager.sync_schema(force=True)

    manager = User.manager(clean_db)

    # Insert users
    users = [
        User(username=Username("bob"), bio=Bio("Java developer")),
        User(username=Username("charlie"), bio=Bio("Python developer")),
    ]
    manager.insert_many(users)

    # Fetch by String value
    python_devs = manager.get(bio="Python developer")
    assert len(python_devs) == 1
    assert python_devs[0].username.value == "charlie"


@pytest.mark.integration
@pytest.mark.order(33)
def test_string_update(clean_db):
    """Test updating String attribute."""

    class Username(String):
        pass

    class Bio(String):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user_str_update")
        username: Username = Flag(Key)
        bio: Bio

    # Create schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(User)
    schema_manager.sync_schema(force=True)

    manager = User.manager(clean_db)

    # Insert user
    user = User(username=Username("diana"), bio=Bio("Junior developer"))
    manager.insert(user)

    # Fetch and update
    results = manager.get(username="diana")
    user_fetched = results[0]
    user_fetched.bio = Bio("Senior developer")
    manager.update(user_fetched)

    # Verify update
    updated = manager.get(username="diana")
    assert updated[0].bio.value == "Senior developer"


@pytest.mark.integration
@pytest.mark.order(34)
def test_string_delete(clean_db):
    """Test deleting entity with String attribute."""

    class Username(String):
        pass

    class Bio(String):
        pass

    class User(Entity):
        flags = EntityFlags(type_name="user_str_delete")
        username: Username = Flag(Key)
        bio: Bio

    # Create schema
    schema_manager = SchemaManager(clean_db)
    schema_manager.register(User)
    schema_manager.sync_schema(force=True)

    manager = User.manager(clean_db)

    # Insert user
    user = User(username=Username("eve"), bio=Bio("TypeDB expert"))
    manager.insert(user)

    # Delete by String attribute
    deleted_count = manager.delete(bio="TypeDB expert")
    assert deleted_count == 1

    # Verify deletion
    results = manager.get(username="eve")
    assert len(results) == 0
