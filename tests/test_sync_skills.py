import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from my_skills.cli import main as cli_main
from my_skills.sync_skills import MANAGED_MARKER, SyncError, load_settings, sync_skills


class SyncSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.skills_dir = self.repo_root / "skills"
        self.install_dir = self.repo_root / "install"
        self.cache_dir = self.repo_root / "cache"
        self.settings_path = self.repo_root / "settings.json"
        self.skills_dir.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_local_skill(self, name: str) -> Path:
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
        return skill_dir

    def write_settings(self, third_party_skills=None) -> None:
        payload = {
            "install_path": str(self.install_dir),
            "local_skills_dir": str(self.skills_dir),
            "third_party_cache_dir": str(self.cache_dir),
            "third_party_skills": third_party_skills or [],
        }
        self.settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self):
        return load_settings(self.settings_path)

    def run_sync(self, **kwargs) -> str:
        output = io.StringIO()
        sync_skills(self.load(), stdout=output, **kwargs)
        return output.getvalue()

    def test_local_skills_are_symlinked(self) -> None:
        skill_dir = self.write_local_skill("learning-notes")
        self.write_settings()

        self.run_sync()

        destination = self.install_dir / "learning-notes"
        self.assertTrue(destination.is_symlink())
        self.assertEqual(destination.resolve(), skill_dir.resolve())

    def test_path_third_party_skill_is_copied_and_marked(self) -> None:
        self.write_settings(
            [
                {
                    "name": "third-party",
                    "type": "path",
                    "path": "vendor/third-party",
                }
            ]
        )
        vendor_dir = self.repo_root / "vendor" / "third-party"
        vendor_dir.mkdir(parents=True)
        (vendor_dir / "SKILL.md").write_text("# external\n", encoding="utf-8")

        self.run_sync(sync_local=False)

        destination = self.install_dir / "third-party"
        self.assertTrue((destination / "SKILL.md").is_file())
        marker = (destination / MANAGED_MARKER).read_text(encoding="utf-8")
        self.assertIn("name=third-party", marker)
        self.assertIn("type=path", marker)

    def test_unmanaged_destination_requires_force(self) -> None:
        self.write_settings(
            [
                {
                    "name": "third-party",
                    "type": "path",
                    "path": "vendor/third-party",
                }
            ]
        )
        vendor_dir = self.repo_root / "vendor" / "third-party"
        vendor_dir.mkdir(parents=True)
        (vendor_dir / "SKILL.md").write_text("# external\n", encoding="utf-8")
        destination = self.install_dir / "third-party"
        destination.mkdir(parents=True)
        (destination / "note.txt").write_text("keep me", encoding="utf-8")

        with self.assertRaises(SyncError):
            self.run_sync(sync_local=False)

        self.run_sync(sync_local=False, force=True)
        self.assertTrue((destination / "SKILL.md").is_file())
        self.assertFalse((destination / "note.txt").exists())

    def test_existing_install_path_source_is_skipped(self) -> None:
        existing = self.install_dir / "existing-skill"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("# existing\n", encoding="utf-8")
        self.write_settings(
            [
                {
                    "name": "existing-skill",
                    "type": "path",
                    "path": str(existing),
                }
            ]
        )

        output = self.run_sync(sync_local=False)

        self.assertIn("Skipped third-party skill already at install path", output)
        self.assertFalse((existing / MANAGED_MARKER).exists())

    def test_git_third_party_skill_from_local_repo_is_installed(self) -> None:
        source_repo = self.repo_root / "remote-skill"
        source_repo.mkdir()
        (source_repo / "SKILL.md").write_text("# remote\n", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=source_repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", "SKILL.md"], cwd=source_repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "initial",
            ],
            cwd=source_repo,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.write_settings(
            [
                {
                    "name": "git-skill",
                    "type": "git",
                    "repo": str(source_repo),
                }
            ]
        )

        self.run_sync(sync_local=False)

        destination = self.install_dir / "git-skill"
        self.assertTrue((destination / "SKILL.md").is_file())
        self.assertTrue((destination / MANAGED_MARKER).is_file())

    def test_cli_install_installs_selected_skill(self) -> None:
        first = self.repo_root / "vendor" / "first-skill"
        second = self.repo_root / "vendor" / "second-skill"
        first.mkdir(parents=True)
        second.mkdir(parents=True)
        (first / "SKILL.md").write_text("# first\n", encoding="utf-8")
        (second / "SKILL.md").write_text("# second\n", encoding="utf-8")
        self.write_settings(
            [
                {"name": "first", "type": "path", "path": str(first)},
                {"name": "second", "type": "path", "path": str(second)},
            ]
        )

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = cli_main(
                [
                    "install",
                    "--settings",
                    str(self.settings_path),
                    "second",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Installed third-party skill: second", stdout.getvalue())
        self.assertFalse((self.install_dir / "first").exists())
        self.assertTrue((self.install_dir / "second" / "SKILL.md").is_file())

    def test_cli_install_rejects_unknown_name(self) -> None:
        self.write_settings([])

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "install",
                    "--settings",
                    str(self.settings_path),
                    "missing-skill",
                ]
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("Unknown third-party skill(s): missing-skill", stderr.getvalue())

    def test_cli_install_adds_git_skill_to_settings_and_installs_it(self) -> None:
        source_repo = self.repo_root / "vendor-repo"
        skill_dir = source_repo / "skills" / "obsidian-cli"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# obsidian-cli\n", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=source_repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], cwd=source_repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test User",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-m",
                "initial",
            ],
            cwd=source_repo,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self.write_settings([])

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = cli_main(
                [
                    "install",
                    "--settings",
                    str(self.settings_path),
                    "--name",
                    "obsidian-cli",
                    "--repo",
                    str(source_repo),
                    "--subpath",
                    "skills/obsidian-cli",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("Installed third-party skill: obsidian-cli", stdout.getvalue())
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["third_party_skills"],
            [
                {
                    "name": "obsidian-cli",
                    "type": "git",
                    "repo": str(source_repo),
                    "subpath": "skills/obsidian-cli",
                }
            ],
        )
        self.assertTrue((self.install_dir / "obsidian-cli" / "SKILL.md").is_file())

    def test_cli_install_rejects_conflicting_existing_settings_without_force(self) -> None:
        self.write_settings(
            [
                {
                    "name": "obsidian-cli",
                    "type": "git",
                    "repo": "https://example.com/old.git",
                }
            ]
        )

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "install",
                    "--settings",
                    str(self.settings_path),
                    "--name",
                    "obsidian-cli",
                    "--repo",
                    "https://example.com/new.git",
                ]
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("already configured", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
