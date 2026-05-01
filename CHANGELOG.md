# Changelog

## 0.5.0 — 2026-05-01

Initial release. Registry server + read-only HTML UI. Hybrid model:
optional YAML seed declares "expected" services; live registrations
happen via POST /api/services on each component's startup.

Built against `enterprise-ai-platform-sdk` 0.5.0 + the
`ghcr.io/narisun/ai-python-base:3.11-sdk0.5.0` base image.
