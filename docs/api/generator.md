# Code Generator

Generate TypeBridge Python models from TypeDB schema files (`.tql`).

## Overview

The generator eliminates manual synchronization between TypeDB schemas and Python code. Instead of writing both `.tql` and Python classes, you write the schema once in TypeQL and generate type-safe Python models.

```
schema.tql  →  generator  →  attributes.py
                          →  entities.py
                          →  relations.py
                          →  __init__.py
```

## Quick Start

### CLI Usage

```bash
# Generate models from a schema file
python -m type_bridge.generator schema.tql -o ./myapp/models/

# With options
python -m type_bridge.generator schema.tql \
    --output ./myapp/models/ \
    --version 2.0.0 \
    --implicit-keys id
```

### Programmatic Usage

```python
from type_bridge.generator import generate_models

# From a file path
generate_models("schema.tql", "./myapp/models/")

# From schema text
schema = """
define
entity person, owns name @key;
attribute name, value string;
"""
generate_models(schema, "./myapp/models/")
```

## CLI Reference

```
python -m type_bridge.generator [-h] -o DIR [--version VERSION]
                                [--no-copy-schema]
                                [--implicit-keys [ATTR ...]]
                                schema

positional arguments:
  schema                Path to the TypeDB schema file (.tql)

options:
  -h, --help            Show help message and exit
  -o, --output DIR      Output directory for generated package (required)
  --version VERSION     Schema version string (default: 1.0.0)
  --no-copy-schema      Don't copy the schema file to the output directory
  --implicit-keys       Attribute names to treat as @key even if not marked
```

The `--output` directory is **required**. We recommend a dedicated directory like `./myapp/models/` or `./src/schema/` to keep generated code separate from hand-written code.

## Generated Package Structure

```
myapp/models/
├── __init__.py      # Package exports, SCHEMA_VERSION, schema_text()
├── attributes.py    # Attribute class definitions
├── entities.py      # Entity class definitions
├── relations.py     # Relation class definitions
└── schema.tql       # Copy of original schema (unless --no-copy-schema)
```

### Using the Generated Package

```python
from myapp.models import attributes, entities, relations
from myapp.models import SCHEMA_VERSION, schema_text

# Access generated classes
person = entities.Person(name=attributes.Name("Alice"))

# Get schema version
print(SCHEMA_VERSION)  # "1.0.0"

# Get original schema text
print(schema_text())
```

## Supported TypeQL Features

The generator supports the full TypeDB 3.0 schema syntax:

| Feature | Status |
|---------|--------|
| Attributes with value types | ✓ |
| `@abstract` types | ✓ |
| `@independent` attributes | ✓ |
| `sub` inheritance | ✓ |
| `@regex` constraints | ✓ |
| `@values` constraints | ✓ |
| `@range` constraints | ✓ |
| `@key` / `@unique` | ✓ |
| `@card` on owns | ✓ |
| `@card` on plays | ✓ |
| `@card` on relates | ✓ |
| Role overrides (`as`) | ✓ |
| Functions (`fun`) | ✓ |
| `#` and `//` comments | ✓ |

### Attributes

```typeql
// Basic attribute with value type
attribute name, value string;

// Abstract attribute (generates inheritance)
attribute id @abstract, value string;
attribute person-id sub id;

// Independent attribute (can exist without owner)
attribute language @independent, value string;

// With constraints
attribute email, value string @regex("^.*@.*$");
attribute status, value string @values("active", "inactive");

// Range constraints
attribute age, value integer @range(0..150);
attribute latitude, value double @range(-90.0..90.0);
attribute birth-date, value date @range(1900-01-01..2100-12-31);
attribute created-at, value datetime @range(1970-01-01T00:00:00..);  // Open-ended
```

**Generated Python:**

```python
class Name(String):
    flags = AttributeFlags(name="name")

class Id(String):
    flags = AttributeFlags(name="id")

class PersonId(Id):
    flags = AttributeFlags(name="person-id")

class Language(String):
    flags = AttributeFlags(name="language")
    independent: ClassVar[bool] = True

class Email(String):
    flags = AttributeFlags(name="email")
    regex: ClassVar[str] = r"^.*@.*$"

class Status(String):
    flags = AttributeFlags(name="status")
    allowed_values: ClassVar[tuple[str, ...]] = ("active", "inactive",)

class Age(Integer):
    flags = AttributeFlags(name="age")
    range_min: ClassVar[str] = "0"
    range_max: ClassVar[str] = "150"
```

### Entities

