import os
import subprocess
from pathlib import Path


def executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def test_preview_reads_underscore_action_inputs(tmp_path: Path) -> None:
    """Docker Action input IDs must survive the POSIX shell environment."""
    binaries = tmp_path / "bin"
    workspace = tmp_path / "workspace"
    capture = tmp_path / "arguments"
    binaries.mkdir()
    workspace.mkdir()
    executable(binaries / "git", "#!/bin/sh\nexit 0\n")
    executable(
        binaries / "changelog-fragments",
        '#!/bin/sh\nprintf "%s\\n" "$*" > "$CAPTURE"\n',
    )
    environment = {
        **os.environ,
        "PATH": f"{binaries}:{os.environ['PATH']}",
        "CAPTURE": str(capture),
        "GITHUB_WORKSPACE": str(workspace),
        "INPUT_COMMAND": "preview",
        "INPUT_BASE_REF": "base",
        "INPUT_HEAD_REF": "head",
        "INPUT_FRAGMENT_DIR": "notes",
        "INPUT_PR_NUMBER": "42",
        "INPUT_POST_COMMENT": "false",
    }
    environment.pop("GITHUB_REPOSITORY", None)

    subprocess.run(
        ("sh", str(Path(__file__).parents[1] / "entrypoint.sh")),
        check=True,
        env=environment,
    )

    assert capture.read_text().strip() == (
        "preview --base-ref base --head-ref head --fragment-dir notes --pr-number 42"
    )
