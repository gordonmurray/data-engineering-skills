#!/usr/bin/env python3
"""Validate the skill catalogue against this repository's structural rules.

Checks frontmatter validity, naming, required sections, file size, directory
layout, relative links, and README coverage. Run before opening a pull request:

    python3 .github/scripts/validate_skills.py

Exits 0 when every skill passes and 1 otherwise.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install it with: pip install pyyaml")

REPO = pathlib.Path(__file__).resolve().parents[2]

MAX_DESCRIPTION = 1024
MAX_NAME = 64
MAX_LINES = 500

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
SECTION = re.compile(r"^## (.+)$", re.MULTILINE)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

REQUIRED_SECTIONS = (
    "Scope",
    "Inspect First",
    "Safety",
    "Verify",
    "Update Checklist",
)

# A skill directory holds only resources the agent uses to perform the skill.
# Anything else, authoring notes included, is clutter. Contents of the resource
# directories are not policed by name; dotfiles are ignored as tooling.
ALLOWED_FILES = ("SKILL.md",)
ALLOWED_DIRS = ("references", "scripts", "assets")
LAYOUT_HINT = "a skill directory holds only SKILL.md plus references/, scripts/, and assets/"


def skill_dirs(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def check_skill(directory: pathlib.Path) -> tuple[list[str], str | None, int, int]:
    """Return (errors, skill name, line count, description length)."""
    errors: list[str] = []
    skill_md = directory / "SKILL.md"

    if not skill_md.exists():
        return ([f"no SKILL.md in {directory.name}/"], None, 0, 0)

    for entry in sorted(directory.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            if entry.name not in ALLOWED_DIRS:
                errors.append(f"unexpected directory {entry.name}/; {LAYOUT_HINT}")
        elif entry.name not in ALLOWED_FILES:
            errors.append(f"unexpected file {entry.name}; {LAYOUT_HINT}")

    text = skill_md.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    if line_count > MAX_LINES:
        errors.append(f"SKILL.md is {line_count} lines, over the {MAX_LINES} line ceiling")

    match = FRONTMATTER.match(text)
    if not match:
        errors.append("missing YAML frontmatter delimited by --- on the first line")
        return (errors, None, line_count, 0)

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        errors.append(f"frontmatter is not valid YAML: {exc}")
        return (errors, None, line_count, 0)

    if not isinstance(meta, dict):
        errors.append("frontmatter must be a YAML mapping")
        return (errors, None, line_count, 0)

    name = meta.get("name")
    if not isinstance(name, str) or not name:
        errors.append("frontmatter is missing a name")
        name = None
    else:
        if name != directory.name:
            errors.append(f'name "{name}" does not match directory "{directory.name}"')
        if not NAME_PATTERN.match(name):
            errors.append(f'name "{name}" must be lowercase kebab case')
        if len(name) > MAX_NAME:
            errors.append(f"name is {len(name)} characters, over the {MAX_NAME} limit")

    description = meta.get("description")
    desc_len = 0
    if not isinstance(description, str) or not description.strip():
        errors.append("frontmatter is missing a description")
    else:
        desc_len = len(description)
        if desc_len > MAX_DESCRIPTION:
            errors.append(
                f"description is {desc_len} characters, over the {MAX_DESCRIPTION} limit"
            )

    sections = SECTION.findall(text)
    for required in REQUIRED_SECTIONS:
        if required not in sections:
            errors.append(f"missing required section: ## {required}")

    for target in MD_LINK.findall(text):
        target = target.split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        if not (directory / target).exists():
            errors.append(f"broken relative link: {target}")

    return (errors, name, line_count, desc_len)


def check_readme(root: pathlib.Path, dir_names: list[str]) -> list[str]:
    readme = root / "README.md"
    if not readme.exists():
        return ["no README.md at the repository root"]

    text = readme.read_text(encoding="utf-8")
    listed = {
        t.split("/", 1)[0]
        for t in MD_LINK.findall(text)
        if t.endswith("/SKILL.md") and "://" not in t
    }

    errors = []
    for missing in sorted(set(dir_names) - listed):
        errors.append(f"README does not list the {missing} skill")
    for stale in sorted(listed - set(dir_names)):
        errors.append(f"README links to {stale}/SKILL.md, which does not exist")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=REPO,
        help="repository root to validate (default: this repository)",
    )
    args = parser.parse_args()

    directories = skill_dirs(args.root)
    if not directories:
        print(f"No skill directories found in {args.root}")
        return 1

    failed = 0
    dir_names: list[str] = []
    seen: dict[str, str] = {}

    for directory in directories:
        errors, name, lines, desc_len = check_skill(directory)
        dir_names.append(directory.name)

        if name:
            if name in seen:
                errors.append(f'duplicate skill name, also used by {seen[name]}/')
            seen[name] = directory.name

        if errors:
            failed += 1
            print(f"FAIL  {directory.name}")
            for error in errors:
                print(f"        {error}")
        else:
            print(f"ok    {directory.name:<16} {lines:>3} lines, description {desc_len} chars")

    readme_errors = check_readme(args.root, dir_names)
    if readme_errors:
        failed += 1
        print("FAIL  README.md")
        for error in readme_errors:
            print(f"        {error}")

    print()
    if failed:
        print(f"{failed} check group(s) failed")
        return 1

    print(f"All {len(directories)} skills passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
