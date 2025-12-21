# Type-Bridge Performance Analysis

This document provides a technical audit of the `type-bridge` library performance bottlenecks and tracks optimization efforts.

## 1. Executive Summary

Major performance optimizations have been implemented:
- **N+1 IID Resolution**: Fixed in PR #73 (10-50x improvement)
- **Batch Write Operations**: `insert_many`, `update_many`, `delete_many` now use single queries
- **`update_with()` Batching**: Now uses single batched query (30-50x improvement)
- **All `_populate_iids()` Batching**: Entity and Relation managers/queries now use single disjunctive queries (100x improvement)
- **EntityQuery `_match_entity_type()`**: Now uses in-memory lookup (no N+1 queries)
- **RelationQuery `update_with()` Batching**: Now uses single conjunctive query (30-50x improvement)
- **RelationManager `delete_many()` Batching**: Now uses disjunctive queries (Nx improvement)

Remaining low-priority optimizations:
- **Triple-query overhead in `get()`**: Could be reduced from 3 to 2 queries (1.5x improvement)

---

## 2. Completed Optimizations

### A. N+1 IID & Type Resolution — COMPLETED (PR #73)

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 entities | 102 | 2-3 |
| Improvement | — | **10-50x** |

Modified `_get_iids_and_types` to use dual-query approach with in-memory lookup instead of per-entity database queries.

### B. Batch Write Operations — COMPLETED

| Operation | Before | After |
|-----------|--------|-------|
| `insert_many` | N queries | 1 query |
| `update_many` | N queries | 1 query (conjunctive batching) |
| `delete_many` | N queries | 1 query (disjunctive batching) |

### C. `update_with()` Batching — COMPLETED

**Location:** `crud/entity/query.py`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 entities | 101 | 2 |
| Improvement | — | **30-50x** |

**Solution implemented:**
- Added `_build_batched_update_query()` method that combines all entity updates into a single TypeQL query
- Uses the same conjunctive batching pattern as `update_many()` in EntityManager
- Each entity gets unique variable names (`$e0`, `$e1`, etc.) to avoid conflicts

### D. Relation `_populate_iids()` Batching — COMPLETED

**Location:** `crud/relation/manager.py`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 relations | 100 | 1 |
| Improvement | — | **100x** |

**Solution implemented:**
- Uses single disjunctive query with shared variable names
- Correlates results back to relations by matching role player key attributes
- Single query fetches IIDs for all relations and their role players

### E. EntityQuery `_match_entity_type()` — COMPLETED

**Location:** `crud/entity/query.py`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 entities | 100 | 0 (in-memory) |
| Improvement | — | **N queries eliminated** |

**Solution implemented:**
- Updated `_get_iids_and_types()` to return a map keyed by attribute values (matching EntityManager pattern)
- `_match_entity_type()` now does pure in-memory lookup instead of database query per entity

### F. EntityQuery._populate_iids() — COMPLETED

**Location:** `crud/entity/query.py:460-555`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 entities | 100 | 2 |
| Improvement | — | **50x** |

**Solution implemented:**
- Uses single disjunctive query with shared variable names
- Correlates results by position (fetch and select return in same order)
- Single query fetches IIDs for all entities

### G. EntityManager._populate_iids() — COMPLETED

**Location:** `crud/entity/manager.py:1375-1471`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 entities | 100 | 2 |
| Improvement | — | **50x** |

**Solution implemented:**
- Uses single disjunctive query with shared variable names
- Same pattern as EntityQuery._populate_iids()

### H. RelationQuery._populate_iids() — COMPLETED

**Location:** `crud/relation/query.py:557-678`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 relations | 100 | 1 |
| Improvement | — | **100x** |

**Solution implemented:**
- Uses single disjunctive query with shared variable names
- Correlates results by position

### I. RelationManager.delete_many() — COMPLETED

**Location:** `crud/relation/manager.py:1191-1354`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 relations | 100 | 2 |
| Improvement | — | **50x** |

