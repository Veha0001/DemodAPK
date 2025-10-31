# DemodAPK Codebase Guidelines for AI Agents

This document outlines essential information for AI agents working within the DemodAPK repository, covering project structure, key commands, and coding conventions.

## 1. Project Overview

DemodAPK is a Python CLI tool designed for modifying APK resources based on a configuration. It uses `flit_core` for package management and `mkdocs` for documentation.

## 2. Essential Commands

### Build
The project uses `flit` for building. The typical command to build the package is:
```bash
flit build
```

### Install
To install the package in editable mode for development:
```bash
flit install --symlink
```

### Run
The main CLI entry point is `demodapk.cli:main`. After installation, the tool can be run using:
```bash
demodapk [arguments]
```

### Lint
`pylint` is used for code linting. To run pylint on the main source directory:
```bash
pylint demodapk/
```

### Documentation
The project documentation is built with MkDocs.
- To build the documentation:
```bash
mkdocs build
```
- To serve the documentation locally (for development):
```bash
mkdocs serve
```

## 3. Code Organization and Structure

- **`demodapk/`**: Contains the core Python source code for the CLI tool.
  - `demodapk/cli.py`: Defines the command-line interface.
  - `demodapk/baseconf.py`: Likely contains base configuration handling.
  - `demodapk/mark.py`, `demodapk/mods.py`, `demodapk/patch.py`, `demodapk/tool.py`, `demodapk/utils.py`: Contain various modules related to the APK modification logic.
  - `demodapk/schema.py`, `demodapk/schema.json`: Define and handle data schemas.
- **`docs/`**: Contains the MkDocs documentation source files.
- **`.github/workflows/`**: Contains GitHub Actions workflows for CI/CD, specifically for publishing to PyPI.

## 4. Naming Conventions and Style Patterns

- **Python**: Follows standard Python naming conventions (snake_case for variables and functions, CapWords for classes).
- **Configuration**: Schema definitions are found in `demodapk/schema.py` and `demodapk/schema.json`.

## 5. Testing Approach

No explicit testing framework or test files were found (e.g., `pytest` or `unittest` files with `test_` prefix). Future agents should assume manual testing or a yet-to-be-defined testing strategy.

## 6. Important Gotchas and Non-obvious Patterns

- **Flit for Packaging**: The project uses Flit for packaging and distribution to PyPI. Agents should be familiar with Flit's conventions for dependencies and project metadata.
- **Rich for CLI**: The `rich` and `rich-click` libraries are used for creating a rich and user-friendly command-line interface, implying custom styling and output.
- **Dynamic Versioning**: `pyproject.toml` indicates `dynamic = ["version"]`, meaning the version is not statically defined in `pyproject.toml` but likely managed elsewhere (e.g., `demodapk/__init__.py`).
