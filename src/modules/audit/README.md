# audit

Immutable event logs.

Owns document logs, admin logs, permission logs, auth logs, job logs, and other
append-only records.

## Admin Module Integration

### Receiving Admin Events

The audit module receives audit events from the admin module (and other modules) to persist them durably:

- `AdminBlockAuditEvent` records when user blocks are created or deleted
- `AdminProtectionAuditEvent` records when document protections are created or deleted

### Event Ingestion Boundary

**What the audit module owns:**
- Accepting events from all domains (admin, document, permission, auth, jobs, etc.)
- Persisting events to durable append-only storage
- Querying and retrieving historical events
- Enforcing audit policies (immutability, retention, etc.)

**What audit does NOT own:**
- Generating events (each domain generates its own events)
- Business logic around the events (admin, document modules own that)
- Deciding when events should be recorded (domain modules decide that)

### Event Flow

1. Admin service performs an operation and generates an audit event
2. Admin service returns the event to its caller (via `events()` method)
3. Caller is responsible for submitting the event to the audit module for persistence
4. Audit module stores the event in append-only storage
5. Later queries can retrieve the full event history

### Event Normalization

Admin audit events use domain-specific types (`AdminBlockAuditEvent`, `AdminProtectionAuditEvent`) during generation. When persisted to the audit module, these may be converted to the common `AuditEvent` type to enable uniform querying across all event types.

### Immutability Contract

Once an audit event is persisted to the audit module, it cannot be modified or deleted. This ensures an accurate and tamper-proof record of all administrative actions.
