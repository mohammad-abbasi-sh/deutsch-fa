# Cursor — deutsch-fa rule

`cursor/deutsch-fa.mdc` is the Cursor version of this skill. It carries
the same contract in condensed form: never guess der/die/das (decline
with the tool), predict gender with honestly-labelled rules, check
learner sentences conservatively, and state the limits.

## Install — Cursor

Copy `cursor/deutsch-fa.mdc` into your project's `.cursor/rules/`
directory (create it if needed). Cursor applies it automatically. The
rule points at the checker script — copy the whole
`skills/deutsch-fa/` directory into your project, or install the
checker where the rule's commands can find it.

## Install — Windsurf

Copy `cursor/deutsch-fa.mdc` to `.windsurf/rules/deutsch-fa.mdc` in your
project. Windsurf loads `.mdc` rules from that directory. Copy
`skills/deutsch-fa/` alongside it so the script paths resolve.

## Install — Cline / Continue

Cline and Continue use plain Markdown rules:

- **Cline:** copy the contents of `cursor/deutsch-fa.mdc` (without the
  frontmatter block) into `.clinerules/deutsch-fa.md`, and copy
  `skills/deutsch-fa/` into your project.
- **Continue:** copy the same Markdown body into
  `.continue/rules/deutsch-fa.md`, and copy `skills/deutsch-fa/` into
  your project.

In both cases the rule's commands assume the checker lives at
`skills/deutsch-fa/scripts/deutsch_fa.py` relative to the project root —
keep that layout.

## What it covers

- The no-guessing contract (decline with the tool, not from memory).
- Gender-prediction rules with reliability labels and the exception list.
- Conservative sentence checking (verb frames, case prepositions,
  N-declension, adjective endings) — and the "no finding ≠ correct" rule.
- Quiz drills and Anki export.
- The limits (A1 list is not a dictionary; reference, not a teacher).

The full skill with references and the MCP server lives in
`skills/deutsch-fa/` and `mcp-server/`.
