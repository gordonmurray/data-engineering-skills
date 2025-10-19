# Claude Code Skills

Expert knowledge skills for Claude Code to help with specific technologies and tools.

## What are Skills?

Skills are specialized knowledge modules that extend Claude Code's expertise in specific domains. When invoked, a skill provides detailed context, best practices, code examples, and troubleshooting guidance for a particular technology.

## Available Skills

This repository contains skills for:

- **Apache Lance** - Modern columnar data format for ML/AI applications
- **Docker Compose** - Container orchestration with modern V2+ syntax

See individual skill directories for detailed documentation.

## How to Use Skills in Claude Code

### Option 1: Direct File Reference (Recommended)

Reference a skill file directly in your conversation:

```
@lance/lance.md help me create a Lance dataset with vector search
```

or

```
@docker-compose/docker-compose.md write a compose file for a Django app with Postgres and Redis
```

### Option 2: Add as Context

Add skill files to your Claude Code context:
1. Use `@` to reference files
2. Ask questions or request help with that technology
3. Claude will use the skill's expertise to provide accurate, up-to-date guidance

### Option 3: Copy to Project

Copy relevant skill files into your project's `.claude/` directory for project-specific reference.

## Skill Structure

Each skill is organized in its own directory:

```
skills/
├── lance/
│   └── lance.md
├── docker-compose/
│   └── docker-compose.md
└── README.md
```

## Creating Your Own Skills

Skills are markdown files containing:

1. **Expert context** - Positioning Claude as an expert in the domain
2. **Version information** - Current versions and compatibility notes
3. **Core concepts** - Key terminology and architecture
4. **Common operations** - Practical code examples
5. **Best practices** - Performance tips and patterns
6. **Troubleshooting** - Common errors and solutions
7. **Quick reference** - Checklists and command summaries

Structure your skill to provide comprehensive, actionable guidance that helps Claude Code generate correct, modern code.

## Benefits

- **Accurate answers** - Skills provide current, version-specific information
- **Best practices** - Learn recommended patterns and avoid deprecated syntax
- **Code examples** - Working templates you can adapt immediately
- **Troubleshooting** - Quick solutions to common problems
- **Consistency** - Get uniform guidance across your team

## Contributing

Add new skills by creating a directory with a descriptive markdown file. Follow the existing skill structure for consistency.
