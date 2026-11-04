# deutsch-fa — German declension for Persian speakers

A deterministic **Agent Skill** for the hardest daily question of
Persian-speaking German learners: *der, die oder das?*

Persian has no grammatical gender, so every German noun starts from
zero — and agents answering from memory get articles wrong constantly.
`deutsch-fa` makes the article, the case and the ending **deterministic**:
a zero-dependency Python engine plus a hand-checked A1 noun list
(199 nouns — gender, plural, Persian gloss), with every explanation in
Persian.

No model calls. No downloads. No API keys. Python 3.8+ standard library
only.

## The problem

```
Learner writes:   Ich sehe der Mann.
Agent (guessing): looks fine ✓          ← wrong, and now the learner
                                          memorizes "der Mann" in Akkusativ

With deutsch-fa:
$ python3 scripts/deutsch_fa.py check "Ich sehe der Mann"
⚠ 1 finding:
• «der Mann» → «den Mann»
  بعد از «sehen» حالت Akkusativ می‌آید؛ «Mann» (مرد) مذکر است…
```

Before/after, from the engine:

| Before (guessed) | After (deutsch-fa) |
|---|---|
| *der Mädchen* | **das** Mädchen — diminutive `-chen` is always neuter |
| *Ich helfe den Mann* | *Ich helfe **dem** Mann* — helfen takes Dativ |
| *Ich sehe den Student* | *Ich sehe den **Studenten*** — N-Deklination |
| *den kleine Mann* | *den **kleinen** Mann* — weak adjective ending |
| *des Bus* | *des **Busses*** — spelling exception encoded |

## What's inside

```
skills/deutsch-fa/
  SKILL.md                  the agent skill (the contract)
  scripts/deutsch_fa.py     the engine — decline, rules, check, quiz, anki
  data/nouns.json           199 hand-checked A1 nouns (de/gender/plural/fa)
  references/
    declension-tables.md    full article/adjective/possessive tables
    gender-rules.md         gender-prediction rules with reliability labels
cursor/deutsch-fa.mdc       the Cursor rule (same contract, condensed)
mcp-server/                 MCP server (stdio) exposing 4 tools
tests/                      59 tests, all passing (stdlib unittest)
dist/deutsch-fa-skill.zip   ready-to-upload Claude.ai skill bundle
```

Commands:

```bash
python3 scripts/deutsch_fa.py decline Mann
# der Mann · مرد · مذکر — full 4-case paradigm, singular + plural,
# indefinite/negative/possessive articles, adjective endings

python3 scripts/deutsch_fa.py rules Wohnung     # gender prediction
python3 scripts/deutsch_fa.py rules Kuchen      # warns: looks neuter, is masculine
python3 scripts/deutsch_fa.py check "Ich gebe die Frau das Buch"
python3 scripts/deutsch_fa.py quiz --n 5 --ask akkusativ
python3 scripts/deutsch_fa.py anki --out cards.tsv
```

## Install

**Claude Code** — copy `skills/deutsch-fa/` into your project's skills
directory (or `~/.claude/skills/` for global use). The skill's
`SKILL.md` frontmatter makes it discoverable; the script path in the
commands is relative to the skill directory.

**Claude.ai** — upload `dist/deutsch-fa-skill.zip` as a skill (the zip
contains `SKILL.md`, the script, the noun data and the references).

**Cursor** — copy `cursor/deutsch-fa.mdc` to `.cursor/rules/` and
`skills/deutsch-fa/` into your project. Windsurf / Cline / Continue:
see `cursor/README.md`.

**Any MCP client** — point your client at the stdio server:

```json
{
  "mcpServers": {
    "deutsch-fa": {
      "command": "python3",
      "args": ["/path/to/mcp-server/deutsch_fa_mcp_server.py"]
    }
  }
}
```

Tools: `decline`, `check_sentence`, `gender_hint`, `anki_export`.

## Why not just another app?

The DER DIE DAS app, V-IZ and similar are *apps for learners* — this is
a *tool for agents*: deterministic, scriptable, CI-friendly, with JSON
output and an MCP interface, so a tutor agent, a content pipeline or a
classroom bot can decline, check and quiz without guessing. The 199-noun
dataset is original and hand-checked; the engine encodes the standard
reference grammar (article/adjective/possessive paradigms, N-Deklination,
weak *das Herz*, dative-plural `-n`, genitive `-es`/`-s`).

## Honest limits

- The list is A1 core vocabulary (v0.1.0) — not a dictionary for words
  outside it; unknown nouns get a labelled *hint*, not an answer.
- The sentence checker is deliberately conservative: unknown nouns,
  subordinate clauses and Wechselpräpositionen are left alone rather
  than guessed. No finding ≠ correct.
- A deterministic reference, not a teacher: no judgment on style or
  naturalness.

## Roadmap

- Grow the noun list toward 500 (B1), community contributions welcome
  (schema in `SKILL.md` — verify gender + plural against a dictionary).
- Verb-frame coverage for subordinate clauses and reflexive verbs.
- Example sentence per noun (hand-written, case-correct).
- Spaced-repetition scheduling for `quiz`.
- Adjective vocabulary with gradation (gut/besser/am besten).

## License

MIT — see LICENSE.
