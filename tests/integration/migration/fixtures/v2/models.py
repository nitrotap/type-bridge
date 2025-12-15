"""V2 models: Person with name and nickname."""

from type_bridge import Entity, Flag, Key, String, TypeFlags
from type_bridge.attribute import AttributeFlags


class Name(String):
    flags = AttributeFlags(name="name")


class Nickname(String):
    flags = AttributeFlags(name="nickname")


class Person(Entity):
    flags = TypeFlags(name="person")
    name: Name = Flag(Key)
    nickname: Nickname | None = None
