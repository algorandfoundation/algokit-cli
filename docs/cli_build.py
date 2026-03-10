#!/usr/bin/env python3
"""Generate CLI reference markdown from Click source using Sphinx + sphinx-click,
then post-process the output for Starlight consumption.

Run via: uv run poe docs-cli
Or directly: uv run --group docs python docs/cli_build.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
REPO_ROOT = DOCS_DIR.parent
CLI_OUT = DOCS_DIR / "src" / "content" / "docs" / "cli"


def _clean_cli_output() -> None:
    """Remove previous CLI reference output."""
    print("==> Cleaning previous CLI output...")
    if CLI_OUT.exists():
        shutil.rmtree(CLI_OUT)
    CLI_OUT.mkdir(parents=True, exist_ok=True)


def _run_sphinx_build() -> None:
    """Run Sphinx markdown build to generate CLI reference docs."""
    print("==> Running Sphinx + sphinx-click build...")
    result = subprocess.run(
        [
            "uv",
            "run",
            "--group",
            "docs",
            "sphinx-build",
            "-b",
            "markdown",
            "-E",  # force fresh build (don't reuse cached environment)
            "-q",  # quiet
            "docs/sphinx",
            str(CLI_OUT),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: Sphinx build failed (exit code {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        sys.exit(1)


def _remove_sphinx_artifacts() -> None:
    """Remove Sphinx build artifacts not needed by Starlight."""
    print("==> Removing Sphinx artifacts...")
    for name in [".buildinfo"]:
        p = CLI_OUT / name
        if p.exists():
            p.unlink()
    doctrees = CLI_OUT / ".doctrees"
    if doctrees.exists():
        shutil.rmtree(doctrees)


def _inject_frontmatter() -> None:
    """Inject Starlight frontmatter into the generated CLI reference page."""
    print("==> Injecting Starlight frontmatter...")
    index_md = CLI_OUT / "index.md"
    if not index_md.exists():
        print("ERROR: Expected index.md not found after Sphinx build.", file=sys.stderr)
        sys.exit(1)

    content = index_md.read_text(encoding="utf-8")

    # Extract title from H1 if present, otherwise use a default
    title = "AlgoKit CLI Reference"
    h1_match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()
        # Strip the H1 line — Starlight renders frontmatter title as H1
        content = re.sub(r"^#\s+[^\n]+\n(\n)?", "", content, count=1)

    escaped_title = title.replace('"', '\\"')
    index_md.write_text(
        f'---\ntitle: "{escaped_title}"\n---\n\n{content}',
        encoding="utf-8",
    )


def main() -> None:
    """Run the full CLI docs build pipeline."""
    _clean_cli_output()
    _run_sphinx_build()
    _remove_sphinx_artifacts()
    _inject_frontmatter()

    file_count = sum(1 for _ in CLI_OUT.rglob("*.md"))
    print(f"==> CLI reference generated at: {CLI_OUT}")
    print(f"    {file_count} markdown file(s)")


if __name__ == "__main__":
    main()
