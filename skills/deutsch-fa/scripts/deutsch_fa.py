#!/usr/bin/env python3
"""deutsch-fa — German declension for Persian speakers.

A deterministic, zero-dependency (Python standard library only) tool that
answers the hardest daily question of Persian-speaking German learners:
which article (der/die/das), in which case, with which ending.

Commands:
    decline <noun> [--json]      full declension table (articles, possessive,
                                 adjective endings), with Persian glosses
    rules [word]                 gender-prediction rules; with a word, apply
                                 them and compare against the curated list
    check "<sentence>" [--json]  flag wrong articles / N-declension / adjective
                                 endings where deterministically decidable
    quiz [--n 5] [--ask ...]     interactive drill (article/plural/akkusativ)
    anki [--out file.tsv]        Anki-importable TSV of the noun list

Exit codes: 0 = ok (check: no findings) · 1 = findings / noun not in the
curated list · 2 = usage error.

The curated noun list (skills/deutsch-fa/data/nouns.json) is hand-written
and hand-checked; it is loaded relative to this script, so the skill works
wherever the directory is copied.
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nouns.json"

CASES = ["nom", "akk", "dat", "gen"]
CASE_DE = {"nom": "Nominativ", "akk": "Akkusativ",
           "dat": "Dativ", "gen": "Genitiv"}
CASE_FA = {"nom": "فاعلی", "akk": "مفعولیِ مستقیم",
           "dat": "مفعولیِ غیرمستقیم", "gen": "اضافه (ملکی)"}
GENDER_DE = {"m": "maskulin", "f": "feminin",
             "n": "neutral", "pl": "Plural"}
GENDER_FA = {"m": "مذکر", "f": "مؤنث", "n": "خنثی", "pl": "جمع"}

DEFINITE = {
    "m": {"nom": "der", "akk": "den", "dat": "dem", "gen": "des"},
    "f": {"nom": "die", "akk": "die", "dat": "der", "gen": "der"},
    "n": {"nom": "das", "akk": "das", "dat": "dem", "gen": "des"},
    "pl": {"nom": "die", "akk": "die", "dat": "den", "gen": "der"},
}
INDEFINITE = {
    "m": {"nom": "ein", "akk": "einen", "dat": "einem", "gen": "eines"},
    "f": {"nom": "eine", "akk": "eine", "dat": "einer", "gen": "einer"},
    "n": {"nom": "ein", "akk": "ein", "dat": "einem", "gen": "eines"},
}
NEGATIVE = {
    "m": {"nom": "kein", "akk": "keinen", "dat": "keinem", "gen": "keines"},
    "f": {"nom": "keine", "akk": "keine", "dat": "keiner", "gen": "keiner"},
    "n": {"nom": "kein", "akk": "kein", "dat": "keinem", "gen": "keines"},
    "pl": {"nom": "keine", "akk": "keine", "dat": "keinen", "gen": "keiner"},
}
# possessive endings follow the ein-word pattern; euer drops its middle e
POSSESSIVE_ENDINGS = {
    "m": {"nom": "", "akk": "en", "dat": "em", "gen": "es"},
    "f": {"nom": "e", "akk": "e", "dat": "er", "gen": "er"},
    "n": {"nom": "", "akk": "", "dat": "em", "gen": "es"},
    "pl": {"nom": "e", "akk": "e", "dat": "en", "gen": "er"},
}
POSSESSIVE_STEMS = ["mein", "dein", "sein", "ihr",
                    "unser", "euer", "Ihr"]

# adjective endings: weak = after der-word, mixed = after ein-word,
# strong = with no article
WEAK_ADJ = {
    "m": {"nom": "e", "akk": "en", "dat": "en", "gen": "en"},
    "f": {"nom": "e", "akk": "e", "dat": "en", "gen": "en"},
    "n": {"nom": "e", "akk": "e", "dat": "en", "gen": "en"},
    "pl": {"nom": "en", "akk": "en", "dat": "en", "gen": "en"},
}
MIXED_ADJ = {
    "m": {"nom": "er", "akk": "en", "dat": "en", "gen": "en"},
    "f": {"nom": "e", "akk": "e", "dat": "en", "gen": "en"},
    "n": {"nom": "es", "akk": "es", "dat": "en", "gen": "en"},
    "pl": {"nom": "en", "akk": "en", "dat": "en", "gen": "en"},
}
STRONG_ADJ = {
    "m": {"nom": "er", "akk": "en", "dat": "em", "gen": "en"},
    "f": {"nom": "e", "akk": "e", "dat": "er", "gen": "er"},
    "n": {"nom": "es", "akk": "es", "dat": "em", "gen": "en"},
    "pl": {"nom": "e", "akk": "e", "dat": "en", "gen": "er"},
}
ADJ_TABLES = {"weak": WEAK_ADJ, "mixed": MIXED_ADJ, "strong": STRONG_ADJ}

# gender-prediction rules, first match wins; each is
# (test, gender, reliability_fa, explanation_fa)
GENDER_RULES = [
    (lambda w: w.endswith(("ung", "heit", "keit", "schaft", "tät",
                            "tion", "sion", "ik")),
     "f", "خیلی مطمئن",
     "اسم‌هایی که به ‎-ung‏، ‎-heit‏، ‎-keit‏، ‎-schaft‏، ‎-tät‏، ‎-tion‏، ‎-sion‏ یا ‎-ik‏ ختم می‌شوند تقریباً همیشه مؤنث‌اند (die Wohnung، die Freiheit، die Musik)."),
    (lambda w: w.endswith(("chen", "lein")),
     "n", "خیلی مطمئن",
     "پسوندهای تصغیر ‎-chen‏ و ‎-lein‏ اسم را خنثی می‌کنند (das Mädchen، das Fräulein). توجه: ‎-chen‏ در Kuchen تصغیر نیست!"),
    (lambda w: w.endswith(("ismus", "ling", "or")),
     "m", "مطمئن",
     "‎-ismus‏، ‎-ling‏ و ‎-or‏ (لاتین) معمولاً مذکرند (der Tourismus، der Lehrling، der Motor)."),
    (lambda w: w.endswith("ei"),
     "f", "گرایش",
     "‎-ei‏ (مکان/فعالیت) گرایش به مؤنث دارد (die Bäckerei)؛ استثنای معروف: das Ei."),
    (lambda w: w.endswith(("anz", "enz")),
     "f", "گرایش",
     "‎-anz‏/‎-enz‏ گرایش به مؤنث دارند (die Distanz، die Konferenz)."),
    (lambda w: w.endswith("ur"),
     "f", "گرایش",
     "‎-ur‏ گرایش به مؤنث دارد (die Natur، die Kultur)."),
    (lambda w: w.endswith(("age", "ade")),
     "f", "گرایش",
     "‎-age‏/‎-ade‏ (فرانسوی) گرایش به مؤنث دارند (die Garage، die Limonade)."),
    (lambda w: w.endswith("nis"),
     "n", "غالباً",
     "‎-nis‏ غالباً خنثی است (das Ergebnis)؛ استثناها: die Kenntnis، die Erlaubnis."),
    (lambda w: w.endswith("tum"),
     "n", "غالباً",
     "‎-tum‏ غالباً خنثی است (das Eigentum)؛ استثناها: der Reichtum، der Irrtum."),
    (lambda w: w.endswith("ment"),
     "n", "گرایش",
     "‎-ment‏ گرایش به خنثی دارد (das Dokument، das Instrument)."),
    (lambda w: w.startswith("Ge") and w.endswith("e") and len(w) > 4,
     "n", "گرایش",
     "الگوی ‎Ge-…-e‏ گرایش به خنثی دارد (das Gebäude، das Gespräch)."),
    (lambda w: w.endswith("o"),
     "n", "گرایش",
     "‎-o‏ گرایش به خنثی دارد (das Auto، das Kino)؛ استثنا: die Disco."),
    (lambda w: w.endswith("e") and len(w) > 2,
     "f", "گرایش قوی",
     "اسم‌های مختوم به ‎-e‏ گرایش قوی به مؤنث دارند (die Lampe)؛ استثناها را حفظ کن: der Junge، der Name، der Käse، das Ende."),
]

DAYS = {"Montag", "Dienstag", "Mittwoch", "Donnerstag",
        "Freitag", "Samstag", "Sonntag"}
MONTHS = {"Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember"}
SEASONS = {"Frühling", "Sommer", "Herbst", "Winter"}

# verb conjugations (common forms) -> (infinitive, case frame)
# frames: "akk" | "dat" | "dat_akk" (dative person + accusative thing)
VERB_FORMS = {}
for _inf, _frame, _forms in [
    ("sehen", "akk", ["sehe", "siehst", "sieht", "sehen", "seht", "sah"]),
    ("brauchen", "akk", ["brauche", "brauchst", "braucht", "brauchen", "braucht"]),
    ("kaufen", "akk", ["kaufe", "kaufst", "kauft", "kaufen", "kauft"]),
    ("lesen", "akk", ["lese", "liest", "liest", "lesen", "lest", "las"]),
    ("trinken", "akk", ["trinke", "trinkst", "trinkt", "trinken", "trinkt"]),
    ("essen", "akk", ["esse", "isst", "isst", "essen", "esst", "aß"]),
    ("machen", "akk", ["mache", "machst", "macht", "machen", "macht"]),
    ("haben", "akk", ["habe", "hast", "hat", "haben", "habt", "hatte"]),
    ("kennen", "akk", ["kenne", "kennst", "kennt", "kennen", "kennt"]),
    ("lieben", "akk", ["liebe", "liebst", "liebt", "lieben", "liebt"]),
    ("suchen", "akk", ["suche", "suchst", "sucht", "suchen", "sucht"]),
    ("fragen", "akk", ["frage", "fragst", "fragt", "fragen", "fragt"]),
    ("besuchen", "akk", ["besuche", "besuchst", "besucht", "besuchen", "besucht"]),
    ("verstehen", "akk", ["verstehe", "verstehst", "versteht", "verstehen", "versteht"]),
    ("nehmen", "akk", ["nehme", "nimmst", "nimmt", "nehmen", "nehmt", "nahm"]),
    ("helfen", "dat", ["helfe", "hilfst", "hilft", "helfen", "helft", "half"]),
    ("danken", "dat", ["danke", "dankst", "dankt", "danken", "dankt"]),
    ("gehören", "dat", ["gehöre", "gehörst", "gehört", "gehören", "gehört"]),
    ("gefallen", "dat", ["gefalle", "gefällst", "gefällt", "gefallen", "gefallt"]),
    ("folgen", "dat", ["folge", "folgst", "folgt", "folgen", "folgt"]),
    ("antworten", "dat", ["antworte", "antwortest", "antwortet", "antworten", "antwortet"]),
    ("glauben", "dat", ["glaube", "glaubst", "glaubt", "glauben", "glaubt"]),
    ("passen", "dat", ["passe", "passt", "passen", "passt"]),
    ("geben", "dat_akk", ["gebe", "gibst", "gibt", "geben", "gebt", "gab"]),
    ("zeigen", "dat_akk", ["zeige", "zeigst", "zeigt", "zeigen", "zeigt"]),
    ("schenken", "dat_akk", ["schenke", "schenkst", "schenkt", "schenken", "schenkt"]),
    ("bringen", "dat_akk", ["bringe", "bringst", "bringt", "bringen", "bringt"]),
    ("schicken", "dat_akk", ["schicke", "schickst", "schickt", "schicken", "schickt"]),
]:
    for _f in _forms:
        VERB_FORMS[_f] = (_inf, _frame)

PREP_CASE = {
    "mit": "dat", "bei": "dat", "nach": "dat", "von": "dat", "zu": "dat",
    "aus": "dat", "seit": "dat", "gegenüber": "dat",
    "für": "akk", "durch": "akk", "gegen": "akk", "ohne": "akk", "um": "akk",
}

# surface article form -> (kind, gender, case); used to name the kind
ARTICLE_FORMS = {}
for _g in ("m", "f", "n", "pl"):
    for _c in CASES:
        ARTICLE_FORMS.setdefault(DEFINITE[_g][_c], []).append(("def", _g, _c))
for _g in ("m", "f", "n"):
    for _c in CASES:
        ARTICLE_FORMS.setdefault(INDEFINITE[_g][_c], []).append(("indef", _g, _c))
        ARTICLE_FORMS.setdefault(NEGATIVE[_g][_c], []).append(("neg", _g, _c))
for _g in ("m", "f", "n", "pl"):
    for _c in CASES:
        ARTICLE_FORMS.setdefault(NEGATIVE[_g][_c], []).append(("neg", _g, _c))
# possessive stems are registered after possessive() is defined below


def load_nouns(path=None):
    with open(path or DATA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def noun_index(nouns):
    return {n["de"].lower(): n for n in nouns}


def find_noun(word, index):
    """Find a noun entry, tolerating a leading article and any case."""
    w = word.strip()
    for art in ("der", "die", "das", "den", "dem", "des",
                "ein", "eine", "einen", "einem", "einer", "eines"):
        if w.lower().startswith(art + " "):
            w = w[len(art) + 1:]
            break
    w = w[:1].upper() + w[1:]
    return index.get(w.lower())

# ---------------------------------------------------------------------------
# noun forms


def _vowel_groups(word):
    return re.findall(r"[aeiouäöüyAEIOUÄÖÜY]+", word)


def genitive_ending(base):
    low = base.lower()
    if low.endswith(("s", "ss", "ß", "x", "z", "tz", "zt")):
        return "es"
    if len(_vowel_groups(low)) <= 1:
        return "es"
    return "s"


def noun_form(entry, number, case):
    """Surface form of the noun for number (sg/pl) and case."""
    base = entry["de"]
    if number == "sg":
        if base == "Herz":
            return {"nom": "Herz", "akk": "Herz",
                    "dat": "Herzen", "gen": "Herzens"}[case]
        if entry.get("weak") and entry["gender"] == "m":
            if case == "nom":
                return base
            suffix = entry.get("weak_suffix",
                               "n" if base.endswith("e") else "en")
            return base + suffix
        if case == "gen" and entry["gender"] in ("m", "n"):
            if entry.get("gen_sg"):
                return entry["gen_sg"]
            return base + genitive_ending(base)
        return base
    plural = entry["plural"]
    if case == "dat" and not (plural.endswith("n") or plural.endswith("s")):
        return plural + "n"
    return plural


def possessive(stem, gender, case):
    end = POSSESSIVE_ENDINGS[gender][case]
    # euer loses the e before the r when an ending follows: euren, eurem
    stem_use = (stem[:2] + stem[3:]) if stem == "euer" and end else stem
    return stem_use + end


for _stem in POSSESSIVE_STEMS:
    for _g in ("m", "f", "n", "pl"):
        for _c in CASES:
            ARTICLE_FORMS.setdefault(
                possessive(_stem, _g, _c).lower(), []).append(("poss", _g, _c))


def adjective_form(adj, table, gender, case):
    return adj + ADJ_TABLES[table][gender][case]


def decline(entry):
    """Full declension data structure for one noun entry."""
    g = entry["gender"]
    out = {"noun": entry["de"], "gender": g, "fa": entry["fa"],
           "cases": {}, "indefinite": {}, "negative": {},
           "possessive_mein": {}, "adjective_weak": {}}
    numbers = ["sg"] if g != "pl" else []
    if g == "pl" or entry["plural"]:
        numbers.append("pl")
    for number in numbers:
        gg = g if number == "sg" else "pl"
        for case in CASES:
            art = DEFINITE[gg][case]
            out["cases"].setdefault(number, {})[case] = (
                f"{art} {noun_form(entry, number, case)}")
    if g != "pl":
        for case in CASES:
            out["indefinite"][case] = (
                f"{INDEFINITE[g][case]} {noun_form(entry, 'sg', case)}")
            out["negative"][case] = (
                f"{NEGATIVE[g][case]} {noun_form(entry, 'sg', case)}")
            out["possessive_mein"][case] = (
                f"{possessive('mein', g, case)} {noun_form(entry, 'sg', case)}")
            out["adjective_weak"][case] = (
                f"{DEFINITE[g][case]} "
                f"{adjective_form('gut', 'weak', g, case)} "
                f"{noun_form(entry, 'sg', case)}")
    return out


def decline_text(entry):
    d = decline(entry)
    g = entry["gender"]
    lines = [f"{DEFINITE[g if g != 'pl' else 'pl']['nom']} {entry['de']} · "
             f"{entry['fa']} · {GENDER_FA[g]} ({GENDER_DE[g]})"]
    if entry.get("note"):
        lines.append(f"نکته: {entry['note']}")
    elif entry.get("weak"):
        lines.append("نکته: اسم ضعیف (N-Deklination) — در همه حالت‌ها به‌جز "
                     "فاعلی مفرد ‎-(e)n‏ می‌گیرد.")
    lines.append("")
    for number in ("sg", "pl"):
        if number not in d["cases"]:
            if number == "sg":
                continue
            lines.append("جمع ندارد (غیرقابل‌شمارش).")
            break
        lines.append("مفرد (Singular):" if number == "sg"
                     else "جمع (Plural):")
        for case in CASES:
            lines.append(f"  {CASE_DE[case]} ({CASE_FA[case]}): "
                         f"{d['cases'][number][case]}")
        lines.append("")
    if g != "pl":
        lines.append("با حرف تعریف نامعین: " +
                     " / ".join(d["indefinite"][c] for c in CASES))
        lines.append("با حرف تعریف منفی: " +
                     " / ".join(d["negative"][c] for c in CASES))
        lines.append("با ملکی mein: " +
                     " / ".join(d["possessive_mein"][c] for c in CASES))
        lines.append("با صفت (مثال gut، بعد از حرف معین): " +
                     " / ".join(d["adjective_weak"][c] for c in CASES))
    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------------------
# gender prediction


def predict_gender(word):
    """Apply the ending rules to a bare noun; returns (gender, reliability,
    explanation) or None when no rule fires."""
    w = word[:1].upper() + word[1:]
    if w in DAYS or w in MONTHS or w in SEASONS:
        return ("m", "مطمئن",
                "روزهای هفته، ماه‌ها و فصل‌ها در آلمانی مذکرند "
                "(der Montag، der Januar، der Sommer).")
    for test, gender, reliability, explanation in GENDER_RULES:
        if test(w):
            return (gender, reliability, explanation)
    return None


def gender_hint(word, index):
    entry = find_noun(word, index)
    lines = []
    if entry:
        g = entry["gender"]
        lines.append(f"«{entry['de']}» ({entry['fa']}) در فهرست: "
                     f"{GENDER_FA[g]} — {DEFINITE[g if g != 'pl' else 'pl']['nom']}")
        pred = predict_gender(entry["de"])
        if pred and pred[0] == g:
            lines.append(f"قاعده هم همین را می‌گوید ({pred[1]}): {pred[2]}")
        elif pred:
            lines.append(f"⚠ قاعده‌ی صرفی «{pred[2].split('(')[0].strip()}» "
                         f"جنسیت {GENDER_FA[pred[0]]} را حدس می‌زد ({pred[1]})، "
                         f"ولی دیکشنری می‌گوید {GENDER_FA[g]} — این یک استثناست، حفظش کن.")
        else:
            lines.append("هیچ قاعده‌ی پایانی روی این اسم جواب نداد — جنسیتش را باید حفظ کرد.")
        return "\n".join(lines), 0
    pred = predict_gender(word)
    if pred:
        g, reliability, explanation = pred
        return (f"«{word}» در فهرست نیست. حدس قاعده: {GENDER_FA[g]} "
                f"({DEFINITE[g]['nom']}) — {reliability}.\n{explanation}\n"
                f"این فقط حدس است؛ برای اطمینان دیکشنری را چک کن."), 0
    return (f"«{word}» در فهرست نیست و هیچ قاعده‌ای هم روی آن جواب نداد. "
            f"جنسیت را از دیکشنری چک کن."), 1


def rules_text(word, index):
    if word:
        text, _code = gender_hint(word, index)
        return text
    lines = ["قاعده‌های حدس جنسیت اسم (به ترتیب اولویت):", ""]
    lines.append("• روزهای هفته، ماه‌ها و فصل‌ها → مذکر (مطمئن)")
    for _test, gender, reliability, explanation in GENDER_RULES:
        lines.append(f"• → {GENDER_FA[gender]} ({reliability}): {explanation}")
    lines.append("")
    lines.append("این قاعده‌ها حدس‌اند، نه قانون مطلق. استثناهای معروف را حفظ کن "
                 "(مثل das Mädchen با وجود معنای مؤنث، یا der Junge با وجود ‎-e‏).")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# sentence checking (conservative: only flags what is decidable)


def tokenize(sentence):
    return re.findall(r"[A-Za-zÄÖÜäöüß]+(?:-[A-Za-zÄÖÜäöüß]+)*", sentence)


def article_kind(form):
    """Kind of an article surface form: def/indef/neg/poss or None."""
    kinds = {k for (k, _g, _c) in ARTICLE_FORMS.get(form.lower(), [])}
    for pref in ("def", "indef", "neg", "poss"):
        if pref in kinds:
            return pref
    return None


def expected_article(kind, gender, case):
    table = {"def": DEFINITE, "indef": INDEFINITE,
             "neg": NEGATIVE}[kind]
    if kind == "indef" and gender == "pl":
        return None
    return table[gender if gender != "pl" else "pl"][case]


def find_case_anchor(tokens, art_idx):
    """Nearest verb (with frame) or case preposition before the article.

    Returns (case_frame, anchor_word, anchor_kind, verb_index) where
    verb_index is the token index of the verb or None for prepositions.
    """
    for i in range(art_idx - 1, -1, -1):
        low = tokens[i].lower()
        if low in PREP_CASE:
            return (PREP_CASE[low], tokens[i], "prep", None)
        if low in VERB_FORMS:
            _inf, frame = VERB_FORMS[low]
            return (frame, _inf, "verb", i)
    return None


def check_sentence(sentence, index):
    """Return a list of findings; each is a dict with en/fa text.

    Only reports when the noun is in the curated list, the article kind is
    known, and the expected case is decidable from a verb frame or a
    case-governing preposition. Anything else is left alone.
    """
    tokens = tokenize(sentence)
    findings = []
    i = 0
    dat_akk_verbs_used = set()
    while i < len(tokens):
        low = tokens[i].lower()
        if low not in ARTICLE_FORMS:
            i += 1
            continue
        kind = article_kind(low)
        # collect following adjectives (lowercase words) then the noun;
        # stop at anything that cannot be an adjective (articles, verbs,
        # prepositions) so a later article is not swallowed
        j = i + 1
        adjectives = []
        while (j < len(tokens) and tokens[j][:1].islower()
               and tokens[j].lower() not in ARTICLE_FORMS
               and tokens[j].lower() not in VERB_FORMS
               and tokens[j].lower() not in PREP_CASE
               and j - i < 5):
            adjectives.append(tokens[j])
            j += 1
        if j >= len(tokens):
            i += 1
            continue
        noun_tok = tokens[j]
        entry = index.get(noun_tok.lower())
        if entry is None or entry["gender"] == "pl":
            i = j + 1
            continue
        anchor = find_case_anchor(tokens, i)
        if anchor is None:
            i = j + 1
            continue
        frame, anchor_word, anchor_kind, verb_idx = anchor
        g = entry["gender"]
        if frame == "dat_akk":
            # first noun phrase after the verb is dative (the person),
            # the following ones accusative (the thing)
            if verb_idx in dat_akk_verbs_used:
                case = "akk"
            else:
                case = "dat"
                dat_akk_verbs_used.add(verb_idx)
        else:
            case = frame
        if kind == "poss":
            stem = None
            for s in POSSESSIVE_STEMS:
                cand = possessive(s, g, case)
                if cand == low:
                    stem, kind = s, "poss"
                    break
            exp = possessive(stem, g, case) if stem else None
        else:
            exp = expected_article(kind, g, case)
        if exp and low != exp:
            findings.append({
                "type": "article",
                "message": f"«{tokens[i]} {noun_tok}» → «{exp} {noun_tok}»",
                "fa": (f"بعد از «{anchor_word}» حالت {CASE_DE[case]} "
                       f"({CASE_FA[case]}) می‌آید؛ «{entry['de']}» "
                       f"({entry['fa']}) {GENDER_FA[g]} است، پس حرف تعریف درست "
                       f"«{exp}» است نه «{tokens[i]}»."),
            })
        # N-declension: weak masculine nouns take -(e)n outside nominative
        if entry.get("weak") and entry["de"] != "Herz" and case != "nom":
            exp_noun = noun_form(entry, "sg", case)
            if noun_tok != exp_noun and noun_tok.lower() == entry["de"].lower():
                findings.append({
                    "type": "n-declension",
                    "message": f"«{noun_tok}» → «{exp_noun}»",
                    "fa": (f"«{entry['de']}» اسم ضعیف است (N-Deklination): در "
                           f"حالت {CASE_DE[case]} به شکل «{exp_noun}» می‌آید."),
                })
        if entry["de"] == "Herz" and case in ("dat", "gen"):
            exp_noun = noun_form(entry, "sg", case)
            if noun_tok != exp_noun and noun_tok.lower() == "herz":
                findings.append({
                    "type": "n-declension",
                    "message": f"«{noun_tok}» → «{exp_noun}»",
                    "fa": ("«Herz» اسم خنثیِ ضعیف است: "
                           f"در حالت {CASE_DE[case]} «{exp_noun}» می‌شود."),
                })
        # adjective ending after a definite/indefinite/negative article
        if adjectives and kind in ("def", "indef", "neg"):
            table = {"def": "weak", "indef": "mixed", "neg": "mixed"}[kind]
            kind_fa = {"def": "معین (der/die/das)",
                       "indef": "نامعین (ein/eine)",
                       "neg": "منفی (kein/keine)"}[kind]
            exp_end = ADJ_TABLES[table][g][case]
            actual = adjectives[-1]
            # strip to a plausible stem: compare endings only
            if not actual.lower().endswith(exp_end) or (
                    exp_end == "" and False):
                # rebuild the adjective with the right ending: crude stem =
                # word minus a known adjective ending
                stem = re.sub(r"(e|er|en|em|es)$", "", actual)
                fixed = stem + exp_end
                findings.append({
                    "type": "adjective",
                    "message": f"«{actual}» → «{fixed}»",
                    "fa": (f"بعد از حرف تعریف {kind_fa}، صفت در حالت "
                           f"{CASE_DE[case]} پسوند «-{exp_end}» می‌گیرد: "
                           f"«{fixed}»."),
                })
        i = j + 1
    return findings


def check_text(sentence, index, as_json=False):
    findings = check_sentence(sentence, index)
    if as_json:
        return json.dumps({"sentence": sentence, "findings": findings,
                           "count": len(findings)},
                          ensure_ascii=False, indent=2)
    if not findings:
        return ("✓ خطای قابل‌تشخیصی پیدا نشد. (یعنی جمله حتماً درست است؟ نه — "
                "فقط الگوهایی که ابزار بلد است چک کند سالم‌اند.)")
    lines = [f"⚠ {len(findings)} مورد:"]
    for f in findings:
        lines.append(f"• {f['message']}")
        lines.append(f"  {f['fa']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# quiz


def quiz_question(nouns, ask="article", rng=None):
    rng = rng or random
    pool = [n for n in nouns if n["gender"] in ("m", "f", "n")
            and (ask != "plural" or n["plural"])]
    entry = rng.choice(pool)
    g = entry["gender"]
    if ask == "article":
        prompt = (f"حرف تعریف معین «{entry['de']}» ({entry['fa']}) "
                  f"در حالت فاعلی چیست؟ (der/die/das)")
        answer = DEFINITE[g]["nom"]
    elif ask == "plural":
        prompt = (f"جمع «{entry['de']}» ({entry['fa']}) چیست؟ "
                  f"(با حرف تعریف، مثلاً die Männer)")
        answer = f"die {entry['plural']}"
    elif ask == "akkusativ":
        prompt = (f"«Ich sehe …»: «{entry['de']}» ({entry['fa']}) در حالت "
                  f"مفعولی مستقیم با حرف معین چه می‌شود؟ (مثلاً den Mann)")
        answer = f"{DEFINITE[g]['akk']} {noun_form(entry, 'sg', 'akk')}"
    else:
        raise ValueError(f"unknown quiz kind: {ask}")
    return {"prompt": prompt, "answer": answer, "noun": entry["de"]}


def check_quiz_answer(question, given):
    return given.strip().lower() == question["answer"].lower()


def run_quiz(nouns, n=5, ask="article"):
    score = 0
    for k in range(1, n + 1):
        q = quiz_question(nouns, ask)
        print(f"[{k}/{n}] {q['prompt']}")
        try:
            given = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if check_quiz_answer(q, given):
            print("✓ درست!")
            score += 1
        else:
            print(f"✗ جواب درست: {q['answer']}")
    print(f"\nنتیجه: {score} از {n}")


# ---------------------------------------------------------------------------
# anki export


def anki_tsv(nouns):
    lines = []
    for entry in nouns:
        g = entry["gender"]
        art = DEFINITE[g if g != "pl" else "pl"]["nom"]
        front = f"{entry['de']} ({entry['fa']})"
        if entry["plural"]:
            back = f"{art} {entry['de']} · die {entry['plural']}"
        else:
            back = f"{art} {entry['de']} · (بدون جمع)"
        lines.append(f"{front}\t{back}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI


def build_parser():
    p = argparse.ArgumentParser(
        prog="deutsch_fa.py",
        description="German declension for Persian speakers "
                    "(deterministic, zero-dependency).")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("decline", help="full declension table for a noun")
    d.add_argument("noun", help="German noun, with or without article")
    d.add_argument("--json", action="store_true")
    r = sub.add_parser("rules", help="gender-prediction rules")
    r.add_argument("word", nargs="?", help="optional noun to apply rules to")
    c = sub.add_parser("check", help="check articles/cases in a sentence")
    c.add_argument("sentence", help="German sentence in quotes")
    c.add_argument("--json", action="store_true")
    q = sub.add_parser("quiz", help="interactive drill")
    q.add_argument("--n", type=int, default=5)
    q.add_argument("--ask", default="article",
                   choices=["article", "plural", "akkusativ"])
    a = sub.add_parser("anki", help="export Anki TSV")
    a.add_argument("--out", default=None,
                   help="output file (default: stdout)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        nouns = load_nouns()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot load noun data: {exc}", file=sys.stderr)
        return 2
    index = noun_index(nouns)

    if args.cmd == "decline":
        entry = find_noun(args.noun, index)
        if entry is None:
            text, _code = gender_hint(args.noun, index)
            print(text)
            print("\n(این اسم در فهرست ۱۹۹تایی نسخه ۱ نیست؛ "
                  "حدس بالا را با دیکشنری چک کن.)")
            return 1
        if args.json:
            print(json.dumps(decline(entry), ensure_ascii=False, indent=2))
        else:
            print(decline_text(entry))
        return 0

    if args.cmd == "rules":
        print(rules_text(args.word, index))
        return 0

    if args.cmd == "check":
        out = check_text(args.sentence, index, as_json=args.json)
        print(out)
        return 1 if check_sentence(args.sentence, index) else 0

    if args.cmd == "quiz":
        run_quiz(nouns, n=args.n, ask=args.ask)
        return 0

    if args.cmd == "anki":
        tsv = anki_tsv(nouns)
        if args.out:
            Path(args.out).write_text(tsv, encoding="utf-8")
            print(f"wrote {len(nouns)} cards to {args.out}")
        else:
            sys.stdout.write(tsv)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
