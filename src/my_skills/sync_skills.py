from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence, TextIO

MANAGED_MARKER = ".managed-by-my-skills"


class SyncError(Exception):
    """Raised when skill sync configuration or execution is invalid."""


@dataclass(frozen=True)
class ThirdPartySkill:
    name: str
    skill_type: str
    source: str
    subpath: str = ""
    ref: str = ""


@dataclass(frozen=True)
class Settings:
    install_path: Path
    local_skills_dir: Path
    third_party_cache_dir: Path
    third_party_skills: tuple[ThirdPartySkill, ...]


def expand_path(value: Optional[str], repo_root: Path, default: Optional[str] = None) -> Path:
    resolved = value if value not in (None, "") else default
    if resolved in (None, ""):
        raise SyncError("Expected a path value but found nothing.")

    expanded = os.path.expandvars(os.path.expanduser(resolved))
    path = Path(expanded)
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve(strict=False)


def resolve_git_source(source: str, repo_root: Path) -> str:
    if "://" in source or source.startswith("git@"):
        return source
    return str(expand_path(source, repo_root))


def load_settings(settings_path: Path) -> Settings:
    repo_root = settings_path.resolve().parent

    with settings_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    try:
        install_path = expand_path(raw.get("install_path"), repo_root)
    except SyncError as exc:
        raise SyncError("settings.json must define install_path") from exc

    local_skills_dir = expand_path(raw.get("local_skills_dir", "skills"), repo_root, default="skills")
    third_party_cache_dir = expand_path(
        raw.get("third_party_cache_dir"),
        repo_root,
        default=str(Path(tempfile.gettempdir()) / "my-skills-third-party-cache"),
    )

    third_party_items = []
    for item in raw.get("third_party_skills", []):
        name = (item.get("name") or "").strip()
        skill_type = (item.get("type") or "git").strip()
        subpath = (item.get("subpath") or "").strip()
        ref = (item.get("ref") or "").strip()

        if not name:
            raise SyncError("Each third_party_skills item must define name")

        if skill_type == "git":
            source = (item.get("repo") or item.get("source") or "").strip()
            if not source:
                raise SyncError(f"Third-party skill {name} is missing its source")
            source = resolve_git_source(source, repo_root)
        elif skill_type == "path":
            source = (item.get("path") or item.get("source") or "").strip()
            if not source:
                raise SyncError(f"Third-party skill {name} is missing its source")
            source = str(expand_path(source, repo_root))
        else:
            raise SyncError(f"Unsupported third-party skill type: {skill_type}")

        third_party_items.append(
            ThirdPartySkill(
                name=name,
                skill_type=skill_type,
                source=source,
                subpath=subpath,
                ref=ref,
            )
        )

    return Settings(
        install_path=install_path,
        local_skills_dir=local_skills_dir,
        third_party_cache_dir=third_party_cache_dir,
        third_party_skills=tuple(third_party_items),
    )


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.exists():
        shutil.rmtree(path)


def replace_destination(destination: Path, force: bool) -> None:
    if destination.is_symlink():
        destination.unlink()
        return

    if not destination.exists():
        return

    if force:
        remove_path(destination)
        return

    if destination.is_dir() and (destination / MANAGED_MARKER).exists():
        shutil.rmtree(destination)
        return

    raise SyncError(
        f"Destination already exists and is not managed by this repo: {destination}. "
        "Re-run with --force if you want to replace it."
    )


def write_marker(destination: Path, skill: ThirdPartySkill) -> None:
    marker_text = (
        f"name={skill.name}\n"
        f"type={skill.skill_type}\n"
        f"source={skill.source}\n"
        f"subpath={skill.subpath}\n"
        f"ref={skill.ref}\n"
    )
    (destination / MANAGED_MARKER).write_text(marker_text, encoding="utf-8")


