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

### Attributes

```typeql
# Basic attribute with value type
attribute name, value string;

# Abstract attribute (generates inheritance)
attribute id @abstract, value string;
attribute person-id sub id;

# With constraints
attribute email, value string @regex("^.*@.*$");
attribute status, value string @values("active", "inactive");
```

**Generated Python:**

```python
class Name(String):
    flags = AttributeFlags(name="name")

class Id(String):
    flags = AttributeFlags(name="id")

class PersonId(Id):
    flags = AttributeFlags(name="person-id")

class Email(String):
    flags = AttributeFlags(name="email")
    regex: ClassVar[str] = r"^.*@.*$"

class Status(String):
    flags = AttributeFlags(name="status")
    allowed_values: ClassVar[tuple[str, ...]] = ("active", "inactive",)
```

### Entities

```typeql
# Basic entity
entity person,
    owns name @key,
    owns age,
    plays employment:employee;

# Abstract entity with inheritance
entity content @abstract,
    owns id @key;

entity post sub content,
    owns title,
    owns body;

# Cardinality constraints
entity page,
    owns tag @card(0..10),
    owns name @card(1..3);
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
# Basic relation
relation employment,
    relates employer,
    relates employee;

# Relation with inheritance and role override
relation contribution @abstract,
    relates contributor,
    relates work;

relation authoring sub contribution,
    relates author as contributor;  # Role override

# Relation with attributes
relation review,
    relates reviewer,
    relates reviewed,
    owns score,
    owns timestamp;
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

## Comment Annotations

The generator supports special comment annotations for customizing output:

```typeql
# @prefix: PERSON_
# Custom prefix for IDs
entity person,
    owns id @key;

# @internal
# This entity is for internal use
entity audit-log,
    owns timestamp;
```

| Annotation | Effect |
|------------|--------|
| `# @prefix: XXX` | Adds `prefix: ClassVar[str] = "XXX"` |
| `# @internal` | Sets `internal = True` on the spec |
| `# @case: SNAKE_CASE` | Uses specified case for type name |
| `# @transform: xxx` | Adds `transform = "xxx"` attribute |
| `# Any other comment` | Becomes the class docstring |

## Functions

TypeDB functions (`fun` declarations) are automatically skipped during parsing. The generator only processes type definitions.

```typeql
# This function is ignored by the generator
fun get_user_posts($user: user) -> { post }:
    match
        $post isa post;
        (author: $user, work: $post) isa authoring;
    return { $post };
```

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

    def accumulate_inheritance(self) -> None:
        """Propagate owns/plays/keys down inheritance hierarchies."""
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

## Limitations

The following TypeQL features are not yet supported:

- `@range(min..max)` constraints on numeric attributes
- `@independent` attribute flag
- `@card` on `plays` declarations (e.g., `plays posting:page @card(0..)`)
- `//` style comments (only `#` comments are parsed)

## See Also

- [Entities Documentation](entities.md) - Entity inheritance and ownership
- [Relations Documentation](relations.md) - Relations, roles, and role players
- [Attributes Documentation](attributes.md) - Attribute types and constraints
- [Cardinality Documentation](cardinality.md) - Card API and Flag system
