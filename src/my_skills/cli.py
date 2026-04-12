from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from my_skills.sync_skills import Settings, SyncError, ThirdPartySkill, load_settings, sync_skills


def select_third_party_skills(settings: Settings, names: Sequence[str]) -> Settings:
    requested = set(names)
    available = {skill.name: skill for skill in settings.third_party_skills}
    missing = sorted(requested - set(available))

    if missing:
        raise SyncError(f"Unknown third-party skill(s): {', '.join(missing)}")

    selected = tuple(skill for skill in settings.third_party_skills if skill.name in requested)
    return Settings(
        install_path=settings.install_path,
        local_skills_dir=settings.local_skills_dir,
        third_party_cache_dir=settings.third_party_cache_dir,
        third_party_skills=selected,
    )


def add_settings_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--settings", default="settings.json", help="Use a custom settings.json file.")


def add_force_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--force", action="store_true", help="Replace conflicting unmanaged destinations.")


def make_git_skill(args: argparse.Namespace) -> ThirdPartySkill:
    if not args.name:
        raise SyncError("--name is required when adding a new third-party skill")
    if not args.repo:
        raise SyncError("--repo is required when adding a new third-party skill")

    return ThirdPartySkill(
        name=args.name.strip(),
        skill_type="git",
        source=args.repo.strip(),
        subpath=(args.subpath or "").strip(),
        ref=(args.ref or "").strip(),
    )


def read_settings_payload(settings_path: Path) -> dict:
    with settings_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def upsert_third_party_skill(settings_path: Path, skill: ThirdPartySkill, *, force: bool) -> None:
    payload = read_settings_payload(settings_path)
    skills = payload.setdefault("third_party_skills", [])

    for index, existing in enumerate(skills):
        if existing.get("name") != skill.name:
            continue

        new_payload = serialize_skill(skill)
        if existing == new_payload:
            return
        if not force:
            raise SyncError(
                f"Third-party skill {skill.name} is already configured. "
                "Re-run with --force to replace its settings entry."
            )

        skills[index] = new_payload
        settings_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return

    skills.append(serialize_skill(skill))
    settings_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="my-skills",
        description="Utilities for managing this personal Codex skills repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Sync local skills and configured third-party skills.")
    add_settings_argument(sync_parser)
    add_force_argument(sync_parser)
    sync_mode = sync_parser.add_mutually_exclusive_group()
    sync_mode.add_argument("--local-only", action="store_true", help="Only sync local skills from local_skills_dir.")
    sync_mode.add_argument("--third-party-only", action="store_true", help="Only install third-party skills.")

    install_parser = subparsers.add_parser(
        "install",
        help="Install configured third-party skills, or add one from git and install it immediately.",
    )
    add_settings_argument(install_parser)
    add_force_argument(install_parser)
    install_parser.add_argument(
        "names",
        nargs="*",
        help="Optional configured third-party skill names to install. If omitted, install all configured third-party skills.",
    )
    install_parser.add_argument("--name", help="Add or update a third-party skill entry with this name before installing.")
    install_parser.add_argument("--repo", help="Git repository URL or path for a third-party skill to add and install.")
    install_parser.add_argument("--subpath", help="Optional subdirectory inside the repo containing the skill.")
    install_parser.add_argument("--ref", help="Optional git branch, tag, or commit for the third-party skill.")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings_path = Path(args.settings).resolve(strict=False)

    try:
        settings = load_settings(settings_path)

        if args.command == "sync":
            sync_skills(
                settings,
                sync_local=not args.third_party_only,
                sync_third_party=not args.local_only,
                force=args.force,
            )
        elif args.command == "install":
            adding_new_skill = any([args.name, args.repo, args.subpath, args.ref])

            if adding_new_skill and args.names:
                raise SyncError("Do not mix configured skill names with --name/--repo install arguments")

            if adding_new_skill:
                skill = make_git_skill(args)
                upsert_third_party_skill(settings_path, skill, force=args.force)
                settings = load_settings(settings_path)
                selected_settings = select_third_party_skills(settings, [skill.name])
            else:
                selected_settings = select_third_party_skills(settings, args.names) if args.names else settings

            sync_skills(
                selected_settings,
                sync_local=False,
                sync_third_party=True,
                force=args.force,
            )
        else:
            raise SyncError(f"Unsupported command: {args.command}")
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