**Solution implemented:**
- Uses batched disjunctive queries for existence checking and deletion
- Added `strict` parameter for optional error handling (matches EntityManager API)

### J. RelationQuery.update_with() — COMPLETED

**Location:** `crud/relation/query.py:821-1130`

| Metric | Before | After |
|--------|--------|-------|
| Queries for 100 relations | 100 | 2 |
| Improvement | — | **50x** |

**Solution implemented:**
- Uses conjunctive batching pattern for efficient bulk updates
- Each relation gets unique indexed variable names ($r0, $r1, etc.)
- Single query updates all relations

---

## 3. Open Bottlenecks

### A. Triple-Query Overhead in `get()` — LOW PRIORITY

**Location:** `crud/entity/manager.py:1189-1311`

**Problem:**
When `get()` is called without key filters, three queries execute:
1. `_get_iids_and_types()`: Fetch query for attributes
2. `_get_iids_and_types()`: Select query for IIDs/types
3. Main fetch query for full instantiation

| Metric | Current | Expected |
|--------|---------|----------|
| Queries | 3 | 2 |
| Potential Improvement | — | **1.5x** |

**Solution:**
Cache and reuse the fetch results from `_get_iids_and_types()` instead of re-fetching.

---

## 4. Low Priority Items

### Connection Pooling

**Location:** `session.py:204-210`

Current implementation uses lazy connection initialization with no connection pooling. Each `Database` instance creates its own driver.

**Impact:** Variable, depends on usage pattern
**Effort:** Low

### String Formatting in Loops

**Locations:**
- `crud/entity/manager.py:686-687`
- `crud/relation/manager.py:70-87`

`format_value()` is called repeatedly in loops without memoization.

**Impact:** Minimal
**Effort:** Low

---

## 5. Rejected Proposals

### Pydantic `model_construct()` — ABANDONED

Attempted and abandoned. `model_construct()` bypasses too much Pydantic logic, causing bugs with optional attributes. The benefit was minimal since validators already short-circuit for wrapped values.

### Rust Core Rewrite — NOT RECOMMENDED

The bottleneck is database roundtrips, not Python performance. The N+1 fix achieved 10-50x improvement in pure Python. Rust would add maintenance burden without addressing the actual bottleneck.

---

## 6. Recommended Roadmap

| Priority | Task | Impact | Effort | Status |
|----------|------|--------|--------|--------|
| 1 | Batch `update_with()` queries | 30-50x | Medium | **COMPLETED** |
| 2 | Batch all `_populate_iids()` methods | 50-100x | Medium | **COMPLETED** |
| 3 | EntityQuery `_match_entity_type()` fix | N queries | Low | **COMPLETED** |
| 4 | Batch RelationQuery `update_with()` | 50x | Medium | **COMPLETED** |
| 5 | Batch RelationManager `delete_many()` | 50x | Medium | **COMPLETED** |
| 6 | Consolidate `get()` query flow | 1.5x | Low | TODO |
| 7 | Connection pooling | Variable | Low | TODO |

---

## 7. Changelog

- **2024-12-21**: Implemented remaining N+1 fixes:
  - EntityQuery._populate_iids() batching (50x improvement)
  - EntityManager._populate_iids() batching (50x improvement)
  - RelationQuery._populate_iids() batching (100x improvement)
  - RelationManager.delete_many() batching with `strict` parameter (50x improvement)
  - RelationQuery.update_with() batching (50x improvement)
- **2024-12-20**: Implemented `update_with()` batching (30-50x improvement)
- **2024-12-20**: Implemented RelationManager `_populate_iids()` batching (100x improvement)
- **2024-12-20**: Fixed EntityQuery `_match_entity_type()` N+1 pattern
- **2024-12-20**: Added new findings from comprehensive code review
- **2024-12-18**: N+1 fix implemented (PR #73)
- **2024-12-18**: Batch write operations completed
- **2024-12-18**: Pydantic `model_construct()` attempted and abandoned
- **2024-12-18**: Rust core proposal evaluated and deemed premature
