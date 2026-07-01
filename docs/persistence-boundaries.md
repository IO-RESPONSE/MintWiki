# Persistence Boundaries

Database ownership and repository rules for the PostgreSQL persistence layer.

## Overview

The persistence layer uses the repository pattern to abstract database access. Each module owns its tables and exposes repository interfaces that enforce data ownership and consistency rules.

## Database Ownership

Ownership is defined by module, not by developer or role. Each module has exclusive write access to its tables.

### Document Module

**Owns table:** `document`

| Column | Type | Constraints | Ownership |
|--------|------|-------------|-----------|
| `id` | String(255) | PRIMARY KEY | Document module |
| `title` | String(500) | NOT NULL | Document module |
| `normalized_title` | String(500) | NOT NULL, UNIQUE | Document module |
| `current_revision_id` | String(255) | NULL | Document module (pointer to revision) |
| `created_at` | DateTime(tz) | NOT NULL, DEFAULT NOW | Database managed |
| `updated_at` | DateTime(tz) | NOT NULL, DEFAULT NOW, ONUPDATE NOW | Database managed |

**Exposed Operations:**
- `create(document: Document) -> Document` — Create a new document
- `get(id: str) -> Optional[Document]` — Fetch by id
- `get_by_normalized_title(title: str) -> Optional[Document]` — Fetch by normalized title
- `update(document: Document) -> Document` — Update existing document

**Invariants:**
- `normalized_title` is unique across the table
- `current_revision_id` is optional and points to a revision (no FK constraint—checked at service layer)
- `title` is the raw user input, never NULL
- `normalized_title` is derived from `title` by stripping and collapsing whitespace

**Access Rules:**
- Document module may write to `document` table
- Revision module may read `document.id` only for foreign key validation
- Other modules may read `document` via `DocumentService` only
- No module may directly mutate `normalized_title` or bypass uniqueness checks

### Revision Module

**Owns table:** `revision`

| Column | Type | Constraints | Ownership |
|--------|------|-------------|-----------|
| `id` | String(255) | PRIMARY KEY | Revision module |
| `document_id` | String(255) | NOT NULL, FK → document.id | Revision module |
| `source` | Text | NOT NULL | Revision module |
| `author_id` | String(255) | NOT NULL | Revision module (ACL module verifies author) |
| `summary` | String(500) | NOT NULL | Revision module |
| `parent_revision_id` | String(255) | NULL | Revision module (no FK constraint—checked at service layer) |
| `created_at` | DateTime(tz) | NOT NULL, DEFAULT NOW | Database managed |

**Exposed Operations:**
- `create(revision: Revision) -> Revision` — Create a new revision
- `get(id: str) -> Optional[Revision]` — Fetch by id
- `list_by_document_id(document_id: str) -> list[Revision]` — Fetch all revisions for a document, ordered by creation

**Invariants:**
- `document_id` must exist in `document` table (FK constraint)
- `parent_revision_id` is optional and points to another revision (no FK constraint—service layer validates)
- Revisions are append-only; once created, they are never modified
- `created_at` is set on insert and never changes
- Source is immutable after creation

**Access Rules:**
- Revision module may write to `revision` table
- Document module may read `revision` for current revision lookups (via service)
- Parser module may read `revision.source` for parsing, but only through Revision service
- Other modules may access revisions via `RevisionService` only
- No direct SQL queries to `revision` table from outside the module

## Repository Pattern

### Domain Model Separation

Each module has a domain model that represents the business entity, separate from the database representation.

**Document Domain Model** (`modules/document/model.py`):
```python
class Document:
    id: str
    title: str
    normalized_title: str  # Derived from title
    current_revision_id: Optional[str]
```

**Document ORM Model** (`persistence/models.py`):
```python
class DocumentORM(Base):
    __tablename__ = "document"
    # Maps directly to domain model via to_domain() and from_domain()
```

### Repository Interface

Each module defines an abstract repository interface:

```python
class DocumentRepository(ABC):
    async def create(self, document: Document) -> Document
    async def get(self, id: str) -> Optional[Document]
    async def get_by_normalized_title(self, normalized_title: str) -> Optional[Document]
    async def update(self, document: Document) -> Document
```

**Why abstract?** Multiple implementations can satisfy the interface:
- `InMemoryDocumentRepository` — For unit tests, local dev
- `DatabaseDocumentRepository` — For production, using AsyncSession

### Data Flow

**Write Path:**
```
Domain Model (Document)
  ↓ (from_domain)
ORM Model (DocumentORM)
  ↓ (add to session)
SQLAlchemy Session
  ↓ (flush/commit)
PostgreSQL
```

**Read Path:**
```
PostgreSQL
  ↓ (query result)
SQLAlchemy Session
  ↓ (scalar_one_or_none)
ORM Model (DocumentORM)
  ↓ (to_domain)
Domain Model (Document)
```

