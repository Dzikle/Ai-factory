"""Allow only formatter-body/test edits against one immutable Git commit."""

import ast
from pathlib import Path
import re
import subprocess
import sys


def protected(source):
    tree = ast.parse(source)
    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and node.name == "format_scorecard"]
    if len(definitions) != 1:
        raise ValueError("Exactly one formatter definition is required")
    # Keep arguments, defaults, decorators, returns and sync/async identity.
    definitions[0].body = [ast.Pass()]
    return ast.dump(tree, include_attributes=False)


def main(base):
    if not re.fullmatch(r"[a-f0-9]{40}", base):
        raise ValueError("The evaluation base must be a full Git commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"], check=True, capture_output=True)
    changed = subprocess.check_output(["git", "diff", "--name-only", base, "HEAD"], text=True).splitlines()
    if not changed or not set(changed) <= {"milestone2/scorecard.py", "tests/test_scorecard_format.py"}:
        raise ValueError("Candidate scope changed")
    reference = subprocess.check_output(["git", "show", base + ":milestone2/scorecard.py"])
    if protected(Path("milestone2/scorecard.py").read_bytes()) != protected(reference):
        raise ValueError("Protected collector or formatter signature changed")


if __name__ == "__main__":
    main(sys.argv[1])
