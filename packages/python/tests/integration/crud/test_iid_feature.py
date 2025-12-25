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
        assert found.age is not None
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
        employment = IidEmployment(employee=person, employer=company, position=Position("Engineer"))
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
        employment = IidEmployment(employee=person, employer=company, position=Position("Manager"))
        IidEmployment.manager(self.db).insert(employment)

        # Get the IID
        fetched = IidEmployment.manager(self.db).get()[0]
        iid = fetched._iid
        assert iid is not None

        # Fetch by IID
        found = IidEmployment.manager(self.db).get_by_iid(iid)
        assert found is not None
        assert found.position is not None
        assert found.position.value == "Manager"
        assert found._iid == iid

    def test_relation_get_populates_role_player_iids(self):
        """Test that get() populates _iid on role player entities (issue #68)."""
        # Insert entities
        person = IidPerson(name=PersonName("Grace"), age=PersonAge(29))
        IidPerson.manager(self.db).insert(person)

        company = IidCompany(name=CompanyName("StartupCo"))
        IidCompany.manager(self.db).insert(company)

        # Get entity IIDs for comparison
        person_iid = IidPerson.manager(self.db).get(name="Grace")[0]._iid
        company_iid = IidCompany.manager(self.db).get(name="StartupCo")[0]._iid
        assert person_iid is not None
        assert company_iid is not None

        # Insert relation
        employment = IidEmployment(employee=person, employer=company, position=Position("Founder"))
        IidEmployment.manager(self.db).insert(employment)

        # Fetch the relation
        fetched = IidEmployment.manager(self.db).get()
        assert len(fetched) == 1

        # Verify relation IID is populated
        fetched_emp = fetched[0]
        assert fetched_emp._iid is not None
        assert fetched_emp._iid.startswith("0x")

        # Verify role player IIDs are populated (issue #68)
        assert fetched_emp.employee is not None
        assert fetched_emp.employee._iid is not None
        assert fetched_emp.employee._iid.startswith("0x")
        assert fetched_emp.employee._iid == person_iid

        assert fetched_emp.employer is not None
        assert fetched_emp.employer._iid is not None
        assert fetched_emp.employer._iid.startswith("0x")
        assert fetched_emp.employer._iid == company_iid

    def test_relation_filter_execute_populates_role_player_iids(self):
        """Test that filter().execute() populates _iid on role player entities (issue #68)."""
        # Insert entities
        person = IidPerson(name=PersonName("Henry"), age=PersonAge(45))
        IidPerson.manager(self.db).insert(person)

        company = IidCompany(name=CompanyName("MegaCorp"))
        IidCompany.manager(self.db).insert(company)

        # Get entity IIDs for comparison
        person_iid = IidPerson.manager(self.db).get(name="Henry")[0]._iid
        company_iid = IidCompany.manager(self.db).get(name="MegaCorp")[0]._iid
        assert person_iid is not None
        assert company_iid is not None

        # Insert relation
        employment = IidEmployment(employee=person, employer=company, position=Position("CEO"))
        IidEmployment.manager(self.db).insert(employment)

        # Fetch using filter
        fetched = IidEmployment.manager(self.db).filter(position=Position("CEO")).execute()
        assert len(fetched) == 1

        # Verify relation IID is populated
        fetched_emp = fetched[0]
        assert fetched_emp._iid is not None
        assert fetched_emp._iid.startswith("0x")

        # Verify role player IIDs are populated (issue #68)
        assert fetched_emp.employee is not None
        assert fetched_emp.employee._iid is not None
        assert fetched_emp.employee._iid == person_iid

        assert fetched_emp.employer is not None
        assert fetched_emp.employer._iid is not None
        assert fetched_emp.employer._iid == company_iid

    def test_relation_all_populates_role_player_iids(self):
        """Test that all() populates _iid on role player entities (issue #68)."""
        # Insert entities
        person = IidPerson(name=PersonName("Iris"), age=PersonAge(33))
        IidPerson.manager(self.db).insert(person)

        company = IidCompany(name=CompanyName("GiantCorp"))
        IidCompany.manager(self.db).insert(company)

        # Get entity IIDs for comparison
        person_iid = IidPerson.manager(self.db).get(name="Iris")[0]._iid
        company_iid = IidCompany.manager(self.db).get(name="GiantCorp")[0]._iid
        assert person_iid is not None
        assert company_iid is not None

        # Insert relation
        employment = IidEmployment(employee=person, employer=company, position=Position("CTO"))
        IidEmployment.manager(self.db).insert(employment)

        # Fetch all relations
        all_relations = IidEmployment.manager(self.db).all()

        # Find our relation
        fetched_emp = next(r for r in all_relations if r.position and r.position.value == "CTO")
        assert fetched_emp is not None

        # Verify relation IID is populated
        assert fetched_emp._iid is not None
        assert fetched_emp._iid.startswith("0x")

        # Verify role player IIDs are populated (issue #68)
        assert fetched_emp.employee is not None
        assert fetched_emp.employee._iid is not None
        assert fetched_emp.employee._iid == person_iid

        assert fetched_emp.employer is not None
        assert fetched_emp.employer._iid is not None
        assert fetched_emp.employer._iid == company_iid


