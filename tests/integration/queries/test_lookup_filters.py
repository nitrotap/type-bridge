"""Integration tests for Django-style lookup filters on EntityManager."""

import pytest

from type_bridge import Entity, Flag, Integer, Key, String, TypeFlags


@pytest.mark.integration
@pytest.mark.order(205)
def test_string_lookups(db_with_schema):
    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    mgr = Person.manager(db_with_schema)

    people = [
        Person(name=Name("Alice"), age=Age(30)),
        Person(name=Name("Albert"), age=Age(25)),
        Person(name=Name("Bob"), age=Age(40)),
    ]
    mgr.insert_many(people)

    startswith_a = mgr.filter(name__startswith="Al").execute()
    assert {p.name.value for p in startswith_a} == {"Alice", "Albert"}

    contains_ice = mgr.filter(name__contains="ice").execute()
    assert {p.name.value for p in contains_ice} == {"Alice"}

    endswith_ce = mgr.filter(name__endswith="ce").execute()
    assert {p.name.value for p in endswith_ce} == {"Alice"}

    regex_b = mgr.filter(name__regex="^B.*").execute()
    assert {p.name.value for p in regex_b} == {"Bob"}


@pytest.mark.integration
@pytest.mark.order(206)
def test_numeric_lookups_and_in(db_with_schema):
    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    mgr = Person.manager(db_with_schema)

    people = [
        Person(name=Name("Cara"), age=Age(20)),
        Person(name=Name("Dora"), age=Age(35)),
        Person(name=Name("Eli"), age=Age(42)),
    ]
    mgr.insert_many(people)

    over_30 = mgr.filter(age__gt=30).execute()
    assert {p.name.value for p in over_30} == {"Dora", "Eli"}

    in_filter = mgr.filter(name__in=["Cara", Name("Eli")]).execute()
    assert {p.name.value for p in in_filter} == {"Cara", "Eli"}


@pytest.mark.integration
@pytest.mark.order(207)
def test_isnull_lookup(db_with_schema):
    class Name(String):
        pass

    class Age(Integer):
        pass

    class Person(Entity):
        flags = TypeFlags(name="person")
        name: Name = Flag(Key)
        age: Age | None

    mgr = Person.manager(db_with_schema)

    mgr.insert_many(
        [
            Person(name=Name("NullAge"), age=None),
            Person(name=Name("WithAge"), age=Age(50)),
        ]
    )

    missing_age = mgr.filter(age__isnull=True).execute()
    assert {p.name.value for p in missing_age} == {"NullAge"}

    present_age = mgr.filter(age__isnull=False).execute()
    assert {p.name.value for p in present_age} == {"WithAge"}
