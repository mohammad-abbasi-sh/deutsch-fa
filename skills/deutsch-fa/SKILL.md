---
name: deutsch-fa
description: German declension for Persian speakers — decline any noun (der/die/das + 4 cases, adjective endings, possessive forms) with a deterministic zero-dependency tool, predict noun gender from ending rules with Persian explanations, check a learner's German sentence for article/case errors, drill with quizzes, and export Anki cards. Use when writing or correcting German for Persian-speaking learners, when an agent must not guess a noun's gender, or when building German-learning features. Never guess der/die/das — look it up.
---

# German declension for Persian speakers — look it up, never guess it

Persian has no grammatical gender, so for Persian-speaking learners every
German noun starts with the same question: *der, die oder das?* Agents
answering from memory get this wrong constantly — and a wrong article
poisons the whole case paradigm. This skill makes the article, the case
and the ending **deterministic**: a zero-dependency engine plus a
hand-checked A1 noun list (199 nouns, gender + plural + Persian gloss),
with every explanation in Persian.

## The contract

1. **Never guess der/die/das.** When German text is on the table, run the
   bundled tool (pure stdlib, no downloads, no API):

   ```bash
   python3 scripts/deutsch_fa.py decline <noun> [--json]
   ```

   It prints the full paradigm — definite / indefinite / negative articles
   across Nominativ, Akkusativ, Dativ, Genitiv, singular and plural —
   plus possessive forms, weak adjective endings with an example, the
   Persian gloss, and the traps (N-Deklination, das Mädchen, des Busses).
   If the noun is not in the curated list, the tool says so and falls
   back to a rule-based gender *hint* labelled as a guess — then check a
   dictionary. Exit codes: `0` = declined · `1` = noun not in the list
   (hint printed) · `2` = usage error.

2. **Predict gender with the rules, stated honestly.** Endings predict
   gender with known reliability — `-ung/-heit/-keit` → feminine (very
   reliable), `-chen/-lein` → neuter (very reliable), days/months/seasons
   → masculine (reliable), `-e` → feminine (strong tendency; memorize
   *der Junge, der Name, der Käse* as exceptions). See
   `references/gender-rules.md` for the full table with reliability
   labels, and use `rules [word]` to apply them:

   ```bash
   python3 scripts/deutsch_fa.py rules Wohnung
   python3 scripts/deutsch_fa.py rules Kuchen   # warns: looks neuter, is masculine
   ```

3. **Check learner sentences conservatively.** The checker only flags
   what it can decide — a verb frame (`sehen` → Akkusativ,
   `helfen` → Dativ, `geben` → Dativ + Akkusativ) or a case-governing
   preposition (`mit` → Dativ, `für` → Akkusativ) plus a noun from the
   curated list:

   ```bash
   python3 scripts/deutsch_fa.py check "Ich sehe der Mann" [--json]
   # → «der Mann» → «den Mann», with a Persian explanation
   ```

   It also catches N-declension nouns (`den Student` → `den Studenten`)
   and adjective endings (`den kleine Mann` → `den kleinen Mann`).
   Exit codes: `0` = no findings · `1` = findings · `2` = usage error.
   **No finding is not a proof of correctness** — say that when reporting.

4. **Drill and export.** `quiz [--n 5] [--ask article|plural|akkusativ]`
   runs an interactive drill; `anki [--out cards.tsv]` exports the whole
   list as Anki-importable TSV (front: noun + Persian gloss, back:
   article + plural).

## Know the limits — and say them

- The curated list is A1 core vocabulary (199 nouns, v0.1.0). It does not
  replace a dictionary for words outside it.
- The sentence checker is deliberately conservative: unknown nouns,
  subordinate clauses and Wechselpräpositionen (`in/an/auf` — position vs.
  direction) are left alone rather than guessed.
- Genitive singular `-es`/`-s` follows the standard monosyllabic rule
  with the known spelling exceptions encoded (`des Busses`); rare
  alternatives are not listed.
- This is a deterministic reference, not a teacher: it cannot judge
  style, word choice or whether a sentence sounds natural.

## Layout

- `scripts/deutsch_fa.py` — the engine (declension, rules, checker,
  quiz, Anki export). Loads `data/nouns.json` relative to itself.
- `data/nouns.json` — the hand-checked noun list. Contributions welcome:
  keep the schema (`de`, `gender` ∈ m/f/n/pl, `plural` or null,
  `fa`), and verify gender + plural against a dictionary before adding.
- `references/declension-tables.md` — the full article/adjective/
  possessive tables as a readable reference.
- `references/gender-rules.md` — the gender-prediction rules with
  reliability labels and the exception list.
