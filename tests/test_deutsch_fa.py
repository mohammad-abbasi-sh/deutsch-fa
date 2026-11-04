#!/usr/bin/env python3
"""Tests for the deutsch-fa declension engine.

Run: python3 -m pytest tests/ -q   (from the project root)
or:   python3 tests/test_deutsch_fa.py  (stdlib fallback runner at bottom)
"""
import json
import random
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "deutsch-fa" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import deutsch_fa as df  # noqa: E402

NOUNS = df.load_nouns()
INDEX = df.noun_index(NOUNS)


class ArticleTables(unittest.TestCase):
    def test_definite_paradigm(self):
        self.assertEqual(df.DEFINITE["m"]["akk"], "den")
        self.assertEqual(df.DEFINITE["m"]["dat"], "dem")
        self.assertEqual(df.DEFINITE["m"]["gen"], "des")
        self.assertEqual(df.DEFINITE["f"]["dat"], "der")
        self.assertEqual(df.DEFINITE["f"]["gen"], "der")
        self.assertEqual(df.DEFINITE["n"]["nom"], "das")
        self.assertEqual(df.DEFINITE["pl"]["dat"], "den")
        self.assertEqual(df.DEFINITE["pl"]["gen"], "der")

    def test_indefinite_paradigm(self):
        self.assertEqual(df.INDEFINITE["m"]["akk"], "einen")
        self.assertEqual(df.INDEFINITE["m"]["dat"], "einem")
        self.assertEqual(df.INDEFINITE["m"]["gen"], "eines")
        self.assertEqual(df.INDEFINITE["f"]["nom"], "eine")
        self.assertEqual(df.INDEFINITE["f"]["dat"], "einer")
        self.assertEqual(df.INDEFINITE["n"]["akk"], "ein")

    def test_negative_paradigm(self):
        self.assertEqual(df.NEGATIVE["m"]["akk"], "keinen")
        self.assertEqual(df.NEGATIVE["pl"]["dat"], "keinen")
        self.assertEqual(df.NEGATIVE["pl"]["nom"], "keine")
        self.assertEqual(df.NEGATIVE["f"]["gen"], "keiner")

    def test_possessive(self):
        self.assertEqual(df.possessive("mein", "m", "akk"), "meinen")
        self.assertEqual(df.possessive("mein", "f", "dat"), "meiner")
        self.assertEqual(df.possessive("mein", "n", "nom"), "mein")
        self.assertEqual(df.possessive("mein", "pl", "dat"), "meinen")
        # euer drops the middle e before vowel endings
        self.assertEqual(df.possessive("euer", "m", "akk"), "euren")
        self.assertEqual(df.possessive("euer", "f", "nom"), "eure")
        self.assertEqual(df.possessive("euer", "m", "nom"), "euer")
        self.assertEqual(df.possessive("dein", "n", "gen"), "deines")


class AdjectiveEndings(unittest.TestCase):
    def test_weak(self):
        self.assertEqual(df.adjective_form("gut", "weak", "m", "nom"), "gute")
        self.assertEqual(df.adjective_form("gut", "weak", "m", "akk"), "guten")
        self.assertEqual(df.adjective_form("gut", "weak", "m", "dat"), "guten")
        self.assertEqual(df.adjective_form("gut", "weak", "f", "dat"), "guten")
        self.assertEqual(df.adjective_form("gut", "weak", "pl", "nom"), "guten")

    def test_strong(self):
        self.assertEqual(df.adjective_form("gut", "strong", "m", "nom"), "guter")
        self.assertEqual(df.adjective_form("gut", "strong", "m", "akk"), "guten")
        self.assertEqual(df.adjective_form("gut", "strong", "m", "dat"), "gutem")
        self.assertEqual(df.adjective_form("gut", "strong", "n", "nom"), "gutes")
        self.assertEqual(df.adjective_form("gut", "strong", "f", "gen"), "guter")
        self.assertEqual(df.adjective_form("gut", "strong", "pl", "dat"), "guten")

    def test_mixed(self):
        self.assertEqual(df.adjective_form("gut", "mixed", "m", "nom"), "guter")
        self.assertEqual(df.adjective_form("gut", "mixed", "m", "akk"), "guten")
        self.assertEqual(df.adjective_form("gut", "mixed", "n", "nom"), "gutes")
        self.assertEqual(df.adjective_form("gut", "mixed", "f", "akk"), "gute")
        self.assertEqual(df.adjective_form("gut", "mixed", "pl", "akk"), "guten")


