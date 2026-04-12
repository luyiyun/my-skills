# Repository Guide

## Purpose

This repository is the source of truth for personal Codex skills and the configuration used to install third-party skills into Codex's discovery directory.

## Layout

- `skills/`: first-party skills owned in this repository. Each skill lives in its own directory and must contain `SKILL.md`.
- `settings.json`: installation configuration for both local and third-party skills.
- `src/my_skills/cli.py`: top-level CLI entrypoint with subcommands for repository management tasks.
- `src/my_skills/sync_skills.py`: Python implementation of the sync workflow.
- `tests/`: automated tests for sync behavior.
- `pyproject.toml`: uv-managed Python project metadata.

## Workflow

1. Add or edit first-party skills under `skills/<skill-name>/`.
2. Register third-party skills in `settings.json`.
3. Use `uv run my-skills sync` to refresh both local and third-party skills.
4. Use `uv run my-skills install [name ...]` when you only want to install configured third-party skills, optionally filtering by skill name.
5. Use `uv run my-skills install --name <skill-name> --repo <git-url> [--subpath ...] [--ref ...]` to add a third-party git skill to `settings.json` and install it in one step.
6. Run `uv run python -m unittest discover -s tests -p 'test_*.py'` after changing sync logic.

## Settings Contract

`settings.json` currently supports:

- `install_path`: the Codex skills directory to populate, for example `~/.codex/skills`.
- `local_skills_dir`: repository-relative or absolute directory containing first-party skills.
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
- Local skills are meant to stay symlinked so source changes are immediately visible after syncing.
- Third-party skills are copied into the install directory and marked with `.managed-by-my-skills` so future syncs can safely replace them.
- Prefer extending the Python implementation and tests together; keep the CLI subcommand-oriented so future repository utilities fit naturally.
- If you change the `settings.json` schema, update the Python sync tool and this file in the same task.
