#!/usr/bin/env python3
"""Verify every `gplay` command and flag used in the skills against the CLI's
generated command reference (GPLAY.md).

This guards against skills drifting away from the real CLI surface — the exact
failure the April-2026 audit found (fabricated flags like `--developer-id`,
`--cluster-id`, `--release-notes-locale`, wrong `--rollout` units, etc.).

Usage:
    python3 scripts/check-commands.py --reference /path/to/GPLAY.md
    python3 scripts/check-commands.py            # downloads GPLAY.md from main

Exit code 0 = clean, 1 = drift found.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

RAW_GPLAY_MD = "https://raw.githubusercontent.com/tamtom/play-console-cli/main/GPLAY.md"

# Global flags accepted on (nearly) any command — not always spelled out per
# command in GPLAY.md, so whitelist them to avoid false positives.
GLOBAL_FLAGS = {
    "--help", "--output", "--pretty", "--package", "--profile", "--dry-run",
    "--debug", "--paginate", "--confirm", "--json", "--output-file",
}

# Tokens that end a command path (start of args/flags/placeholders/shell).
_STOP = re.compile(r"^(--|-[a-zA-Z]|<|\$|\{|\||>|&|@|\"|')")
_CMD_WORD = re.compile(r"^[a-z][a-z0-9-]*$")
_GPLAY_INVOCATION = re.compile(r"\bgplay\s+([^\n`]*)")
_FLAG = re.compile(r"(--[a-z][a-z0-9-]*)")


def load_reference(text: str):
    """Return (set of valid command-path tuples, set of valid flag tokens)."""
    cmds, flags = set(), set()
    for line in text.splitlines():
        m = re.match(r"^##\s+gplay\s+(.+?)\s*$", line)
        if m:
            words = tuple(m.group(1).split())
            if all(_CMD_WORD.match(w) for w in words):
                cmds.add(words)
        flags.update(_FLAG.findall(line))
    return cmds, flags


def command_path(arg_str: str):
    """Extract the leading command-path words from a `gplay ...` invocation."""
    words = []
    for tok in arg_str.strip().split():
        if _STOP.match(tok) or not _CMD_WORD.match(tok):
            break
        words.append(tok)
    return tuple(words)


def path_is_valid(path, valid_cmds, groups):
    """Validate a command path against the known surface.

    - Exact match to a known command → valid.
    - Otherwise take the longest known prefix P:
        * P is a GROUP (has subcommands) → the next word should have been a
          subcommand but isn't a known one → INVALID (catches fabricated leaves
          like `vitals crashes list`, `testers list`, `performance overview`).
        * P is a LEAF (executable) → trailing words are positional args → valid.
    - No known prefix at all → INVALID (unknown top-level command)."""
    if not path:
        return True  # bare `gplay` / `gplay <command>` placeholder
    if path in valid_cmds:
        return True
    for i in range(len(path), 0, -1):
        prefix = path[:i]
        if prefix in valid_cmds:
            return prefix not in groups  # group needs a real subcommand next
    return False


def code_segments(line: str, in_fence: bool):
    """Yield the parts of a line that are code: the whole line inside a ```fence,
    else only the spans wrapped in `backticks`. Prose mentions of "gplay" are
    ignored so they don't read as command invocations."""
    if in_fence:
        yield line
    else:
        yield from re.findall(r"`([^`]*)`", line)


def check_skill(md_path: Path, valid_cmds, valid_flags, groups):
    problems = []
    in_fence = False
    for lineno, line in enumerate(md_path.read_text().splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        for seg in code_segments(line, in_fence):
            for arg_str in _GPLAY_INVOCATION.findall(seg):
                path = command_path(arg_str)
                # skip placeholders: `gplay <command>`, `gplay --help`
                if path and not path_is_valid(path, valid_cmds, groups):
                    problems.append((lineno, "command", "gplay " + " ".join(path)))
                for flag in _FLAG.findall(arg_str):
                    if flag not in valid_flags and flag not in GLOBAL_FLAGS:
                        problems.append((lineno, "flag", flag))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", help="Path to GPLAY.md (else download from main)")
    ap.add_argument("--skills-dir", default=str(Path(__file__).resolve().parent.parent / "skills"))
    args = ap.parse_args()

    if args.reference:
        ref_text = Path(args.reference).read_text()
    else:
        with urllib.request.urlopen(RAW_GPLAY_MD) as r:  # noqa: S310
            ref_text = r.read().decode()

    valid_cmds, valid_flags = load_reference(ref_text)
    if not valid_cmds:
        print("ERROR: no commands parsed from reference — is GPLAY.md valid?", file=sys.stderr)
        return 2

    # A command is a "group" if any other known command extends it as a prefix.
    groups = {c for c in valid_cmds
              if any(o != c and o[:len(c)] == c for o in valid_cmds)}

    total = 0
    for skill in sorted(Path(args.skills_dir).glob("*/SKILL.md")):
        problems = check_skill(skill, valid_cmds, valid_flags, groups)
        if problems:
            total += len(problems)
            print(f"\n✗ {skill.parent.name}")
            for lineno, kind, tok in problems:
                print(f"    L{lineno}  unknown {kind}: {tok}")

    if total:
        print(f"\n{total} drift issue(s) found — fix against GPLAY.md.", file=sys.stderr)
        return 1
    print(f"✓ All skill commands/flags valid against the CLI reference "
          f"({len(valid_cmds)} commands known).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
