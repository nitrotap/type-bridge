"""Integration tests for IID (Internal ID) feature.

Tests for issue #62: Expose TypeDB IID on entity instances.
"""

import pytest

from type_bridge import (
    Entity,
    Flag,
    Integer,
    Key,
    Relation,
    Role,
    SchemaManager,
    String,
    TypeFlags,
)


class PersonName(String):
    pass


class PersonAge(Integer):
    pass


class CompanyName(String):
    pass


class Position(String):
    pass


class IidPerson(Entity):
    flags = TypeFlags(name="iid_person")
    name: PersonName = Flag(Key)
    age: PersonAge | None = None


class IidCompany(Entity):
    flags = TypeFlags(name="iid_company")
    name: CompanyName = Flag(Key)


class IidEmployment(Relation):
    flags = TypeFlags(name="iid_employment")
    employee: Role[IidPerson] = Role("employee", IidPerson)
    employer: Role[IidCompany] = Role("employer", IidCompany)
    position: Position | None = None


@pytest.mark.integration
class TestEntityIidPopulation:
    """Tests for IID population on entities."""

    @pytest.fixture(autouse=True)
    def setup_schema(self, clean_db):
        """Setup schema for each test."""
        self.db = clean_db
        schema_manager = SchemaManager(clean_db)
        schema_manager.register(IidPerson)
        schema_manager.register(IidCompany)
        schema_manager.register(IidEmployment)
        schema_manager.sync_schema(force=True)

    def test_get_populates_iid(self):
        """Test that get() populates _iid on returned entities."""
        manager = IidPerson.manager(self.db)

        # Insert a person
        person = IidPerson(name=PersonName("Alice"), age=PersonAge(30))
        manager.insert(person)

        # Fetch the person
        fetched = manager.get(name="Alice")
        assert len(fetched) == 1

        # Verify IID is populated
        fetched_person = fetched[0]
        assert fetched_person._iid is not None
        assert fetched_person._iid.startswith("0x")

    def test_filter_execute_populates_iid(self):
        """Test that filter().execute() populates _iid on returned entities."""
        manager = IidPerson.manager(self.db)

        # Insert a person
        person = IidPerson(name=PersonName("Bob"), age=PersonAge(25))
        manager.insert(person)

        # Fetch using filter
        fetched = manager.filter(name=PersonName("Bob")).execute()
        assert len(fetched) == 1

        # Verify IID is populated
        fetched_person = fetched[0]
        assert fetched_person._iid is not None
        assert fetched_person._iid.startswith("0x")

    def test_iid_is_stable_across_queries(self):
        """Test that the same entity returns the same IID across queries."""
        manager = IidPerson.manager(self.db)

        # Insert a person
        person = IidPerson(name=PersonName("Charlie"), age=PersonAge(35))
        manager.insert(person)

        # Fetch twice
        first_fetch = manager.get(name="Charlie")[0]
        second_fetch = manager.get(name="Charlie")[0]

        # IIDs should match
        assert first_fetch._iid is not None
        assert second_fetch._iid is not None
        assert first_fetch._iid == second_fetch._iid


@pytest.mark.integration
class TestGetByIid:
    """Tests for get_by_iid method."""

    @pytest.fixture(autouse=True)
    def setup_schema(self, clean_db):
        """Setup schema for each test."""
        self.db = clean_db
        schema_manager = SchemaManager(clean_db)
        schema_manager.register(IidPerson)
        schema_manager.register(IidCompany)
        schema_manager.register(IidEmployment)
        schema_manager.sync_schema(force=True)

    def test_get_by_iid_returns_entity(self):
        """Test that get_by_iid returns the correct entity."""
        manager = IidPerson.manager(self.db)

        # Insert a person
        person = IidPerson(name=PersonName("David"), age=PersonAge(40))
        manager.insert(person)

        # Get the IID
        fetched = manager.get(name="David")[0]
        iid = fetched._iid
        assert iid is not None

        # Fetch by IID
        found = manager.get_by_iid(iid)
        assert found is not None
        assert found.name.value == "David"
        assert found.age.value == 40
        assert found._iid == iid

    def test_get_by_iid_returns_none_for_nonexistent(self):
        """Test that get_by_iid returns None for non-existent IID."""
        manager = IidPerson.manager(self.db)

        # Try to fetch with a fake IID
        result = manager.get_by_iid("0xdeadbeefdeadbeefdeadbeef")
        assert result is None

    def test_get_by_iid_validates_format(self):
        """Test that get_by_iid validates IID format."""
        manager = IidPerson.manager(self.db)

        with pytest.raises(ValueError, match="Invalid IID format"):
            manager.get_by_iid("not-a-valid-iid")


@pytest.mark.integration
class TestRelationIidPopulation:
    """Tests for IID population on relations."""

    @pytest.fixture(autouse=True)
    def setup_schema(self, clean_db):
        """Setup schema for each test."""
        self.db = clean_db
        schema_manager = SchemaManager(clean_db)
        schema_manager.register(IidPerson)
        schema_manager.register(IidCompany)
        schema_manager.register(IidEmployment)
        schema_manager.sync_schema(force=True)

    def test_relation_get_populates_iid(self):
        """Test that get() populates _iid on returned relations."""
        # Insert entities
        person = IidPerson(name=PersonName("Eve"), age=PersonAge(28))
        IidPerson.manager(self.db).insert(person)

        company = IidCompany(name=CompanyName("TechCorp"))
        IidCompany.manager(self.db).insert(company)

        # Insert relation
        employment = IidEmployment(
            employee=person,
            employer=company,
            position=Position("Engineer")
        )
        IidEmployment.manager(self.db).insert(employment)

        # Fetch the relation
        fetched = IidEmployment.manager(self.db).get()
        assert len(fetched) == 1

        # Verify IID is populated
        fetched_emp = fetched[0]
        assert fetched_emp._iid is not None
        assert fetched_emp._iid.startswith("0x")

    def test_relation_get_by_iid(self):
        """Test that get_by_iid works for relations."""
        # Insert entities
        person = IidPerson(name=PersonName("Frank"), age=PersonAge(32))
        IidPerson.manager(self.db).insert(person)

        company = IidCompany(name=CompanyName("BigCorp"))
        IidCompany.manager(self.db).insert(company)

        # Insert relation
        employment = IidEmployment(
            employee=person,
            employer=company,
            position=Position("Manager")
        )
        IidEmployment.manager(self.db).insert(employment)

        # Get the IID
        fetched = IidEmployment.manager(self.db).get()[0]
        iid = fetched._iid
        assert iid is not None

        # Fetch by IID
        found = IidEmployment.manager(self.db).get_by_iid(iid)
        assert found is not None
        assert found.position.value == "Manager"
        assert found._iid == iid
