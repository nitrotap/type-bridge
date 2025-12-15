"""V1 models: Person with name only."""

from type_bridge import Entity, Flag, Key, String, TypeFlags
from type_bridge.attribute import AttributeFlags


class Name(String):
    flags = AttributeFlags(name="name")


class Person(Entity):
    flags = TypeFlags(name="person")
    name: Name = Flag(Key)
