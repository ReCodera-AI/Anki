# Anki

[![Build Status](https://github.com/ankitects/anki/actions/workflows/ci.yml/badge.svg)](https://github.com/ankitects/anki/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/badge/docs-dev--docs.ankiweb.net-blue)](https://dev-docs.ankiweb.net/en/latest/)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=ankitects_anki&metric=coverage)](https://sonarcloud.io/summary/new_code?id=ankitects_anki)

> This repository contains the source code for Anki's desktop application. The project combines a web frontend, a Qt desktop interface, Python libraries, and a Rust core.

This repo contains the source code for the computer version of
[Anki](https://apps.ankiweb.net).

## About

Anki is a spaced repetition program. Please see the [website](https://apps.ankiweb.net) to learn more.

The desktop application is developed as a multi-layer project. Its frontend and native interface communicate with the Python collection layer and Rust core; Protocol Buffers define interfaces shared between these components. Fluent files provide the source for translated interface messages.

## Repository Guide

| Path | Purpose |
| --- | --- |
| `ts/` | Svelte and TypeScript frontend, including browser-based end-to-end tests in `ts/tests/e2e/`. |
| `qt/aqt/` | PyQt desktop interface and embedded web application integration. |
| `pylib/anki/` | Python collection and application library. `pylib/rsbridge/` connects Python to Rust. |
| `rslib/` | Rust core implementation and services. |
| `proto/` | Protocol Buffer definitions used across application layers. |
| `ftl/core/`, `ftl/qt/` | Fluent translation source files for shared and Qt-specific messages. |
| `docs/` | Contributor guidance and development setup documentation. |
| `docs-site/` | Anki user and developer documentation, including the unit testing guide. |
| `qt/installer/` | Briefcase-based installer and platform-specific templates. |
| `justfile` | Canonical recipes for running, building, formatting, linting, and testing. |
| `AGENTS.md` | Project workflow, implementation, translation, and verification rules for contributors and AI agents. |
| `CONTRIBUTORS` | List of project contributors. |
| `LICENSE` | Project license. |

Build output is generated under `out/`; treat it as disposable output and make source changes in the corresponding source directories instead.

## Getting Started

### Contributing

Want to contribute to Anki? Check out the [Contribution Guidelines](./docs/contributing.md).

For more information on building and developing, please see [Development](./docs/development.md).

Before making changes, review [Project Workflow Rules](./AGENTS.md). Build and development tasks are exposed as recipes in `justfile`; run `just --list` to see the available commands. Typical commands include `just run` for a development build, `just check` for the main checks, and `just test-rust`, `just test-py`, or `just test-ts` for language-specific tests. Refer to the development guide for prerequisites and setup details.

#### Contributors

The following people have contributed to Anki: [CONTRIBUTORS](./CONTRIBUTORS)

### Anki Betas

If you'd like to try development builds of Anki but don't feel comfortable
building the code, please see [Anki betas](https://docs.ankiweb.net/releases/betas/intro).

## License

Anki's license: [LICENSE](./LICENSE)
