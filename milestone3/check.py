"""Deterministic pinned test-environment check; standard library only.

Verifies the pinned test dependencies before running the suite, so a
missing or mismatched environment fails fast with an actionable recovery
command instead of surfacing as application or test defects.
"""

import argparse
import subprocess
import sys

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _metadata_version
except ImportError:  # pragma: no cover - very old interpreters
    from importlib_metadata import PackageNotFoundError  # type: ignore
    from importlib_metadata import version as _metadata_version  # type: ignore

PINNED = (("jsonschema", "4.25.1"), ("PyYAML", "6.0.2"))

RECOVERY_COMMAND = (
    "uv run --offline --no-project "
    "--with jsonschema[format]==4.25.1 "
    "--with PyYAML==6.0.2 "
    "python -m unittest discover -s tests -q"
)


def version_of(distribution):
    """Installed distribution version; raises PackageNotFoundError if absent."""
    return _metadata_version(distribution)


def find_problems():
    """Return human-readable version problems, or an empty list when pinned."""
    problems = []
    for distribution, expected in PINNED:
        try:
            installed = version_of(distribution)
        except PackageNotFoundError:
            problems.append("%s==%s is not installed" % (distribution, expected))
            continue
        except Exception as exc:
            problems.append("%s lookup failed: %s" % (distribution, exc))
            continue
        if installed != expected:
            problems.append(
                "%s==%s is required but %s is installed" % (distribution, expected, installed)
            )
    return problems


def build_parser():
    parser = argparse.ArgumentParser(
        description="Check the pinned test environment, then run the test suite."
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="print the pinned recovery test command and exit",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.print_command:
        sys.stdout.write(RECOVERY_COMMAND + "\n")
        return 0
    problems = find_problems()
    if problems:
        sys.stderr.write(
            "test environment mismatch: %s. Run: %s\n" % ("; ".join(problems), RECOVERY_COMMAND)
        )
        return 2
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