### Conversion Semantics

**`from_domain(domain_model) -> orm_model`:**
- Called when preparing a domain entity for persistence
- Creates a new ORM instance with the domain model's fields
- Does not execute database operations; only creates the ORM object
- Conversion is deterministic and side-effect-free

**`to_domain() -> domain_model`:**
- Called after loading an ORM model from the database
- Reconstructs the domain model with data from the row
- The domain model is independent of the ORM model lifecycle
- Conversion is deterministic and idempotent

## Transaction Guarantees

### Session Lifecycle

Each repository method receives an `AsyncSession` from the application's session factory:

```python
class DatabaseDocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
```

**Session ownership:** The session is created by the application layer (in `app/database.py`) and passed to repositories. Repositories do not create or close sessions.

### ACID Properties

**Atomicity:** Each repository method is wrapped in a transaction:
```python
async def create(self, document: Document) -> Document:
    orm_document = DocumentORM.from_domain(document)
    self.session.add(orm_document)
    await self.session.flush()      # Validate constraints
    await self.session.commit()     # Atomically write
```

If `flush()` raises an `IntegrityError`, the transaction is rolled back via `await self.session.rollback()`, and the error is re-raised as a domain exception (e.g., `DuplicateNormalizedTitleError`).

**Consistency:** Constraints are checked in the database:
- `normalized_title` UNIQUE constraint prevents duplicates
- `document_id` FK constraint in `revision` table prevents orphaned revisions
- `NOT NULL` constraints prevent incomplete rows

**Isolation:** AsyncIO sessions use PostgreSQL's default read-committed isolation level. Cross-session reads may see uncommitted data if sessions are not properly synchronized.

**Durability:** PostgreSQL WAL ensures durability after `COMMIT` returns.

### Cross-Module Transactions

When document creation must atomically create a document and a revision, use `DocumentRevisionTransaction`:

```python
from persistence.transaction import DocumentRevisionTransaction

transaction = DocumentRevisionTransaction(session)
document_to_create = Document(id=doc_id, title=title, current_revision_id=rev_id)
revision_to_create = Revision(id=rev_id, document_id=doc_id, ...)
document, revision = await transaction.create_document_with_revision(
    document_to_create, revision_to_create
)
# Both succeed or both fail atomically
```

If an error occurs during either operation, both changes are rolled back. This ensures that a document is never left without a revision, and a revision is never left orphaned.

## Integrity Rules

### Normalized Title Uniqueness

The `document.normalized_title` column has a UNIQUE constraint. The repository enforces this rule:

**Rule:** No two documents may have the same normalized title.

**Implementation:**
- `InMemoryDocumentRepository` checks in memory before insertion
- `DatabaseDocumentRepository` catches `IntegrityError` and re-raises as `DuplicateNormalizedTitleError`
- Domain: clients should validate titles before calling create

### Document-Revision Relationship

A revision must reference an existing document via the foreign key `revision.document_id → document.id`.

**Rule:** A revision may not be created for a document that does not exist.

**Implementation:**
- Database enforces via FK constraint
- Repository does not check; constraint failure is raised to caller
- Service layer (`RevisionService`) may validate before calling repository

### Current Revision Pointer

The `document.current_revision_id` column is optional and points to a revision.

**Rule:** A document's current revision must exist in the `revision` table.

**Implementation:**
- No FK constraint on `current_revision_id` (allows soft deletes, delayed writes)
- Service layer must validate before updating
- Repository does not enforce; service layer is responsible

## Module Boundaries

### Document Module Responsibilities

- Owns `document` table
- Provides `DocumentRepository` interface
- Ensures `normalized_title` uniqueness
- Maintains `current_revision_id` pointer
- Exposes `DocumentService` for public API

### Revision Module Responsibilities

- Owns `revision` table
- Provides `RevisionRepository` interface
- Ensures `document_id` FK integrity
- Maintains `parent_revision_id` chain for diffs and reverts
- Exposes `RevisionService` for public API

### Persistence Module Responsibilities

- Defines `DocumentORM` and `RevisionORM` classes
- Provides `Base` class and metadata for SQLAlchemy
- Provides transaction helpers (e.g., `DocumentRevisionTransaction`)
- Does NOT implement business logic

### Cross-Module Access

**Allowed:**
- Document service may call RevisionService to get current revision details
- Test code may directly instantiate and use repositories for isolation
- Service layers are the public contract between modules

**Not Allowed:**
- Direct SQL queries from outside the module's repository
- Bypassing the repository to directly instantiate ORM models
- Cross-module writes (e.g., revision module writing to document table)
- Repositories calling repositories from other modules

## Error Handling

### Database Errors

**`IntegrityError`:** Raised by SQLAlchemy when a constraint is violated.
- `DatabaseDocumentRepository` catches and converts to `DuplicateNormalizedTitleError`
- `DatabaseRevisionRepository` lets FK errors bubble up (FK constraint validates existence)

