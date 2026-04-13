from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional, Sequence, TextIO

from my_skills.sync_skills import (
    Settings,
    SyncError,
    ThirdPartySkill,
    available_skill_names,
    clone_git_source,
    discover_skill_dirs,
    import_installed_skills,
    iter_installed_skill_dirs,
    iter_skill_dirs,
    load_settings,
    sync_skills,
)


PromptFn = Callable[[str], str]


def prompt_choice(prompt: str, valid_choices: dict[str, str], *, input_fn: PromptFn) -> str:
    choice_hint = "/".join(valid_choices)
    while True:
        response = input_fn(f"{prompt} [{choice_hint}]: ").strip().lower()
        if response in valid_choices:
            return response
        print(f"Please choose one of: {', '.join(valid_choices)}", file=sys.stderr)


def confirm(prompt: str, *, input_fn: PromptFn) -> bool:
    return prompt_choice(prompt, {"y": "yes", "n": "no"}, input_fn=input_fn) == "y"


def read_settings_payload(settings_path: Path) -> dict:
    with settings_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_settings_payload(settings_path: Path, payload: dict) -> None:
    settings_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def serialize_skill(skill: ThirdPartySkill) -> dict:
    payload = {
        "name": skill.name,
        "type": skill.skill_type,
    }
    if skill.skill_type == "git":
        payload["repo"] = skill.source
    else:
        payload["path"] = skill.source
    if skill.subpath:
        payload["subpath"] = skill.subpath
    if skill.ref:
        payload["ref"] = skill.ref
    return payload


def local_name_sources(settings: Settings) -> dict[str, str]:
    sources: dict[str, str] = {}
    if settings.first_party_skills_dir.is_dir():
        for skill_dir in iter_skill_dirs(settings.first_party_skills_dir):
            sources[skill_dir.name] = "first-party"
    if settings.imported_skills_dir.is_dir():
        for skill_dir in iter_skill_dirs(settings.imported_skills_dir):
            sources[skill_dir.name] = "imported"
    return sources


def select_third_party_skills(settings: Settings, names: Sequence[str]) -> Settings:
    requested = set(names)
    available = {skill.name: skill for skill in settings.third_party_skills}
    missing = sorted(requested - set(available))

    if missing:
        raise SyncError(f"Unknown third-party skill(s): {', '.join(missing)}")

    selected = tuple(skill for skill in settings.third_party_skills if skill.name in requested)
    return Settings(
        install_path=settings.install_path,
        first_party_skills_dir=settings.first_party_skills_dir,
        imported_skills_dir=settings.imported_skills_dir,
        third_party_cache_dir=settings.third_party_cache_dir,
        add_confirmation_threshold=settings.add_confirmation_threshold,
        third_party_skills=selected,
    )


def make_single_git_skill(repo: str, subpath: str, name: Optional[str], ref: str) -> ThirdPartySkill:
    skill_name = (name or Path(subpath.rstrip("/")).name).strip()
    if not skill_name:
        raise SyncError("Could not determine a skill name. Pass --name when the subpath does not end with a directory name.")
    return ThirdPartySkill(
        name=skill_name,
        skill_type="git",
        source=repo.strip(),
        subpath=subpath.strip(),
        ref=ref.strip(),
    )


def discover_git_repo_skills(settings: Settings, repo: str, ref: str, explicit_name: Optional[str]) -> list[ThirdPartySkill]:
    settings.third_party_cache_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="my-skills-add-", dir=settings.third_party_cache_dir) as temp_dir:
        checkout_dir = Path(temp_dir) / "repo"
        clone_git_source(repo, checkout_dir, ref)
        discovered_dirs = discover_skill_dirs(checkout_dir)

    if not discovered_dirs:
        raise SyncError("No SKILL.md files were found in the repository.")

    skills: list[ThirdPartySkill] = []
    names_seen: set[str] = set()
    for skill_dir in discovered_dirs:
        relative_dir = skill_dir.relative_to(checkout_dir)
        skill_name = skill_dir.name
        if skill_name in names_seen:
            raise SyncError(f"Discovered duplicate skill name in repository: {skill_name}")
        names_seen.add(skill_name)
        subpath = "" if str(relative_dir) == "." else str(relative_dir)
        skills.append(
            ThirdPartySkill(
                name=skill_name,
                skill_type="git",
                source=repo.strip(),
                subpath=subpath,
                ref=ref.strip(),
            )
        )
    if explicit_name:
        filtered = [skill for skill in skills if skill.name == explicit_name.strip()]
        if not filtered:
            raise SyncError(f'Could not find a skill named "{explicit_name}" in the repository')
        return filtered
    return skills


