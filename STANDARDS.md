# cantica-tech code standards

The rules every cantica-tech repository follows, and why. The configs in this repository are the single source;
a repository holds a synced copy in `.standards/` (never edited there) plus thin configs of its own that extend it
and hold only its **ratchet** — the existing violations it has not fixed yet, which only ever shrink.

## Principles

1. One source of truth: every rule and tool version is set here.
2. Same commands everywhere: `task lint`, `task format`, `task typecheck`, `task standards:sync`,
   `task standards:check`; CI runs exactly these (`.github/workflows/lint.yml`).
3. Formatters own layout (Ruff format, Prettier); linters flag what a formatter cannot fix.
4. Strict for new code, a ratchet for old code; CI fails on any new violation.
5. Exact tool versions, raised by pull requests (Renovate / Dependabot), never silently.
6. Product-agnostic: these are engineering rules, not a product feature.

## Per language

| Language | Format | Lint | Types | Notes |
|---|---|---|---|---|
| Python ≥ 3.11 | Ruff format, 120 columns | Ruff: `E W F I B UP SIM C4 PTH RUF PL S N` | Pyright `standard`, `strict` per new module | tests may `assert`; lazy imports allowed; complexity counts reviewed, not gated |
| TypeScript | Prettier, 120 columns | ESLint ≥ 9 flat config + typescript-eslint `strictTypeChecked` + `stylisticTypeChecked` (`typescript/eslint.config.mjs`); ratchet: ESLint bulk suppressions | `tsc` strict + `noUncheckedIndexedAccess`, `noImplicitOverride`, `noFallthroughCasesInSwitch` (`typescript/tsconfig.strict.json`) | |
| Markdown | none (prose is hand-wrapped, never reflowed) | markdownlint (`markdown/markdownlint.jsonc`) | — | no line length; compact tables |
| YAML | — | yamllint (`yaml/yamllint.yaml`) | — | no line length |
| GitHub Actions | — | actionlint; zizmor (medium and above) | — | third-party actions pinned to a commit SHA; least `permissions:` |
| Shell | — | ShellCheck (`shell/.shellcheckrc`) | — | |
| TOML | Taplo (`toml/taplo.toml`) | — | — | |
| Everything | EditorConfig (UTF-8, LF, final newline) | — | — | secrets scanning (gitleaks) comes in v0.2 |

## Using it in a repository

1. Check this repository out next to it (`../standards`), then `task standards:sync` (or
   `python3 ../standards/scripts/sync.py .`): copies `.standards/`, `.editorconfig`, … and creates the thin configs
   once (`ruff.toml`, `pyrightconfig.json`, `.markdownlint-cli2.jsonc`, `.yamllint.yaml`).
2. Include `Taskfile.standards.yml` in the repository's Taskfile:

   ```yaml
   includes:
     standards:
       taskfile: '{{.STANDARDS_DIR | default "../standards"}}/Taskfile.standards.yml'
       optional: true
       flatten: true
   ```

3. Call the reusable workflow in CI, at the same tag as the sync:

   ```yaml
   jobs:
     standards:
       uses: cantica-tech/standards/.github/workflows/lint.yml@v0.1.0
       with: { ref: v0.1.0 }
   ```

4. TypeScript: the sync writes `.standards/eslint-standard.mjs` (not named eslint.config.*: ESLint would take it for that folder's config), `.standards/tsconfig.strict.json` and
   `.prettierrc.json`, and creates `eslint.config.mjs` once. Add the devDependencies `eslint`, `@eslint/js`,
   `typescript-eslint`, `eslint-config-prettier`; make the base tsconfig `"extends"` the strict one. Existing
   violations: `npx eslint --suppress-all` once (the ratchet file `eslint-suppressions.json`), then
   `--prune-suppressions` as they are fixed.

## Exceptions

Per line (`# noqa: <rule>` / `// eslint-disable-next-line <rule> -- <reason>`) with a reason, or per file in the
repository's thin config with a comment. A rule is turned off for everyone only here, by pull request.