**`NoResultFound` / `NoReturn`:** Raised when a scalar query finds no row.
- Repositories handle this by returning `None`, not raising exceptions
- Example: `get("nonexistent")` returns `None`

### Domain Errors

**`DuplicateNormalizedTitleError`:** Raised when creating a document with a title that already exists (after normalization).
- Both `InMemoryDocumentRepository` and `DatabaseDocumentRepository` raise this
- Caught by `DocumentService` to prevent duplicate documents

**`DocumentNotFoundError`:** Raised when updating a document that does not exist.
- Raised by both repository implementations
- Prevents silent failures when a document has been deleted

**`EmptyTitleError`:** Raised by `normalize_title()` when a title is empty or whitespace-only.
- Raised before repository access, in the service layer

## Migration and Schema Evolution

Migrations are defined in `migrations/versions/` and applied by Alembic.

**Schema ownership by module:**
- Document module owns migrations for `document` table
- Revision module owns migrations for `revision` table
- Persistence module provides base infrastructure

**Rules:**
- Never drop a column without explicit deprecation period
- Add columns with NOT NULL only if a default is provided
- Foreign key constraints are mandatory, not optional
- Indexes should be added as part of the schema migration, not after

**Example migration for document table** (`0002_add_document_table.py`):
- Defines `document` table with columns, constraints, and defaults
- Creates UNIQUE constraint on `normalized_title`
- Downgrade reverses the table creation

## Testing Strategy

### Unit Tests

Test repositories in isolation using in-memory implementations:

```python
async def test_repository():
    repo = InMemoryDocumentRepository()
    doc = Document(id="doc1", title="Test")
    created = await repo.create(doc)
    assert created.id == "doc1"
```

**Benefits:**
- No database setup required
- Tests run in microseconds
- Easy to mock complex scenarios
- Verify contract (interface) not implementation

### Integration Tests

Test repositories with a real database (async SQLite or PostgreSQL):

```python
@pytest.fixture
async def async_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # ... session creation ...

async def test_repository_with_db(async_db_session):
    repo = DatabaseDocumentRepository(async_db_session)
    # Test against real database
```

**Benefits:**
- Validate actual database behavior
- Catch SQL errors, constraint violations
- Test transaction rollback and isolation

### End-to-End Tests

Test the full stack: HTTP → Service → Repository → Database:

```python
async def test_create_document_via_api():
    response = await client.post("/documents", json={"title": "Test"})
    assert response.status_code == 201
    # Verify document was created in database
```

**Benefits:**
- Validate actual API contracts
- Catch serialization errors
- Test error responses and HTTP semantics

## Common Patterns

### Creating a Document with Initial Revision

```python
# Service layer orchestrates both modules atomically
async def create_document_with_revision(
    transaction: DocumentRevisionTransaction,
    title: str,
    source: str,
    author_id: str,
) -> tuple[Document, Revision]:
    doc_id = str(uuid.uuid4())
    rev_id = str(uuid.uuid4())
    
    document = Document(id=doc_id, title=title, current_revision_id=rev_id)
    revision = Revision(
        id=rev_id,
        document_id=doc_id,
        source=source,
        author_id=author_id,
        summary="Initial revision",
    )
    
    doc, rev = await transaction.create_document_with_revision(document, revision)
    return doc, rev
```

### Fetching Current Revision

```python
# Service layer provides read model
async def get_current_revision(
    doc_repo: DocumentRepository,
    rev_repo: RevisionRepository,
    document_id: str,
) -> Optional[Revision]:
    doc = await doc_repo.get(document_id)
    if doc is None or doc.current_revision_id is None:
        return None
    return await rev_repo.get(doc.current_revision_id)
```

### Listing All Revisions

```python
# Service layer delegates to repository
async def list_document_revisions(
    rev_repo: RevisionRepository,
    document_id: str,
) -> list[Revision]:
    return await rev_repo.list_by_document_id(document_id)
```

## Future Considerations

### Read Replicas

If read scaling is needed:
- DocumentRepository and RevisionRepository currently use a single session
- Extended to use a read session for queries, write session for mutations
- No code changes in modules; only inject different sessions

### Soft Deletes

If document deletion is needed:
- Add `deleted_at: DateTime(tz) | NULL` column to `document` and `revision` tables
- Repositories filter out deleted rows in queries
- Service layer handles "deleted" state

### Partitioning

If table growth requires partitioning:
- Partition by document_id in the revision table (time-series data)
- Queries by document_id naturally align with partitions
- No code changes; handled by database migration

### Event Sourcing

If audit trail is needed:
- Create `document_events` table with event log
- Repositories emit events after successful writes
- Service layer subscribes to events for search indexing, cache purges
- Revision table already supports this pattern (append-only)
