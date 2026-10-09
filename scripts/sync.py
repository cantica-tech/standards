#!/usr/bin/env python3
"""Sync the cantica-tech standards into a repository, or check it has not drifted.

    python3 scripts/sync.py <repository> [--check]

For each language the repository holds (by its tracked files), the standard's
config is copied into `<repository>/.standards/` (synced, never edited there)
or, for the ones a repository never ratchets, to its root (`.editorconfig`,
`.shellcheckrc`, `.taplo.toml`). The repository's own thin configs, which
extend `.standards/` and hold only its ratchet, are created once when missing
and never overwritten. `.standards/VERSION` records the standards version.

`--check` writes nothing and exits 1 when a synced file differs or is missing
(CI: the repository runs the standard it claims). Stdlib only.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# language -> (detecting suffixes, synced files {source: target}, thin configs {target: text})
LANGUAGES: dict[str, tuple[tuple[str, ...], dict[str, str], dict[str, str]]] = {
    "all": ((), {".editorconfig": ".editorconfig"}, {}),
    "python": ((".py",), {"python/ruff.toml": ".standards/ruff.toml",
                          "python/pyrightconfig.base.json": ".standards/pyright.json"}, {
        "ruff.toml": '# Ruff: the cantica-tech standard plus this repository\'s ratchet only.\n'
                     'extend = ".standards/ruff.toml"\n',
        "pyrightconfig.json": '{\n  "extends": "./.standards/pyright.json",\n  "include": ["."],\n'
                              '  "exclude": ["**/node_modules", "**/.venv", "dist", "out"]\n}\n'}),
    "markdown": ((".md",), {"markdown/markdownlint.jsonc": ".standards/markdownlint.jsonc"}, {
        ".markdownlint-cli2.jsonc": '{\n  "config": { "extends": ".standards/markdownlint.jsonc" },\n'
                                    '  "ignores": ["**/node_modules/**", "**/dist/**", "**/out/**"]\n}\n'}),
    "yaml": ((".yml", ".yaml"), {"yaml/yamllint.yaml": ".standards/yamllint.yaml"}, {
        ".yamllint.yaml": "extends: .standards/yamllint.yaml\n"}),
    "toml": ((".toml",), {"toml/taplo.toml": ".taplo.toml"}, {}),
    "shell": ((".sh", ".bash"), {"shell/.shellcheckrc": ".shellcheckrc"}, {}),
}


def tracked(repo: Path) -> list[str]:
    out = subprocess.run(["git", "-C", str(repo), "ls-files"], capture_output=True, text=True, check=False)
    if out.returncode == 0:
        return out.stdout.splitlines()
    return [p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts]


def languages(repo: Path) -> list[str]:
    files = tracked(repo)
    found = ["all"]
    for name, (suffixes, _, _) in LANGUAGES.items():
        if suffixes and any(f.endswith(suffixes) for f in files if not f.startswith(".standards/")):
            found.append(name)
    return found


def version() -> str:
    tag = subprocess.run(["git", "-C", str(HERE), "describe", "--tags", "--always", "--dirty"],
                         capture_output=True, text=True, check=False).stdout.strip()
    return tag or (HERE / "VERSION").read_text(encoding="utf-8").strip()


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    check = "--check" in argv
    if len(args) != 1:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    repo = Path(args[0]).resolve()
    drift, written = [], []
    for name in languages(repo):
        _, synced, thin = LANGUAGES[name]
        for source, target in synced.items():
            text = (HERE / source).read_text(encoding="utf-8")
            dest = repo / target
            if dest.is_file() and dest.read_text(encoding="utf-8") == text:
                continue
            if check:
                drift.append(f"{target} ({'differs from' if dest.exists() else 'missing; from'} standards {source})")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            written.append(target)
        for target, text in thin.items():
            dest = repo / target
            if not dest.exists():
                if check:
                    drift.append(f"{target} (missing: the repository's own config extending .standards/)")
                    continue
                dest.write_text(text, encoding="utf-8")
                written.append(f"{target} (created once; yours to ratchet)")
    if check:
        if drift:
            print("standards drift — run `task standards:sync` (or scripts/sync.py <repo>):")
            print("\n".join(f"  - {d}" for d in drift))
            return 1
        print(f"standards: in sync ({', '.join(languages(repo))})")
        return 0
    if written:
        (repo / ".standards").mkdir(exist_ok=True)
        (repo / ".standards" / "VERSION").write_text(version() + "\n", encoding="utf-8")
    print("\n".join(written) if written else "standards: nothing to change")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
