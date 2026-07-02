# admin

Administrative workflows.

Owns blocks, protections, reports, moderation actions, dashboards, and
operational controls.

## Admin and Audit Integration

### Audit Event Generation

The admin module generates audit events whenever administrative actions occur:

- `AdminBlockService` creates `AdminBlockAuditEvent` when blocks are created or deleted
- `AdminProtectionService` creates `AdminProtectionAuditEvent` when protections are created or deleted

Each service accumulates events in memory as actions are performed. Callers retrieve these events via the `events()` method to inspect the audit trail for that service instance.

### Event Generation Boundary

**What the admin services own:**
- Creating and managing the underlying resources (blocks, protections)
- Generating domain-specific audit events during those operations
- Maintaining an in-memory event list for the service's lifetime
- Exposing events to the caller

**What admin does NOT own:**
- Persisting audit events to durable storage (audit module's responsibility)
- Querying historical events (audit module's responsibility)
- Enforcing audit policies (audit module's responsibility)

### Audit Event Structure

Admin audit events capture:

- `id`: Unique event identifier
- `action`: The specific action taken (e.g., `BLOCK_CREATED`, `PROTECTION_DELETED`)
- `resource_id`: The block or protection ID affected by the action
- `occurred_at`: When the action occurred
- `actor_id`: Who performed the action (optional)

### Integration with Audit Module

The admin module does NOT depend on the audit module directly. Instead:

1. Admin services generate audit events as side effects of operations
2. Callers retrieve these events from the service
3. Callers (or higher-level orchestrators) are responsible for persisting these events to the audit module

This separation allows admin logic to remain independent of audit storage concerns and enables the audit module to handle all event types (document, permission, auth, etc.) uniformly.