```typeql
// Basic entity
entity person,
    owns name @key,
    owns age,
    plays employment:employee;

// Abstract entity with inheritance
entity content @abstract,
    owns id @key;

entity post sub content,
    owns title,
    owns body;

// Cardinality constraints on owns
entity page,
    owns tag @card(0..10),
    owns name @card(1..3);

// Cardinality constraints on plays
entity user,
    plays friendship:friend @card(0..100),
    plays posting:author @card(0..);
```

**Generated Python:**

```python
class Person(Entity):
    flags = TypeFlags(name="person")
    plays: ClassVar[tuple[str, ...]] = ("employment:employee",)
    name: attributes.Name = Flag(Key)
    age: attributes.Age | None = None

class Content(Entity):
    flags = TypeFlags(name="content", abstract=True)
    id: attributes.Id = Flag(Key)

class Post(Content):
    flags = TypeFlags(name="post")
    title: attributes.Title | None = None
    body: attributes.Body | None = None

class Page(Entity):
    flags = TypeFlags(name="page")
    tag: list[attributes.Tag] = Flag(Card(0, 10))
    name: list[attributes.Name] = Flag(Card(1, 3))
```

### Relations

```typeql
// Basic relation
relation employment,
    relates employer,
    relates employee;

// Relation with inheritance and role override
relation contribution @abstract,
    relates contributor,
    relates work;

relation authoring sub contribution,
    relates author as contributor;  // Role override

// Relation with attributes
relation review,
    relates reviewer,
    relates reviewed,
    owns score,
    owns timestamp;

// Cardinality constraints on roles
relation social-relation @abstract,
    relates related @card(0..);

relation friendship sub social-relation,
    relates friend as related @card(0..1000);

relation parentship,
    relates parent @card(1..2),
    relates child @card(1..);
```

**Generated Python:**

```python
class Employment(Relation):
    flags = TypeFlags(name="employment")
    employer: Role[entities.Company] = Role("employer", entities.Company)
    employee: Role[entities.Person] = Role("employee", entities.Person)

class Contribution(Relation):
    flags = TypeFlags(name="contribution", abstract=True)
    contributor: Role[entities.Contributor] = Role("contributor", entities.Contributor)
    work: Role[entities.Publication] = Role("work", entities.Publication)

class Authoring(Contribution):
    flags = TypeFlags(name="authoring")
    author: Role[entities.Contributor] = Role("author", entities.Contributor)

class Review(Relation):
    flags = TypeFlags(name="review")
    score: attributes.Score
    timestamp: attributes.Timestamp
    reviewer: Role[entities.User] = Role("reviewer", entities.User)
    reviewed: Role[entities.Publication] = Role("reviewed", entities.Publication)
```

## Cardinality Mapping

| TypeQL | Python Type | Default |
|--------|-------------|---------|
| `@card(1)` or `@card(1..1)` | `Type` | Required |
| `@card(0..1)` or no annotation | `Type \| None = None` | Optional |
| `@card(0..)` | `list[Type] = Flag(Card(min=0))` | Optional list |
| `@card(1..)` | `list[Type] = Flag(Card(min=1))` | Required list |
| `@card(2..5)` | `list[Type] = Flag(Card(2, 5))` | Bounded list |
| `@key` | `Type = Flag(Key)` | Key (implies required) |
| `@unique` | `Type = Flag(Unique)` | Unique (implies required) |

## Comments

The parser supports both `#` (shell-style) and `//` (C-style) comments:

```typeql
# This is a shell-style comment
// This is a C-style comment
attribute name, value string;  // Inline comment
entity person, owns name;  # Also inline
```

### Comment Annotations

The generator supports special comment annotations for customizing output:

```typeql
# @prefix(PERSON_)
# Custom prefix for IDs
entity person,
    owns id @key;

# @internal
# This entity is for internal use
entity audit-log,
    owns timestamp;

# @tags(api, public)
entity user,
    owns username @key;
```

| Annotation | Effect |
|------------|--------|
| `# @prefix(XXX)` | Adds `prefix: ClassVar[str] = "XXX"` |
| `# @internal` | Sets `internal = True` on the spec |
| `# @case(SNAKE_CASE)` | Uses specified case for type name |
| `# @transform(xxx)` | Adds `transform = "xxx"` attribute |
| `# @tags(a, b, c)` | Adds list annotation |
| `# Any other comment` | Becomes the class docstring |

## Functions

TypeDB functions (`fun` declarations) are fully parsed and can be used for metadata. The generator extracts function signatures including parameters and return types.

### Supported Function Syntax