class NounForms(unittest.TestCase):
    def test_genitive_es_monosyllabic(self):
        self.assertEqual(df.noun_form(INDEX["mann"], "sg", "gen"), "Mannes")
        self.assertEqual(df.noun_form(INDEX["kind"], "sg", "gen"), "Kindes")
        self.assertEqual(df.noun_form(INDEX["tag"], "sg", "gen"), "Tages")
        self.assertEqual(df.noun_form(INDEX["fuß"], "sg", "gen"), "Fußes")
        self.assertEqual(df.noun_form(INDEX["bus"], "sg", "gen"), "Busses")

    def test_genitive_s_polysyllabic(self):
        self.assertEqual(df.noun_form(INDEX["vater"], "sg", "gen"), "Vaters")
        self.assertEqual(df.noun_form(INDEX["abend"], "sg", "gen"), "Abends")
        self.assertEqual(df.noun_form(INDEX["mädchen"], "sg", "gen"), "Mädchens")
        self.assertEqual(df.noun_form(INDEX["computer"], "sg", "gen"), "Computers")

    def test_feminine_unchanged(self):
        self.assertEqual(df.noun_form(INDEX["frau"], "sg", "gen"), "Frau")
        self.assertEqual(df.noun_form(INDEX["frau"], "sg", "dat"), "Frau")

    def test_n_declension(self):
        self.assertEqual(df.noun_form(INDEX["student"], "sg", "akk"), "Studenten")
        self.assertEqual(df.noun_form(INDEX["student"], "sg", "dat"), "Studenten")
        self.assertEqual(df.noun_form(INDEX["student"], "sg", "gen"), "Studenten")
        self.assertEqual(df.noun_form(INDEX["name"], "sg", "dat"), "Namen")
        self.assertEqual(df.noun_form(INDEX["junge"], "sg", "akk"), "Jungen")
        self.assertEqual(df.noun_form(INDEX["herr"], "sg", "gen"), "Herrn")

    def test_herz_weak_neuter(self):
        self.assertEqual(df.noun_form(INDEX["herz"], "sg", "gen"), "Herzens")
        self.assertEqual(df.noun_form(INDEX["herz"], "sg", "dat"), "Herzen")
        self.assertEqual(df.noun_form(INDEX["herz"], "sg", "nom"), "Herz")

    def test_dative_plural_n(self):
        self.assertEqual(df.noun_form(INDEX["mann"], "pl", "dat"), "Männern")
        self.assertEqual(df.noun_form(INDEX["kind"], "pl", "dat"), "Kindern")
        self.assertEqual(df.noun_form(INDEX["haus"], "pl", "dat"), "Häusern")

    def test_dative_plural_no_double_n_or_s(self):
        self.assertEqual(df.noun_form(INDEX["frau"], "pl", "dat"), "Frauen")
        self.assertEqual(df.noun_form(INDEX["student"], "pl", "dat"), "Studenten")
        self.assertEqual(df.noun_form(INDEX["auto"], "pl", "dat"), "Autos")
        self.assertEqual(df.noun_form(INDEX["handy"], "pl", "dat"), "Handys")


class DataIntegrity(unittest.TestCase):
    def test_size(self):
        self.assertGreaterEqual(len(NOUNS), 150)

    def test_schema(self):
        seen = set()
        for n in NOUNS:
            self.assertIn(n["gender"], ("m", "f", "n", "pl"))
            self.assertTrue(n["de"][:1].isupper(), n["de"])
            self.assertTrue(n["fa"].strip(), n["de"])
            self.assertNotIn(n["de"].lower(), seen, f"duplicate {n['de']}")
            seen.add(n["de"].lower())
            self.assertTrue(n["plural"] is None or n["plural"].strip())

    def test_spot_genders(self):
        # the classic traps must be right
        self.assertEqual(INDEX["mädchen"]["gender"], "n")
        self.assertEqual(INDEX["junge"]["gender"], "m")
        self.assertEqual(INDEX["käse"]["gender"], "m")
        self.assertEqual(INDEX["butter"]["gender"], "f")
        self.assertEqual(INDEX["zucker"]["gender"], "m")