@pytest.mark.integration
class TestRelationAllIidCorrectness:
    """Tests for issue #78: RelationManager.all() assigns incorrect IIDs to role players.

    When using RelationManager.all() to fetch multiple relations, each relation
    should have unique, correct IIDs for its role players - not the same IIDs
    from the first matched result.
    """

    @pytest.fixture(autouse=True)
    def setup_schema(self, clean_db):
        """Setup schema for each test."""
        self.db = clean_db
        schema_manager = SchemaManager(clean_db)
        schema_manager.register(IidPerson)
        schema_manager.register(IidCompany)
        schema_manager.register(IidEmployment)
        schema_manager.sync_schema(force=True)

    def test_all_returns_unique_role_player_iids_issue_78(self):
        """Test that all() returns unique IIDs for each relation's role players.

        Regression test for issue #78: Previously, all relations returned by all()
        would have the same IIDs for their role players (from the first result).
        """
        # Create two different people
        person_a = IidPerson(name=PersonName("PersonA"), age=PersonAge(25))
        person_b = IidPerson(name=PersonName("PersonB"), age=PersonAge(30))
        IidPerson.manager(self.db).insert(person_a)
        IidPerson.manager(self.db).insert(person_b)

        # Create two different companies
        company_x = IidCompany(name=CompanyName("CompanyX"))
        company_y = IidCompany(name=CompanyName("CompanyY"))
        IidCompany.manager(self.db).insert(company_x)
        IidCompany.manager(self.db).insert(company_y)

        # Get the actual IIDs for each entity from the database
        person_a_iid = IidPerson.manager(self.db).get(name="PersonA")[0]._iid
        person_b_iid = IidPerson.manager(self.db).get(name="PersonB")[0]._iid
        company_x_iid = IidCompany.manager(self.db).get(name="CompanyX")[0]._iid
        company_y_iid = IidCompany.manager(self.db).get(name="CompanyY")[0]._iid

        # Verify all IIDs are unique
        all_entity_iids = {person_a_iid, person_b_iid, company_x_iid, company_y_iid}
        assert len(all_entity_iids) == 4, "All entities should have unique IIDs"

        # Create two employments with different role players
        emp1 = IidEmployment(employee=person_a, employer=company_x, position=Position("Role1"))
        emp2 = IidEmployment(employee=person_b, employer=company_y, position=Position("Role2"))
        IidEmployment.manager(self.db).insert(emp1)
        IidEmployment.manager(self.db).insert(emp2)

        # Fetch all relations using all()
        all_relations = list(IidEmployment.manager(self.db).all())
        assert len(all_relations) == 2

        # Find each relation by position
        rel1 = next(r for r in all_relations if r.position and r.position.value == "Role1")
        rel2 = next(r for r in all_relations if r.position and r.position.value == "Role2")

        # Verify each relation has the correct IIDs for its role players
        # This is the key assertion for issue #78 - previously both relations
        # would have the same IIDs (from the first matched result)

        # Relation 1 should have PersonA and CompanyX
        assert rel1.employee is not None
        assert rel1.employee._iid == person_a_iid, (
            f"Expected PersonA IID {person_a_iid}, got {rel1.employee._iid}"
        )
        assert rel1.employer is not None
        assert rel1.employer._iid == company_x_iid, (
            f"Expected CompanyX IID {company_x_iid}, got {rel1.employer._iid}"
        )

        # Relation 2 should have PersonB and CompanyY
        assert rel2.employee is not None
        assert rel2.employee._iid == person_b_iid, (
            f"Expected PersonB IID {person_b_iid}, got {rel2.employee._iid}"
        )
        assert rel2.employer is not None
        assert rel2.employer._iid == company_y_iid, (
            f"Expected CompanyY IID {company_y_iid}, got {rel2.employer._iid}"
        )

        # Also verify that the relation IIDs themselves are unique
        assert rel1._iid is not None
        assert rel2._iid is not None
        assert rel1._iid != rel2._iid, "Each relation should have a unique IID"

    def test_get_returns_unique_role_player_iids_issue_78(self):
        """Test that get() also returns unique IIDs for each relation's role players.

        Similar to test_all but using get() without filters.
        """
        # Create people and companies
        person_c = IidPerson(name=PersonName("PersonC"), age=PersonAge(35))
        person_d = IidPerson(name=PersonName("PersonD"), age=PersonAge(40))
        IidPerson.manager(self.db).insert(person_c)
        IidPerson.manager(self.db).insert(person_d)

        company_z = IidCompany(name=CompanyName("CompanyZ"))
        company_w = IidCompany(name=CompanyName("CompanyW"))
        IidCompany.manager(self.db).insert(company_z)
        IidCompany.manager(self.db).insert(company_w)

        # Get entity IIDs
        person_c_iid = IidPerson.manager(self.db).get(name="PersonC")[0]._iid
        person_d_iid = IidPerson.manager(self.db).get(name="PersonD")[0]._iid
        company_z_iid = IidCompany.manager(self.db).get(name="CompanyZ")[0]._iid
        company_w_iid = IidCompany.manager(self.db).get(name="CompanyW")[0]._iid

        # Create employments
        emp3 = IidEmployment(employee=person_c, employer=company_z, position=Position("Role3"))
        emp4 = IidEmployment(employee=person_d, employer=company_w, position=Position("Role4"))
        IidEmployment.manager(self.db).insert(emp3)
        IidEmployment.manager(self.db).insert(emp4)

        # Fetch using get() with no filters
        all_relations = IidEmployment.manager(self.db).get()
        assert len(all_relations) == 2

        # Find each relation
        rel3 = next(r for r in all_relations if r.position and r.position.value == "Role3")
        rel4 = next(r for r in all_relations if r.position and r.position.value == "Role4")

        # Verify correct IIDs
        assert rel3.employee._iid == person_c_iid
        assert rel3.employer._iid == company_z_iid
        assert rel4.employee._iid == person_d_iid
        assert rel4.employer._iid == company_w_iid
