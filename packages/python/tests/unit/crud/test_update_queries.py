"""Unit tests for update query generation to ensure multi-value diffs are guarded."""

from typing import Any, cast

from typedb.driver import TransactionType

from type_bridge import (
    Card,
    Database,
    Entity,
    Flag,
    Key,
    Relation,
    Role,
    String,
    TypeFlags,
)
from type_bridge.crud.entity.manager import EntityManager
from type_bridge.crud.relation.manager import RelationManager


class _RecordingEntityManager(EntityManager):
    """Entity manager that records executed queries instead of hitting TypeDB."""

    def __init__(self, model_class: type):
        super().__init__(cast(Database, object()), model_class)
        self.queries: list[str] = []

    def _execute(self, query: str, tx_type: TransactionType) -> list[dict[str, Any]]:
        self.queries.append(query)
        return []


class _RecordingRelationManager(RelationManager):
    """Relation manager that records executed queries instead of hitting TypeDB."""

    def __init__(self, model_class: type):
        super().__init__(cast(Database, object()), model_class)
        self.queries: list[str] = []

    def _execute(self, query: str, tx_type: TransactionType) -> list[dict[str, Any]]:
        self.queries.append(query)
        return []


def test_entity_update_multi_value_uses_guards():
    """Updating multi-value attributes should guard against deleting kept values."""

    class Name(String):
        pass

    class Tag(String):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        tags: list[Tag] = Flag(Card(min=0))

    person = Person(name=Name("Alice"), tags=[Tag("keep"), Tag("drop")])
    mgr = _RecordingEntityManager(Person)

    mgr.update(person)

    query = mgr.queries[-1]
    attr_name = Tag.get_attribute_name()
    # Variable name includes entity var suffix for batch query compatibility
    attr_var = f"${attr_name}_e"
    expected_try = (
        "try {\n"
        f"  $e has {attr_name} {attr_var};\n"
        f'  not {{ {attr_var} == "keep"; }};\n'
        f'  not {{ {attr_var} == "drop"; }};\n'
        "};"
    )
    assert expected_try in query


def test_relation_update_multi_value_uses_guards():
    """Relation updates should also guard multi-value deletions."""

    class Note(String):
        pass

    class Doc(String):
        pass

    class User(Entity):
        flags = TypeFlags(name="user")
        doc: Doc = Flag(Key)

    class Attachment(Relation):
        flags = TypeFlags(name="attachment")
        owner: Role[User] = Role("owner", User)
        notes: list[Note] = Flag(Card(min=0))

    attachment = Attachment(owner=User(doc=Doc("ref")), notes=[Note("keep"), Note("old")])
    mgr = _RecordingRelationManager(Attachment)

    mgr.update(attachment)

    query = mgr.queries[-1]
    attr_name = Note.get_attribute_name()
    attr_var = f"${attr_name}"
    expected_try = (
        "try {\n"
        f"  $r has {attr_name} {attr_var};\n"
        f'  not {{ {attr_var} == "keep"; }};\n'
        f'  not {{ {attr_var} == "old"; }};\n'
        "};"
    )
    assert expected_try in query
