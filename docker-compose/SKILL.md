---
name: docker-compose
description: Docker Compose V2 and Compose Specification expertise for writing correct compose.yaml and docker-compose.yml files. Use when the user mentions Docker Compose, compose.yaml, docker-compose.yml, docker compose CLI, multi-container apps, profiles, healthchecks, depends_on, networks, volumes, secrets, build contexts, or avoiding deprecated V1 patterns.
---

# Docker Compose V2 Expert

Use this skill to write, review, and modernize Docker Compose files using the current Compose Specification and `docker compose` V2 CLI.

## Current Facts

- The top-level `version` property is obsolete. Compose keeps it only for backward compatibility and warns when it is used.
- Compose validates against the most recent schema regardless of `version`.
- Use `docker compose`, not the old standalone `docker-compose` command, unless supporting a pinned legacy environment.
- Default file names are `compose.yaml` and `compose.yml`; `docker-compose.yml` remains widely supported.
- Root-level keys commonly include `services`, `networks`, `volumes`, `configs`, and `secrets`.
- Current example image majors as of June 2026: PostgreSQL 18 and Redis 8. Pin exact patch/minor versions for production.

## How To Use

1. Start with `services:` and no `version:` field.
2. Add only the networks, volumes, secrets, configs, profiles, and build settings required for the user’s workflow.
3. Use healthchecks plus long-form `depends_on` when startup readiness matters.
4. Bind sensitive ports to `127.0.0.1` unless external access is required.
5. For deeper templates and examples, consult [full-reference.md](references/full-reference.md). Treat older image tags there as examples to refresh before use.

## Review Checklist

- No top-level `version:`.
- `services:` is plural and at the root.
- Service names are stable and lowercase.
- Images are pinned for production; avoid `latest` except in disposable examples.
- Secrets are not embedded in YAML; use env vars, `.env`, secret files, or platform secrets.
- Persistent database state uses named volumes.
- Development bind mounts are explicit and use `:ro` when possible.
- Healthchecks use commands available inside the image.
- Resource limits are explicit where runaway memory/CPU use is risky.

## Common Patterns

- PostgreSQL: use `postgres:18-alpine` for current examples unless project requirements say otherwise.
- Redis: use `redis:8-alpine` for current examples unless project requirements say otherwise.
- Internal databases should usually live only on a backend network and avoid host port exposure.
- Use `profiles` for optional services such as observability, admin tools, or one-off jobs.
- Use `docker compose config` to validate rendered configuration.

## Update Checklist

- Recheck Docker Compose docs for newly added keys such as `develop`, `interface_name`, or pull policy support before recommending them.
- Recheck upstream image tags before refreshing examples.
- Keep this `SKILL.md` concise; move long templates to `references/`.
