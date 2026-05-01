# Changelog

## 0.6.2 — 2026-05-01

### NEW

- Per-entry `environment` stamping on `RegistryEntry`. Captured from
  the `X-Environment` header at registration time and persisted as a
  column on the `services` table. Lookups that include `X-Environment`
  filter results to matching entries (defense-in-depth: cross-env
  enumeration is no longer possible). Unauthenticated reads without
  the header still return everything.

## 0.5.1 — 2026-05-01

### Fixed
- Docker image: pre-create `/var/lib/registry` with `appuser` ownership so
  volume mounts at that path are writable by the runtime user. Without
  this fix, mounting a named volume produces `sqlite3.OperationalError:
  unable to open database file` on startup. (Reported during ai-dev-stack
  v0.5.0 integration.)

## 0.5.0 — 2026-05-01

Initial release. Registry server + read-only HTML UI. Hybrid model:
optional YAML seed declares "expected" services; live registrations
happen via POST /api/services on each component's startup.

Built against `enterprise-ai-platform-sdk` 0.5.0 + the
`ghcr.io/narisun/ai-python-base:3.11-sdk0.5.0` base image.
