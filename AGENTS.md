# Repository Guide

## Purpose

This repository is the source of truth for personal Codex skills and the configuration used to install third-party skills into Codex's discovery directory.

## Layout

- `skills/first-party/`: skills created and maintained directly in this repository.
- `skills/imported/`: third-party skills copied into this repository from an install directory so they can be tracked by git.
- `settings.json`: installation configuration for both local and third-party skills.
- `src/my_skills/cli.py`: top-level CLI entrypoint with subcommands for repository management tasks.
- `src/my_skills/sync_skills.py`: Python implementation of the sync workflow.
- `tests/`: automated tests for sync behavior.
- `pyproject.toml`: uv-managed Python project metadata.

## Workflow

1. Add or edit first-party skills under `skills/first-party/<skill-name>/`.
2. Use `uv run my-skills add <git-url> [subpath] [--name <skill-name>] [--ref <git-ref>]` to register third-party git skills in `settings.json` and install them immediately.
3. Use `uv run my-skills sync [name ...]` to install selected first-party, imported, or configured third-party skills. Without names it syncs everything.
4. Use `uv run my-skills import [name ...]` to copy unmanaged installed skills from `install_path` into `skills/imported/` and switch them to repo-managed symlinks.
5. Use `uv run my-skills list` to inspect first-party, imported, configured third-party, and unmanaged installed skills.
6. Run `uv run python -m unittest discover -s tests -p 'test_*.py'` after changing sync logic.

## Settings Contract

`settings.json` currently supports:

- `install_path`: the Codex skills directory to populate, for example `~/.codex/skills`.
- `first_party_skills_dir`: repository-relative or absolute directory containing skills authored in this repository.
- `imported_skills_dir`: repository-relative or absolute directory containing imported third-party skill copies that are now tracked by git.
- `add_confirmation_threshold`: maximum number of skills `my-skills add` may register at once before it asks for confirmation.
- `third_party_cache_dir`: optional cache directory for cloned third-party repositories.
- `third_party_skills`: list of external skills.

Each `third_party_skills` item supports:

- `name`: destination directory name under `install_path`.
- `type`: `git` or `path`.
- `repo` or `source`: git URL when `type` is `git`.
- `path` or `source`: local path when `type` is `path`.
- `subpath`: optional subdirectory containing the actual skill.
- `ref`: optional git branch, tag, or commit to check out.

## Agent Notes

- Do not edit the installed skills directory directly. Edit the source here, then rerun the sync script.
- First-party and imported skills are both treated as local sources and stay symlinked into the install directory after syncing.
- Third-party skills are registered through `my-skills add` and installed immediately; later `my-skills sync` runs keep them up to date. Installed copies are marked with `.managed-by-my-skills` so future syncs can safely replace them.
- Imported skills should live under `skills/imported/`; once imported, they are managed from this repo rather than from the original install directory copy.
- Prefer extending the Python implementation and tests together; keep the CLI subcommand-oriented so future repository utilities fit naturally.
- If you change the `settings.json` schema, update the Python sync tool and this file in the same task.
