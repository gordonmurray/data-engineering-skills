---
name: docker-compose
description: Write, review, and modernize Docker Compose files against the current Compose Specification and the docker compose CLI. Use for authoring compose.yaml or docker-compose.yml, service dependency and healthcheck ordering, profiles, networks, volumes, secrets and configs, build contexts, migrating off V1 and the obsolete version key, or containers that fail to start, restart-loop, report unhealthy, or lose data between runs.
license: MIT
---

# Docker Compose Expert

## Scope

Writing, reviewing, and modernizing Compose files using the current Compose
Specification and the `docker compose` CLI, plus local multi-container
workflows.

Not a Kubernetes or Swarm skill. When a user needs production orchestration,
say so rather than stretching Compose to fit.

## Current Facts

- **Supported CLI lines are Compose v2 and Compose v5**, both defined by the Compose Specification. Current release is v5.3.1, July 7, 2026. Docker skipped 3.x and 4.x deliberately, to avoid confusion with the obsolete v1 file-format versions 2.x and 3.x.
- The top-level `version` property is obsolete. Compose keeps it only for backward compatibility and warns when it is used.
- Compose validates against the most recent schema regardless of `version`.
- Use `docker compose`, not the old standalone `docker-compose` command, unless supporting a pinned legacy environment. V1 reached end of life in June 2023.
- Default file names are `compose.yaml` (preferred) and `compose.yml`; `docker-compose.yaml` and `docker-compose.yml` remain supported. Compose prefers `compose.yaml` when both exist.
- Top-level keys are `version`, `name`, `include`, `services`, `models`, `networks`, `volumes`, `secrets`, and `configs`.
- **Recent additions:** service-level `pre_start` for native init containers, added in Compose v5.3.0 (July 2026); `restart: on-failure:<max-retries>`; `build.no_cache_filter`; and `docker compose start --wait`.
- Compose v5.0.0 removed the internal BuildKit builder and delegates builds to Docker Bake, the same path as `docker build`.
- Current example image majors as of July 2026: PostgreSQL 18 (18.4) and Redis 8 (8.8.1). Pin exact patch/minor versions for production.

## Inspect First

Establish before recommending or changing anything:

1. Read the existing Compose file in full before editing. Preserve service
   names, networks, and volumes the user already depends on.
2. Confirm Compose V2 is in use via `docker compose version`, not the
   standalone V1 binary.
3. Identify which services hold persistent state and which ports are currently
   published to the host.
4. For startup failures, read `docker compose ps` and the actual container
   logs before changing configuration. Most restart loops are an application
   error, not a Compose error.

## Authoring Rules

- Start with `services:` and no `version:` field.
- Add only the networks, volumes, secrets, configs, profiles, and build
  settings the workflow actually needs.
- Use healthchecks plus long-form `depends_on` with `condition:
  service_healthy` when startup order matters. Plain `depends_on` waits for
  the container to start, not for the service to be ready.
- Bind sensitive ports to `127.0.0.1` unless external access is required.
- Keep internal databases on a backend network with no host port published.
- Use service-level `pre_start` for migrations, permission fixes, and other
  init work, rather than the older pattern of a one-off service plus
  `depends_on`. Each step runs in an ephemeral container before the service
  starts, in declared order, and a non-zero exit fails the service and its
  dependents. This differs from `post_start` and `pre_stop`, which run inside
  the running service container.
- Use `profiles` for optional services such as observability, admin tools, or
  one-off jobs.
- Use `postgres:18-alpine` and `redis:8-alpine` for current examples unless
  project requirements say otherwise.

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

## Safety

- `docker compose down -v` deletes named volumes and everything in them. Never
  offer it as a generic reset without stating that database contents will be
  destroyed, and confirm first.
- A bare `5432:5432` publishes the database on every host interface. Use
  `127.0.0.1:5432:5432` unless remote access is genuinely required.
- Keep secrets out of committed YAML and never echo secret values into output
  or logs.
- Renaming a named volume silently orphans the old data rather than migrating
  it. Confirm before changing volume definitions on a running stack.

## Verify

- Run `docker compose config` to confirm the file parses and to inspect the
  rendered result, including variable interpolation.
- Bring the stack up and confirm `docker compose ps` reports the expected
  services as healthy, not merely running.
- Confirm each healthcheck command exists inside its image. A healthcheck
  calling `curl` in an image without curl reports unhealthy forever.
- For stateful services, confirm data survives `docker compose down` followed
  by `docker compose up`.
- Report which services you started, their health status, and anything you
  could not test.

## Update Checklist

- Recheck Docker Compose docs for newly added keys before recommending them, for example `develop`, `pre_start`, or the service-level `networks.<name>.interface_name`.
- Recheck upstream image tags before refreshing examples.