```typeql
// Stream return (single type)
fun user_phones($user: user) -> { phone }:
    match $user has phone $phone;
    return { $phone };

// Stream return (tuple)
fun all_users_and_phones() -> { user, phone, string }:
    match $user isa user, has phone $phone;
    return { $user, $phone, "value" };

// Single scalar return
fun add($x: integer, $y: integer) -> integer:
    match let $z = $x + $y;
    return first $z;

// Tuple return
fun divide($a: integer, $b: integer) -> integer, integer:
    match let $q = $a / $b;
    return first $q, $r;

// Bool return type
fun is_reachable($from: node, $to: node) -> bool:
    match ($from, $to) isa edge;
    return first true;

// Optional return type
fun any_place_with_optional_name() -> place, name?:
    match $p isa place;
    return first $p, $n;

// No parameters
fun mean_karma() -> double:
    match $user isa user, has karma $karma;
    return mean($karma);

// Aggregate returns
fun karma_sum_and_squares() -> double, double:
    match $karma isa karma;
    return sum($karma), sum($karma);
```

### Function Return Types

| TypeQL | Parsed `return_type` |
|--------|---------------------|
| `-> { type }` | `"{ type }"` |
| `-> { t1, t2 }` | `"{ t1, t2 }"` |
| `-> type` | `"type"` |
| `-> t1, t2` | `"t1, t2"` |
| `-> t1, t2?` | `"t1, t2?"` |
| `-> bool` | `"bool"` |

## API Reference

### `generate_models()`

```python
def generate_models(
    schema: str | Path,
    output_dir: str | Path,
    *,
    implicit_key_attributes: Iterable[str] | None = None,
    schema_version: str = "1.0.0",
    copy_schema: bool = True,
) -> None:
    """Generate TypeBridge models from a TypeDB schema.

    Args:
        schema: Path to .tql file or schema text content
        output_dir: Directory to write generated package
        implicit_key_attributes: Attribute names to treat as @key
        schema_version: Version string for SCHEMA_VERSION constant
        copy_schema: Whether to copy schema.tql to output directory
    """
```

### `parse_tql_schema()`

```python
def parse_tql_schema(schema_content: str) -> ParsedSchema:
    """Parse a TypeDB schema into intermediate representation.

    Args:
        schema_content: TypeQL schema text

    Returns:
        ParsedSchema with attributes, entities, and relations
    """
```

### `ParsedSchema`

```python
@dataclass
class ParsedSchema:
    """Container for parsed schema components."""
    attributes: dict[str, AttributeSpec]
    entities: dict[str, EntitySpec]
    relations: dict[str, RelationSpec]
    functions: dict[str, FunctionSpec]

    def accumulate_inheritance(self) -> None:
        """Propagate owns/plays/keys down inheritance hierarchies."""
```

### `FunctionSpec`

```python
@dataclass
class FunctionSpec:
    """Function definition extracted from a TypeDB schema."""
    name: str                        # e.g., "calculate-age"
    parameters: list[ParameterSpec]  # Function parameters
    return_type: str                 # e.g., "{ person }" or "integer, integer"

@dataclass
class ParameterSpec:
    """Parameter definition for a TypeDB function."""
    name: str   # e.g., "birth-date"
    type: str   # e.g., "date" or "user"
```

## Best Practices

### 1. Keep Generated Code Separate

```
myapp/
├── models/          # Generated (don't edit!)
│   ├── __init__.py
│   ├── attributes.py
│   ├── entities.py
│   └── relations.py
├── services/        # Hand-written business logic
└── schema.tql       # Source of truth
```

### 2. Regenerate After Schema Changes

```bash
# Add to your workflow
python -m type_bridge.generator schema.tql -o ./myapp/models/
```

### 3. Version Control the Schema, Not Generated Code

```gitignore
# .gitignore
myapp/models/  # Generated - regenerate from schema.tql
```

Or version control both for CI/CD verification:

```bash
# CI check: ensure generated code is up to date
python -m type_bridge.generator schema.tql -o ./myapp/models/
git diff --exit-code myapp/models/
```

### 4. Use `--implicit-keys` for Convention-Based Keys

If your schema uses `id` as a key by convention:

```bash
python -m type_bridge.generator schema.tql -o ./models/ --implicit-keys id
```

## See Also

- [Entities Documentation](entities.md) - Entity inheritance and ownership
- [Relations Documentation](relations.md) - Relations, roles, and role players
- [Attributes Documentation](attributes.md) - Attribute types and constraints
- [Cardinality Documentation](cardinality.md) - Card API and Flag system