def collect_add_skills(settings: Settings, args: argparse.Namespace) -> list[ThirdPartySkill]:
    repo = args.repo.strip()
    ref = (args.ref or "").strip()
    if args.subpath:
        return [make_single_git_skill(repo, args.subpath, args.name, ref)]
    return discover_git_repo_skills(settings, repo, ref, args.name)


def apply_additions(
    settings_path: Path,
    settings: Settings,
    skills: Sequence[ThirdPartySkill],
    *,
    input_fn: PromptFn,
    stdout: TextIO,
) -> list[str]:
    if len(skills) > settings.add_confirmation_threshold:
        confirmed = confirm(
            f"About to add {len(skills)} skills, which exceeds the configured threshold of {settings.add_confirmation_threshold}. Continue?",
            input_fn=input_fn,
        )
        if not confirmed:
            raise SyncError("Add cancelled by user")

    payload = read_settings_payload(settings_path)
    third_party_payloads = payload.setdefault("third_party_skills", [])
    third_party_index = {item.get("name"): index for index, item in enumerate(third_party_payloads)}
    local_sources = local_name_sources(settings)

    added_names: list[str] = []
    for skill in skills:
        if skill.name in local_sources:
            choice = prompt_choice(
                f'Warning: skill "{skill.name}" already exists as a {local_sources[skill.name]} skill. Skip or abort?',
                {"s": "skip", "a": "abort"},
                input_fn=input_fn,
            )
            if choice == "s":
                print(f"Skipped adding conflicting skill: {skill.name}", file=stdout)
                continue
            raise SyncError("Add cancelled by user")

        serialized = serialize_skill(skill)
        if skill.name in third_party_index:
            existing = third_party_payloads[third_party_index[skill.name]]
            choice = prompt_choice(
                f'Warning: third-party skill "{skill.name}" is already configured. Replace, skip, or abort?',
                {"r": "replace", "s": "skip", "a": "abort"},
                input_fn=input_fn,
            )
            if choice == "s":
                print(f"Skipped existing third-party skill: {skill.name}", file=stdout)
                continue
            if choice == "a":
                raise SyncError("Add cancelled by user")
            third_party_payloads[third_party_index[skill.name]] = serialized
            print(f"Updated third-party skill: {skill.name}", file=stdout)
            added_names.append(skill.name)
            continue

        third_party_payloads.append(serialized)
        third_party_index[skill.name] = len(third_party_payloads) - 1
        print(f"Added third-party skill: {skill.name}", file=stdout)
        added_names.append(skill.name)

    write_settings_payload(settings_path, payload)
    return added_names


def collect_list_sections(settings: Settings) -> list[tuple[str, list[str]]]:
    first_party = [skill_dir.name for skill_dir in iter_skill_dirs(settings.first_party_skills_dir)] if settings.first_party_skills_dir.is_dir() else []
    imported = [skill_dir.name for skill_dir in iter_skill_dirs(settings.imported_skills_dir)] if settings.imported_skills_dir.is_dir() else []
    configured_third_party = [skill.name for skill in settings.third_party_skills]
    monitored = available_skill_names(settings)
    unmanaged_installed = [
        skill_dir.name
        for skill_dir in iter_installed_skill_dirs(settings.install_path)
        if skill_dir.name not in monitored
    ]

    return [
        ("First-Party", first_party),
        ("Imported", imported),
        ("Configured Third-Party", configured_third_party),
        ("Unmanaged Installed", unmanaged_installed),
    ]


def print_list_sections(settings: Settings, *, stdout: TextIO) -> None:
    sections = collect_list_sections(settings)
    for title, items in sections:
        print(f"{title}:", file=stdout)
        if items:
            for item in items:
                print(f"- {item}", file=stdout)
        else:
            print("- none", file=stdout)


