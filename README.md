# ai-registry

Enterprise AI Platform — service catalog, health monitoring, and name-based discovery for the platform's runtime services. Every agent and MCP server self-registers on startup; this service is the single bootstrap URL the rest of the platform uses to find peers.

## Quick start

```bash
pip install -r requirements.txt
INTERNAL_API_KEY=$(openssl rand -hex 32) uvicorn src.app:app --host 0.0.0.0 --port 8090
```

Open the read-only catalog UI at http://localhost:8090.

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `REGISTRY_PORT` | `8090` | Listen port |
| `INTERNAL_API_KEY` | (required) | Bearer token required for write ops |
| `SQLITE_PATH` | `/var/lib/registry/registry.db` | SQLite file path |
| `SEED_PATH` | (unset) | Optional `registry.yaml` seed |
| `HEARTBEAT_GRACE_SECONDS` | `60` | Time before heartbeat-less services go `stale` |
| `EVICTION_SECONDS` | `300` | Time before stale services are evicted |
| `REAPER_INTERVAL_SECONDS` | `30` | How often the reaper runs |

## Endpoints

- `GET /api/services` — list catalog (no auth)
- `GET /api/services/{name}` — single entry (no auth)
- `POST /api/services` — register (Bearer auth)
- `DELETE /api/services/{name}` — deregister (Bearer auth)
- `POST /api/services/{name}/heartbeat` — heartbeat (Bearer auth)
- `GET /health` — registry's own liveness (no auth)
- `GET /` — read-only catalog UI

## Container

```bash
docker pull ghcr.io/narisun/ai-registry:0.5.0
docker run --rm -p 8090:8090 \
  -e INTERNAL_API_KEY=secret \
  -v ai-registry-data:/var/lib/registry \
  ghcr.io/narisun/ai-registry:0.5.0
```

## See also

- Spec: [`docs/specs/2026-04-30-service-registry-design.md` in narisun/ai-platform-sdk](https://github.com/narisun/ai-platform-sdk/blob/main/docs/specs/2026-04-30-service-registry-design.md)
- Client API: `platform_sdk.registry.RegistryClient` (in narisun/ai-platform-sdk)