class DeclineOutput(unittest.TestCase):
    def test_mann(self):
        d = df.decline(INDEX["mann"])
        self.assertEqual(d["cases"]["sg"]["nom"], "der Mann")
        self.assertEqual(d["cases"]["sg"]["akk"], "den Mann")
        self.assertEqual(d["cases"]["sg"]["dat"], "dem Mann")
        self.assertEqual(d["cases"]["sg"]["gen"], "des Mannes")
        self.assertEqual(d["cases"]["pl"]["dat"], "den Männern")
        self.assertEqual(d["indefinite"]["akk"], "einen Mann")
        self.assertEqual(d["possessive_mein"]["dat"], "meinem Mann")

    def test_madchen_neuter(self):
        d = df.decline(INDEX["mädchen"])
        self.assertEqual(d["cases"]["sg"]["nom"], "das Mädchen")
        self.assertEqual(d["cases"]["sg"]["akk"], "das Mädchen")

    def test_frau(self):
        d = df.decline(INDEX["frau"])
        self.assertEqual(d["cases"]["sg"]["dat"], "der Frau")
        self.assertEqual(d["cases"]["sg"]["gen"], "der Frau")

    def test_eltern_plural_only(self):
        d = df.decline(INDEX["eltern"])
        self.assertNotIn("sg", d["cases"])
        self.assertEqual(d["cases"]["pl"]["dat"], "den Eltern")
        self.assertEqual(d["indefinite"], {})

    def test_uncountable(self):
        d = df.decline(INDEX["wasser"])
        self.assertNotIn("pl", d["cases"])
        self.assertEqual(d["cases"]["sg"]["akk"], "das Wasser")


class GenderRules(unittest.TestCase):
    def test_ung(self):
        g, rel, _exp = df.predict_gender("Wohnung")
        self.assertEqual(g, "f")

    def test_chen(self):
        g, _rel, _exp = df.predict_gender("Mädchen")
        self.assertEqual(g, "n")

    def test_day(self):
        g, _rel, _exp = df.predict_gender("Montag")
        self.assertEqual(g, "m")

    def test_kuchen_exception_reported(self):
        text, _code = df.gender_hint("Kuchen", INDEX)
        self.assertIn("استثنا", text)
        self.assertIn("مذکر", text)

    def test_in_list_agrees(self):
        text, code = df.gender_hint("Wohnung", INDEX)
        self.assertEqual(code, 0)
        self.assertIn("مؤنث", text)

    def test_unknown_word(self):
        text, code = df.gender_hint("Xyzabc", INDEX)
        self.assertEqual(code, 1)


