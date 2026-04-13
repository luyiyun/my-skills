import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from my_skills.cli import main as cli_main
from my_skills.sync_skills import MANAGED_MARKER, SyncError, import_installed_skills, load_settings, sync_skills


class SyncSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.first_party_dir = self.repo_root / "skills" / "first-party"
        self.imported_dir = self.repo_root / "skills" / "imported"
        self.install_dir = self.repo_root / "install"
        self.cache_dir = self.repo_root / "cache"
        self.settings_path = self.repo_root / "settings.json"
        self.first_party_dir.mkdir(parents=True)
        self.imported_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_skill_dir(self, root: Path, name: str, content: str = "# skill\n") -> Path:
        skill_dir = root / name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")
        return skill_dir

    def write_local_skill(self, name: str) -> Path:
        return self.write_skill_dir(self.first_party_dir, name, f"# {name}\n")

    def write_imported_skill(self, name: str) -> Path:
        return self.write_skill_dir(self.imported_dir, name, f"# {name}\n")

    def write_settings(self, third_party_skills=None, *, add_confirmation_threshold: int = 5) -> None:
        payload = {
            "install_path": str(self.install_dir),
            "first_party_skills_dir": str(self.first_party_dir),
            "imported_skills_dir": str(self.imported_dir),
            "third_party_cache_dir": str(self.cache_dir),
            "add_confirmation_threshold": add_confirmation_threshold,
            "third_party_skills": third_party_skills or [],
        }
        self.settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self):
        return load_settings(self.settings_path)

    def run_sync(self, **kwargs) -> str:
        output = io.StringIO()
        sync_skills(self.load(), stdout=output, **kwargs)
        return output.getvalue()

    def init_git_repo(self, repo_root: Path) -> None:
        subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], cwd=repo_root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            cwd=repo_root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_local_skills_are_symlinked(self) -> None:
        skill_dir = self.write_local_skill("learning-notes")
        self.write_settings()

        self.run_sync()

        destination = self.install_dir / "learning-notes"
        self.assertTrue(destination.is_symlink())
        self.assertEqual(destination.resolve(), skill_dir.resolve())

    def test_imported_skills_are_symlinked_as_local_skills(self) -> None:
        imported_skill = self.write_imported_skill("obsidian-cli")
        self.write_settings()

        self.run_sync()

        destination = self.install_dir / "obsidian-cli"
        self.assertTrue(destination.is_symlink())
        self.assertEqual(destination.resolve(), imported_skill.resolve())

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

    def test_sync_selected_names_can_include_local_and_third_party(self) -> None:
        local_skill = self.write_local_skill("learning-notes")
        vendor_dir = self.repo_root / "vendor" / "third-party"
        vendor_dir.mkdir(parents=True)
        (vendor_dir / "SKILL.md").write_text("# external\n", encoding="utf-8")
        self.write_settings(
            [
                {
                    "name": "third-party",
                    "type": "path",
                    "path": str(vendor_dir),
                }
            ]
        )

        output = self.run_sync(selected_names={"learning-notes", "third-party"})

        self.assertIn("Linked local skill: learning-notes", output)
        self.assertIn("Installed third-party skill: third-party", output)
        self.assertTrue((self.install_dir / "learning-notes").is_symlink())
        self.assertEqual((self.install_dir / "learning-notes").resolve(), local_skill.resolve())
        self.assertTrue((self.install_dir / "third-party" / "SKILL.md").is_file())

    def test_sync_rejects_unknown_selected_name(self) -> None:
        self.write_settings([])
        with self.assertRaises(SyncError):
            self.run_sync(selected_names={"missing-skill"})

    def test_cli_add_with_subpath_adds_one_skill_to_settings(self) -> None:
        source_repo = self.repo_root / "vendor-repo"
        skill_dir = source_repo / "skills" / "obsidian-cli"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# obsidian-cli\n", encoding="utf-8")
        self.init_git_repo(source_repo)
        self.write_settings([])

        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = cli_main(
            [
                "add",
                "--settings",
                str(self.settings_path),
                str(source_repo),
                "skills/obsidian-cli",
            ],
            input_fn=lambda _: "y",
            stdout=stdout,
            stderr=stderr,
        )

        self.assertEqual(exit_code, 0)
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

    def test_cli_add_without_subpath_discovers_all_repo_skills(self) -> None:
        source_repo = self.repo_root / "vendor-repo"
        self.write_skill_dir(source_repo / "skills", "first", "# first\n")
        self.write_skill_dir(source_repo / "skills", "second", "# second\n")
        self.init_git_repo(source_repo)
        self.write_settings([], add_confirmation_threshold=1)

        prompts: list[str] = []

        def input_fn(prompt: str) -> str:
            prompts.append(prompt)
            return "y"

        stdout = io.StringIO()
        exit_code = cli_main(
            [
                "add",
                "--settings",
                str(self.settings_path),
                str(source_repo),
            ],
            input_fn=input_fn,
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(exit_code, 0)
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["third_party_skills"]), 2)
        self.assertEqual({item["name"] for item in payload["third_party_skills"]}, {"first", "second"})
        self.assertTrue(any("exceeds the configured threshold" in prompt for prompt in prompts))
        self.assertTrue((self.install_dir / "first" / "SKILL.md").is_file())
        self.assertTrue((self.install_dir / "second" / "SKILL.md").is_file())

    def test_cli_add_without_subpath_and_with_name_selects_matching_skill(self) -> None:
        source_repo = self.repo_root / "vendor-repo"
        self.write_skill_dir(source_repo / "skills", "first", "# first\n")
        self.write_skill_dir(source_repo / "skills", "second", "# second\n")
        self.init_git_repo(source_repo)
        self.write_settings([])

        stdout = io.StringIO()
        exit_code = cli_main(
            [
                "add",
                "--settings",
                str(self.settings_path),
                "--name",
                "second",
                str(source_repo),
            ],
            input_fn=lambda _: "y",
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(exit_code, 0)
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["third_party_skills"],
            [
                {
                    "name": "second",
                    "type": "git",
                    "repo": str(source_repo),
                    "subpath": "skills/second",
                }
            ],
        )
        self.assertFalse((self.install_dir / "first").exists())
        self.assertTrue((self.install_dir / "second" / "SKILL.md").is_file())

    def test_cli_add_can_cancel_bulk_add_confirmation(self) -> None:
        source_repo = self.repo_root / "vendor-repo"
        self.write_skill_dir(source_repo / "skills", "first", "# first\n")
        self.write_skill_dir(source_repo / "skills", "second", "# second\n")
        self.init_git_repo(source_repo)
        self.write_settings([], add_confirmation_threshold=1)

        stderr = io.StringIO()
        exit_code = cli_main(
            [
                "add",
                "--settings",
                str(self.settings_path),
                str(source_repo),
            ],
            input_fn=lambda _: "n",
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertEqual(exit_code, 1)
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["third_party_skills"], [])

    def test_cli_add_name_conflict_with_existing_third_party_can_replace(self) -> None:
        self.write_settings(
            [
                {
                    "name": "obsidian-cli",
                    "type": "git",
                    "repo": "https://example.com/old.git",
                }
            ]
        )
        source_repo = self.repo_root / "vendor-repo"
        skill_dir = source_repo / "skills" / "obsidian-cli"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# obsidian-cli\n", encoding="utf-8")
        self.init_git_repo(source_repo)

        stdout = io.StringIO()
        exit_code = cli_main(
            [
                "add",
                "--settings",
                str(self.settings_path),
                str(source_repo),
                "skills/obsidian-cli",
            ],
            input_fn=lambda _: "r",
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(exit_code, 0)
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["third_party_skills"][0]["repo"], str(source_repo))

    def test_cli_add_name_conflict_with_first_party_can_skip(self) -> None:
        self.write_local_skill("obsidian-cli")
        self.write_settings([])
        source_repo = self.repo_root / "vendor-repo"
        skill_dir = source_repo / "skills" / "obsidian-cli"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# obsidian-cli\n", encoding="utf-8")
        self.init_git_repo(source_repo)

        stdout = io.StringIO()
        exit_code = cli_main(
            [
                "add",
                "--settings",
                str(self.settings_path),
                str(source_repo),
                "skills/obsidian-cli",
            ],
            input_fn=lambda _: "s",
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(exit_code, 0)
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["third_party_skills"], [])
        self.assertIn("Skipped adding conflicting skill: obsidian-cli", stdout.getvalue())

    def test_import_installed_skill_copies_into_repo_and_relinks_install_path(self) -> None:
        unmanaged = self.install_dir / "manual-skill"
        unmanaged.mkdir(parents=True)
        (unmanaged / "SKILL.md").write_text("# manual\n", encoding="utf-8")
        (unmanaged / "notes.txt").write_text("copied", encoding="utf-8")
        self.write_settings([])

        output = io.StringIO()
        import_installed_skills(self.load(), ["manual-skill"], stdout=output)

        imported_copy = self.imported_dir / "manual-skill"
        self.assertTrue((imported_copy / "SKILL.md").is_file())
        self.assertEqual((imported_copy / "notes.txt").read_text(encoding="utf-8"), "copied")
        self.assertFalse((imported_copy / MANAGED_MARKER).exists())
        self.assertTrue((self.install_dir / "manual-skill").is_symlink())
        self.assertEqual((self.install_dir / "manual-skill").resolve(), imported_copy.resolve())
        self.assertIn("Import complete.", output.getvalue())

    def test_cli_import_imports_all_unmanaged_installed_skills(self) -> None:
        unmanaged = self.install_dir / "manual-skill"
        unmanaged.mkdir(parents=True)
        (unmanaged / "SKILL.md").write_text("# manual\n", encoding="utf-8")
        monitored = self.write_local_skill("learning-notes")
        self.install_dir.mkdir(parents=True, exist_ok=True)
        if not (self.install_dir / monitored.name).exists():
            (self.install_dir / monitored.name).symlink_to(monitored)
        self.write_settings([])

        stdout = io.StringIO()
        exit_code = cli_main(
            [
                "import",
                "--settings",
                str(self.settings_path),
            ],
            input_fn=lambda _: "s",
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(exit_code, 0)
        self.assertTrue((self.imported_dir / "manual-skill" / "SKILL.md").is_file())
        self.assertTrue((self.install_dir / "manual-skill").is_symlink())
        self.assertIn("Imported installed skill into repo: manual-skill", stdout.getvalue())

    def test_cli_import_conflicting_name_can_skip(self) -> None:
        self.write_local_skill("learning-notes")
        installed = self.install_dir / "learning-notes"
        installed.mkdir(parents=True)
        (installed / "SKILL.md").write_text("# managed elsewhere\n", encoding="utf-8")
        self.write_settings([])

        stdout = io.StringIO()
        exit_code = cli_main(
            [
                "import",
                "--settings",
                str(self.settings_path),
                "learning-notes",
            ],
            input_fn=lambda _: "s",
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(exit_code, 0)
        self.assertFalse((self.imported_dir / "learning-notes").exists())
        self.assertIn("Skipped monitored skill during import: learning-notes", stdout.getvalue())

    def test_cli_list_shows_all_sections(self) -> None:
        self.write_local_skill("learning-notes")
        self.write_imported_skill("obsidian-cli")
        self.write_settings(
            [
                {
                    "name": "third-party",
                    "type": "path",
                    "path": str(self.repo_root / "vendor" / "third-party"),
                }
            ]
        )
        unmanaged = self.install_dir / "manual-skill"
        unmanaged.mkdir(parents=True)
        (unmanaged / "SKILL.md").write_text("# manual\n", encoding="utf-8")

        stdout = io.StringIO()
        exit_code = cli_main(
            [
                "list",
                "--settings",
                str(self.settings_path),
            ],
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("First-Party:", output)
        self.assertIn("- learning-notes", output)
        self.assertIn("Imported:", output)
        self.assertIn("- obsidian-cli", output)
        self.assertIn("Configured Third-Party:", output)
        self.assertIn("- third-party", output)
        self.assertIn("Unmanaged Installed:", output)
        self.assertIn("- manual-skill", output)


if __name__ == "__main__":
    unittest.main()
