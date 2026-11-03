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

Release guidance checked on **2026-11-03**. Recheck the linked sources before
selecting versions for a new deployment; preserve existing project pins.

- **Current CLI release:** Compose v5.7.0, published November 2, 2026. Existing installations may still run v2; inspect the binary before using newer features. CLI major versions are separate from obsolete Compose file-format versions.
- The top-level `version` property is obsolete. Compose keeps it only for backward compatibility and warns when it is used.
- Compose validates against the most recent schema regardless of `version`.
- Use `docker compose`, not the old standalone `docker-compose` command, unless supporting a pinned legacy environment. V1 reached end of life in June 2023.
- Default file names are `compose.yaml` (preferred) and `compose.yml`; `docker-compose.yaml` and `docker-compose.yml` remain supported. Compose prefers `compose.yaml` when both exist.
- Common top-level keys include `name`, `include`, `services`, `models`, `networks`, `volumes`, `secrets`, and `configs`; validate newer keys against the installed CLI.
- **Recent additions gated on a CLI version:** service-level `pre_start` for native init containers needs v5.3.0 (July 2026); `build.no_cache_filter` and `docker compose start --wait` need v5.0.0. None of these are available on Compose v2.
- **Jobs:** v5.6 introduced partial support for manually triggered jobs. Do not assume scheduled-job support from the existence of the `jobs` model; check the target CLI and Engine capabilities.
- `restart` accepts `no`, `always`, `on-failure[:max-retries]`, and `unless-stopped`, with no version gate on any of them. The `on-failure` retry limit is long-standing; its spec wording was clarified in February 2026, which is not the same as being new.
- Compose v5.0.0 removed the internal BuildKit builder and delegates builds to Docker Bake, the same path as `docker build`.
- `postgres:18-alpine` and `redis:8-alpine` remain available example tags. These floating tags are not production pins or permission to upgrade existing database storage.

## Inspect First

Establish before recommending or changing anything:

1. Read the existing Compose file in full before editing. Preserve service
   names, networks, and volumes the user already depends on.
2. Read the CLI version from `docker compose version`, and confirm it is not
   the standalone V1 binary. The version gates which keys are available:
   `pre_start` needs v5.3.0 or newer.
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
- Check the CLI version before using a recently added key. A v5-only key may
  be rejected or ignored by older tooling; successful YAML parsing alone does
  not prove the requested behavior is supported.
- For migrations, permission fixes, and other init work on **Compose v5.3.0 or
  newer**, use service-level `pre_start`. Each step runs in an ephemeral
  container before the service starts, in declared order, and a non-zero exit
  fails the service and its dependents. This differs from `post_start` and
  `pre_stop`, which run inside the running service container.
- On Compose v2, `pre_start` does not exist. Use a one-shot init service plus
  `depends_on: {init: {condition: service_completed_successfully}}` instead.
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

## Sources

- [Compose v5.7.0 release](https://github.com/docker/compose/releases/tag/v5.7.0)
- [Compose v5.6.0 job support limitations](https://github.com/docker/compose/releases/tag/v5.6.0)
- [Compose file reference](https://docs.docker.com/reference/compose-file/)
- [Official PostgreSQL image](https://hub.docker.com/_/postgres) and [Redis image](https://hub.docker.com/_/redis)