class CheckSentence(unittest.TestCase):
    def check(self, s):
        return df.check_sentence(s, INDEX)

    def test_akkusativ_error(self):
        f = self.check("Ich sehe der Mann")
        self.assertEqual(len(f), 1)
        self.assertIn("den Mann", f[0]["message"])

    def test_dativ_error(self):
        f = self.check("Ich helfe den Mann")
        self.assertEqual(len(f), 1)
        self.assertIn("dem Mann", f[0]["message"])

    def test_geben_dat_akk(self):
        f = self.check("Ich gebe die Frau das Buch")
        self.assertEqual(len(f), 1)
        self.assertIn("der Frau", f[0]["message"])

    def test_geben_correct(self):
        self.assertEqual(self.check("Ich gebe der Frau das Buch"), [])

    def test_preposition_mit(self):
        f = self.check("Ich fahre mit der Auto")
        self.assertEqual(len(f), 1)
        self.assertIn("dem Auto", f[0]["message"])

    def test_preposition_fur(self):
        f = self.check("Das ist für der Mann")
        self.assertEqual(len(f), 1)
        self.assertIn("den Mann", f[0]["message"])

    def test_n_declension_noun(self):
        f = self.check("Ich sehe den Student")
        self.assertTrue(any(x["type"] == "n-declension" for x in f))
        self.assertTrue(any("Studenten" in x["message"] for x in f))

    def test_adjective_ending(self):
        f = self.check("Ich sehe den kleine Mann")
        self.assertTrue(any(x["type"] == "adjective" for x in f))
        self.assertTrue(any("kleinen" in x["message"] for x in f))

    def test_correct_sentence_clean(self):
        self.assertEqual(self.check("Ich sehe den kleinen Mann"), [])
        self.assertEqual(self.check("Das Mädchen spielt"), [])

    def test_unknown_noun_ignored(self):
        self.assertEqual(self.check("Ich sehe der Xyzq"), [])

    def test_no_anchor_ignored(self):
        # no verb/preposition with a known frame -> conservative silence
        self.assertEqual(self.check("Der Mann dort"), [])


class Quiz(unittest.TestCase):
    def test_question_shape(self):
        rng = random.Random(42)
        q = df.quiz_question(NOUNS, "article", rng)
        self.assertIn(q["answer"], ("der", "die", "das"))
        self.assertIn("prompt", q)

    def test_plural_question(self):
        rng = random.Random(7)
        q = df.quiz_question(NOUNS, "plural", rng)
        self.assertTrue(q["answer"].startswith("die "))

    def test_akkusativ_question(self):
        rng = random.Random(7)
        q = df.quiz_question(NOUNS, "akkusativ", rng)
        entry = INDEX[q["noun"].lower()]
        self.assertTrue(q["answer"].startswith(
            df.DEFINITE[entry["gender"]]["akk"] + " "))

    def test_check_answer(self):
        q = {"answer": "der"}
        self.assertTrue(df.check_quiz_answer(q, "der"))
        self.assertTrue(df.check_quiz_answer(q, " Der "))
        self.assertFalse(df.check_quiz_answer(q, "die"))


class Anki(unittest.TestCase):
    def test_tsv(self):
        tsv = df.anki_tsv(NOUNS)
        lines = tsv.strip().split("\n")
        self.assertEqual(len(lines), len(NOUNS))
        for line in lines:
            self.assertEqual(len(line.split("\t")), 2)
        self.assertIn("der Mann", tsv)
        self.assertIn("die Männer", tsv)


class CLI(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "deutsch_fa.py"),
                               *args], capture_output=True, text=True)

    def test_decline_exit0(self):
        p = self.run_cli("decline", "Mann")
        self.assertEqual(p.returncode, 0)
        self.assertIn("den Mann", p.stdout)

    def test_decline_unknown_exit1(self):
        p = self.run_cli("decline", "Xyzabc")
        self.assertEqual(p.returncode, 1)

    def test_decline_json(self):
        p = self.run_cli("decline", "Frau", "--json")
        self.assertEqual(p.returncode, 0)
        d = json.loads(p.stdout)
        self.assertEqual(d["cases"]["sg"]["dat"], "der Frau")

    def test_check_exit1_on_finding(self):
        p = self.run_cli("check", "Ich sehe der Mann")
        self.assertEqual(p.returncode, 1)
        self.assertIn("den Mann", p.stdout)

    def test_check_exit0_clean(self):
        p = self.run_cli("check", "Ich sehe den Mann")
        self.assertEqual(p.returncode, 0)

    def test_check_json(self):
        p = self.run_cli("check", "Ich sehe der Mann", "--json")
        d = json.loads(p.stdout)
        self.assertEqual(d["count"], 1)

    def test_rules(self):
        p = self.run_cli("rules")
        self.assertEqual(p.returncode, 0)
        self.assertIn("-ung", p.stdout)

    def test_anki_stdout(self):
        p = self.run_cli("anki")
        self.assertEqual(p.returncode, 0)
        self.assertIn("\t", p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
