# Data Engineering Skills for Claude

Expert knowledge skills for Claude Code and Claude.ai covering modern data
engineering technologies: table formats, stream processing, streaming storage,
ML-native formats, and local orchestration.

Each skill follows the
[Anthropic Agent Skills](https://claude.com/blog/skills) standard:
a folder containing a `SKILL.md` with YAML frontmatter that Claude loads on
demand when the trigger conditions match.

## Available Skills

| Skill | Domain | File |
| --- | --- | --- |
| **Apache Iceberg** | Open table format / lakehouse | [`iceberg/SKILL.md`](iceberg/SKILL.md) |
| **Apache Paimon** | Streaming lake format | [`paimon/SKILL.md`](paimon/SKILL.md) |
| **Apache Fluss** | Streaming storage for real-time analytics | [`fluss/SKILL.md`](fluss/SKILL.md) |
| **Apache Flink** | Stream processing framework | [`flink/SKILL.md`](flink/SKILL.md) |
| **Apache Iggy** | Rust-native message streaming | [`iggy/SKILL.md`](iggy/SKILL.md) |
| **Lance** | Columnar format for ML/AI + vector search | [`lance/SKILL.md`](lance/SKILL.md) |
| **Docker Compose** | Container orchestration (V2+) | [`docker-compose/SKILL.md`](docker-compose/SKILL.md) |

## How Skills Work

Skills use the Agent Skills progressive disclosure model:

1. **YAML frontmatter** (always loaded). `name` and `description` tell Claude
   when the skill is relevant.
2. **`SKILL.md` body** (loaded on trigger). Core instructions and guidance.
3. **Bundled files** (optional, loaded on demand). Deeper references, scripts,
   or templates referenced from `SKILL.md`.

The current skills intentionally keep only concise `SKILL.md` files. Add
`references/`, `scripts/`, or `assets/` only when a skill needs substantial
offline detail, deterministic helpers, or reusable output assets.

## Using These Skills

### Claude Code

Place a skill folder (or symlink it) into `~/.claude/skills/` or a project
`.claude/skills/` directory. Claude Code discovers `SKILL.md` files
automatically and loads them based on the frontmatter `description`.

Alternatively, reference a skill file directly in a conversation:

```
@iceberg/SKILL.md help me migrate an Iceberg v2 table to v3 deletion vectors
```

### Claude.ai

Zip a skill folder and upload via **Settings → Capabilities → Skills**.

### Claude API

Pass the skill via `container.skills` on the Messages API (requires the Code
Execution Tool beta). See
[Using Agent Skills with the API](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

## Skill Structure

Each skill conforms to the Agent Skills standard:

```
skill-name/
└── SKILL.md     # Required: YAML frontmatter + Markdown instructions
```

Minimum frontmatter:

```yaml
---
name: skill-name
description: What the skill does and when Claude should use it (trigger phrases).
---
```

## Contributing

To add a new skill:

1. Create a kebab-case folder: `your-skill-name/`.
2. Add a `SKILL.md` with valid YAML frontmatter (`name` matches the folder;
   `description` includes both *what it does* and *when to use it*, with
   specific trigger phrases).
3. Keep `SKILL.md` focused; move deep reference material to `references/` and
   executable helpers to `scripts/` within the skill folder.
4. Update the table above.

For full authoring guidance, see Anthropic's
[Complete Guide to Building Skills for Claude][guide] (PDF, ~33 pages) and the
[Skill authoring best practices][best-practices] documentation.

[guide]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf
[best-practices]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