def run_command(args: Sequence[str], *, cwd: Optional[Path] = None) -> None:
    try:
        subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError as exc:
        raise SyncError(f"Required command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise SyncError(f"Command failed: {' '.join(args)}") from exc


def prepare_git_checkout(skill: ThirdPartySkill, cache_dir: Path) -> Path:
    checkout_dir = cache_dir / skill.name

    if (checkout_dir / ".git").is_dir():
        run_command(["git", "-C", str(checkout_dir), "fetch", "--tags", "--prune", "origin"])
    else:
        if checkout_dir.exists():
            shutil.rmtree(checkout_dir)
        run_command(["git", "clone", skill.source, str(checkout_dir)])

    if skill.ref:
        run_command(["git", "-C", str(checkout_dir), "checkout", "--force", skill.ref])
    else:
        run_command(["git", "-C", str(checkout_dir), "pull", "--ff-only"])

    return checkout_dir


def source_dir_for_skill(skill: ThirdPartySkill, cache_dir: Path) -> Path:
    if skill.skill_type == "git":
        source_root = prepare_git_checkout(skill, cache_dir)
    elif skill.skill_type == "path":
        source_root = Path(skill.source)
    else:
        raise SyncError(f"Unsupported third-party skill type: {skill.skill_type}")

    return (source_root / skill.subpath).resolve(strict=False) if skill.subpath else source_root.resolve(strict=False)


def iter_local_skill_dirs(local_skills_dir: Path) -> Iterable[Path]:
    if not local_skills_dir.is_dir():
        raise SyncError(f"Local skills directory not found: {local_skills_dir}")

    for child in sorted(local_skills_dir.iterdir()):
        if child.is_dir() and (child / "SKILL.md").is_file():
            yield child


def sync_local_skill(source_dir: Path, install_path: Path, force: bool, stdout: TextIO) -> str:
    skill_name = source_dir.name
    destination = install_path / skill_name
    replace_destination(destination, force)
    os.symlink(source_dir, destination)
    print(f"Linked local skill: {skill_name}", file=stdout)
    return skill_name


def install_third_party_skill(
    skill: ThirdPartySkill,
    install_path: Path,
    cache_dir: Path,
    force: bool,
    stdout: TextIO,
) -> str:
    source_dir = source_dir_for_skill(skill, cache_dir)
    destination = install_path / skill.name

    if not source_dir.is_dir():
        raise SyncError(f"Third-party skill source directory not found: {source_dir}")
    if not (source_dir / "SKILL.md").is_file():
        raise SyncError(f"Third-party skill is missing SKILL.md: {source_dir}")

    if source_dir.resolve(strict=False) == destination.resolve(strict=False):
        print(f"Skipped third-party skill already at install path: {skill.name}", file=stdout)
        return skill.name

    replace_destination(destination, force)
    shutil.copytree(source_dir, destination, symlinks=True)
    write_marker(destination, skill)
    print(f"Installed third-party skill: {skill.name}", file=stdout)
    return skill.name


def sync_skills(
    settings: Settings,
    *,
    sync_local: bool = True,
    sync_third_party: bool = True,
    force: bool = False,
    stdout: Optional[TextIO] = None,
) -> None:
    output = stdout or sys.stdout
    settings.install_path.mkdir(parents=True, exist_ok=True)
    settings.third_party_cache_dir.mkdir(parents=True, exist_ok=True)

    registered_names: set[str] = set()

    def register(name: str) -> None:
        if name in registered_names:
            raise SyncError(f"Duplicate skill name detected: {name}")
        registered_names.add(name)

    if sync_local:
        for skill_dir in iter_local_skill_dirs(settings.local_skills_dir):
            register(skill_dir.name)
            sync_local_skill(skill_dir, settings.install_path, force, output)

    if sync_third_party:
        for skill in settings.third_party_skills:
            register(skill.name)
            install_third_party_skill(
                skill,
                settings.install_path,
                settings.third_party_cache_dir,
                force,
                output,
            )

    print("Sync complete.", file=output)
