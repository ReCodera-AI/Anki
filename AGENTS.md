# Anki Project Workflow Rules

These rules apply to contributors, developers, and AI agents. Follow the repository's existing architecture and conventions, keep changes focused, and verify work before reporting completion.

## Project Map

- `ts/`: Svelte and TypeScript frontend.
- `qt/aqt/`: PyQt user interface and embedded web components.
- `pylib/anki/`: Python collection and library layer; `pylib/rsbridge/` connects it to Rust.
- `rslib/`: Core Rust implementation.
- `proto/`: Protocol Buffer definitions shared across layers.
- `ftl/core/`, `ftl/qt/`: Fluent translations. Prefer `ftl/core/` unless a string is Qt-specific.
- `qt/installer/`: Briefcase installer and platform templates.
- `docs-site/`: User and developer documentation.
- `justfile`: Canonical build, run, format, lint, and test recipes.
- `out/`: Generated build output; do not edit generated files as source.

## Workflow

1. Inspect repository status and relevant source before editing. Preserve unrelated user changes; never reset or overwrite them.
2. Make the smallest focused change that satisfies the task. Avoid unrelated refactoring and generated output.
3. Add or update tests for behavior changes. Before changing unit/component tests, read `docs-site/developers/unit-testing.mdx`.
4. Run the narrowest relevant checks, then broader checks when appropriate. Report exact commands and outcomes; distinguish failures from environmental blockers.
5. Review the diff for correctness, scope, formatting, and accidental artifacts before finishing.

## Build, Run, Format, And Test

- Use `just --list` to discover recipes; use `just` recipes as the standard interface.
- Run development Anki with `just run`; use `just run-optimized` for optimized builds.
- Use `just web-watch` for frontend live reload and `just rebuild-web` for a one-off web rebuild.
- Use `just check` for the full formatting/build/check workflow when feasible.
- Focused checks: `just test-rust`, `just test-py`, `just test-ts`, `just test-e2e`, and `just lint`.
- Format with `just fmt`; use `just fix-fmt`, `just fix-lint` only when formatting or lint fixes are intended.
- Do not invoke `./ninja`, `./run`, or scripts under `./tools` directly; use the repository recipes.
- Changes to `.proto` files may require `just check` to regenerate and validate cross-layer code.

## Implementation Rules

- Preserve existing APIs, architecture, naming, comments, and error-handling conventions unless the task requires otherwise.
- In Rust, prefer workspace dependencies with `dep.workspace = true`; use `AnkiError`/`Result` and `snafu` in `rslib`, and `anyhow` with context elsewhere where appropriate. Unwraps are acceptable in build scripts and tests.
- Reuse `rslib/{process,io}` helpers for process and file operations when suitable.
- Keep protobuf and IPC changes consistent across `proto/`, Rust, Python bridge, and generated TypeScript interfaces.
- Never hand-edit generated translation APIs or files under `out/`.

## Fluent Translations

- Add new translation messages to the appropriate Fluent source under `ftl/`; ask the maintainer when the correct file is unclear. Prefer `ftl/core/`, except for Qt-only strings.
- The Fluent system generates language APIs. For a message `addons-you-have-count` in `addons.ftl`, use:
  - Python: `from aqt.utils import tr; msg = tr.addons_you_have_count(count=3)`
  - TypeScript: `import * as tr from "@generated/ftl"; tr.addonsYouHaveCount({count: 3})`
  - Rust: `collection.tr.addons_you_have_count(3)`
- In Qt `.ui` files, translatable widgets resolve registered Fluent message identifiers automatically.

## Change And Git Hygiene

- Keep changes within the requested scope and do not include unrelated modifications in commits.
- Stage only files belonging to one focused concern. Use clear conventional commit messages when asked to commit or when project policy requires a commit.
- Do not push, merge, or rewrite shared history without explicit authorization.
- Before finishing, inspect `git diff`, `git diff --check`, and `git status`; leave unrelated pre-existing changes untouched and disclose them.
- Do not commit generated build artifacts, caches, temporary profiles, or test output.

## Troubleshooting And Reporting

- When builds or tests fail, preserve the exact error, identify whether it is a code failure or an environment/dependency issue, and try a focused alternative check where possible.
- Do not hide or reclassify a failed check as passed. Mark checks as `PASS`, `FAIL`, or `UNVERIFIED` and state the evidence.
- Treat `out/` as generated; it may be useful to inspect generated cross-language output but must not become the source of a change.

## Contributor References

- Contribution instructions: `docs/contributing.md`.
- Development setup: `docs/development.md`.
- Unit testing guide: `docs-site/developers/unit-testing.mdx`.
- Individual contributor listing: `CONTRIBUTORS`.
- Installer implementation: `qt/installer/`.