def resolve_import_names(
    settings: Settings,
    names: Sequence[str],
    *,
    input_fn: PromptFn,
    stdout: TextIO,
) -> list[str]:
    if not names:
        return []

    installed_names = {skill_dir.name for skill_dir in iter_installed_skill_dirs(settings.install_path)}
    requested = list(dict.fromkeys(names))
    missing = sorted(name for name in requested if name not in installed_names)
    if missing:
        raise SyncError(f"Installed skill(s) not found in install_path: {', '.join(missing)}")

    monitored = available_skill_names(settings)
    selected: list[str] = []
    for name in requested:
        if name not in monitored:
            selected.append(name)
            continue

        choice = prompt_choice(
            f'Warning: skill "{name}" is already monitored. Skip or abort import?',
            {"s": "skip", "a": "abort"},
            input_fn=input_fn,
        )
        if choice == "s":
            print(f"Skipped monitored skill during import: {name}", file=stdout)
            continue
        raise SyncError("Import cancelled by user")

    return selected


def add_settings_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--settings", default="settings.json", help="Use a custom settings.json file.")


def add_force_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--force", action="store_true", help="Replace conflicting unmanaged destinations.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="my-skills",
        description="Utilities for managing this personal Codex skills repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser(
        "add",
        help="Add third-party git skills to settings.json. Without subpath, all discovered skills in the repo are added.",
    )
    add_settings_argument(add_parser)
    add_parser.add_argument("repo", help="Git repository URL or path.")
    add_parser.add_argument("subpath", nargs="?", help="Optional subdirectory inside the repo containing one skill.")
    add_parser.add_argument("--name", help="Optional skill name. Only valid for a single added skill.")
    add_parser.add_argument("--ref", help="Optional git branch, tag, or commit.")

    sync_parser = subparsers.add_parser("sync", help="Sync selected skills from the repository and third-party settings.")
    add_settings_argument(sync_parser)
    add_force_argument(sync_parser)
    sync_mode = sync_parser.add_mutually_exclusive_group()
    sync_mode.add_argument(
        "--local-only",
        action="store_true",
        help="Only sync first-party and imported local skills from the repository.",
    )
    sync_mode.add_argument("--third-party-only", action="store_true", help="Only install third-party skills.")
    sync_parser.add_argument(
        "names",
        nargs="*",
        help="Optional skill names to sync. Names may refer to first-party, imported, or configured third-party skills.",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Copy unmanaged installed skills into the repository and start managing them as imported skills.",
    )
    add_settings_argument(import_parser)
    add_force_argument(import_parser)
    import_parser.add_argument(
        "names",
        nargs="*",
        help="Optional installed skill names to import. If omitted, import all unmanaged installed skills.",
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List first-party, imported, configured third-party, and unmanaged installed skills.",
    )
    add_settings_argument(list_parser)

    return parser


def main(argv: Optional[Sequence[str]] = None, *, input_fn: PromptFn = input, stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings_path = Path(args.settings).resolve(strict=False)

    try:
        settings = load_settings(settings_path)

        if args.command == "add":
            skills = collect_add_skills(settings, args)
            added_names = apply_additions(settings_path, settings, skills, input_fn=input_fn, stdout=stdout)
            if added_names:
                print(f"Updated settings for {len(added_names)} skill(s).", file=stdout)
                updated_settings = load_settings(settings_path)
                sync_skills(
                    select_third_party_skills(updated_settings, added_names),
                    sync_local=False,
                    sync_third_party=True,
                    force=False,
                    stdout=stdout,
                )
            else:
                print("No settings changes were made.", file=stdout)
        elif args.command == "sync":
            sync_skills(
                settings,
                sync_local=not args.third_party_only,
                sync_third_party=not args.local_only,
                force=args.force,
                selected_names=set(args.names) if args.names else None,
                stdout=stdout,
            )
        elif args.command == "import":
            selected_names = resolve_import_names(settings, args.names, input_fn=input_fn, stdout=stdout)
            import_installed_skills(
                settings,
                selected_names,
                force=args.force,
                stdout=stdout,
            )
        elif args.command == "list":
            print_list_sections(settings, stdout=stdout)
        else:
            raise SyncError(f"Unsupported command: {args.command}")
    except SyncError as exc:
        print(f"Error: {exc}", file=stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
