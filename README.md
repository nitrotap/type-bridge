# type-bridge

[![CI](https://github.com/ds1sqe/type-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/ds1sqe/type-bridge/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/type-bridge.svg)](https://pypi.org/project/type-bridge/)
[![npm](https://img.shields.io/npm/v/@type-bridge/type-bridge)](https://www.npmjs.com/package/@type-bridge/type-bridge)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![TypeDB 3.x](https://img.shields.io/badge/TypeDB-3.x-orange.svg)](https://typedb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Type-safe ORM for TypeDB** - Available for Python and TypeScript.

## What is TypeDB?

[TypeDB](https://typedb.com/) is a strongly-typed database with a unique type system featuring:

- **Entities** - Independent objects with attributes
- **Relations** - Connections between entities with role players
- **Attributes** - Typed values owned by entities and relations

type-bridge provides Pythonic/TypeScript abstractions over TypeDB's native TypeQL query language.

## Packages

| Package | Version | Install |
|---------|---------|---------|
| [Python](./packages/python) | 1.1.0 | `pip install type-bridge` |
| [TypeScript](./packages/typescript) | 0.1.0 | `npm install @type-bridge/type-bridge` |

## Quick Start

### Python

```python
from type_bridge import Entity, String, Integer, TypeFlags, Flag, Key

# Define attribute types
class Name(String):
    pass

class Age(Integer):
    pass

# Define entity
class Person(Entity):
    flags = TypeFlags(name="person")
    name: Name = Flag(Key)
    age: Age | None = None

# CRUD operations
from type_bridge import Database

db = Database("localhost:1729", "mydb")
manager = Person.manager(db)

# Insert
alice = Person(name=Name("Alice"), age=Age(30))
manager.insert(alice)

# Query
adults = manager.filter(age__gte=18).all()
```

### TypeScript

```typescript
import {
  Database,
  Entity,
  StringAttribute,
  IntegerAttribute,
  TypeFlags,
  AttributeFlags,
} from '@type-bridge/type-bridge';

// Define attributes
class Name extends StringAttribute {
  static override flags = new AttributeFlags({ name: 'name' });
}

class Age extends IntegerAttribute {
  static override flags = new AttributeFlags({ name: 'age' });
}

// Define entity
class Person extends Entity {
  static override flags = new TypeFlags({ name: 'person' });
  declare name: Name;
  declare age: Age;
}

// CRUD operations
const db = new Database({ address: 'localhost:1729', database: 'mydb' });
await db.connect();

const manager = Person.manager(db);
await manager.insert(new Person({ name: new Name('Alice'), age: new Age(30) }));

const adults = await manager.query().filter({ age__gte: 18 }).all();
```

## Features

| Feature | Python | TypeScript |
|---------|--------|------------|
| CRUD Operations | Yes | Yes |
| Query Builder | Yes | Yes |
| Expression System | Yes | Yes |
| Transaction Support | Yes | Yes |
| Django-style Filters | Yes | Yes |
| Schema Management | Yes | - |
| Migrations | Yes | - |
| Code Generator (TQL→Code) | Yes | - |

## Documentation

- [Python Documentation](./packages/python/README.md)
- [TypeScript Documentation](./packages/typescript/README.md)
- [Python API Reference](./packages/python/docs/api/README.md)
- [TypeScript API Reference](./packages/typescript/docs/README.md)

## Development

### Python

```bash
cd packages/python
uv sync --extra dev
uv run pytest              # Unit tests
./test-integration.sh      # Integration tests (requires TypeDB)
```

### TypeScript

```bash
cd packages/typescript
npm install
npm test
npm run build
```

### Running TypeDB

```bash
docker compose up -d
```

## Requirements

- **Python**: 3.13+, `typedb-driver>=3.7.0`
- **TypeScript**: Node.js 18+, `typedb-driver-http>=3.0.0`
- **TypeDB**: 3.x

## License

MIT
