import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

import rk9_history as h  # noqa: E402

EVENTS_HTML = """<table><tr>
  <td>September 18-20, 2026</td>
  <td><img src="/static/images/logo.png"></td>
  <td><a href="/event/pokemon-baltimore-2027">2027 Baltimore Pokémon Regional Championships</a><br><i></i></td>
  <td>Baltimore, US</td>
  <td><a href="/tournament/BA003">GO</a> <a href="/tournament/BA001">TCG</a>
      <a href="/tournament/BA002-JL3KVbvivVKNAc">VG</a></td>
</tr><tr>
  <td>June 27, 2026</td><td></td><td>Professor Cup</td><td>Online</td><td></td>
</tr></table>"""

ROSTER_HTML = """<table><tr>
  <td>3....9</td><td>Wolfe</td><td> Glick </td><td>US</td><td>Masters</td><td>Wolfey</td>
  <td class=text-center><a href="/teamlist/public/BA002/abc"><strong>View</strong></a></td>
  <td class="text-center">15</th>
</tr><tr>
  <td>1....2</td><td>Wolfe</td><td>Glick</td><td>US</td><td>Juniors</td><td>x</td><td></td><td>3</td>
</tr></table>"""

TEAMLIST_HTML = """<div id="lang-EN">
  <div class="pokemon p-3"><img src="x.png"> Indeedee [Female] &nbsp; <b>EN</b><br>
    <b>Ability:</b> Psychic Surge &nbsp;&nbsp; <b>Held Item:</b> Colbur Berry<br>
    <b>Stat Alignment:</b> Calm<br>
    <h5><span class="badge">Follow Me</span><span class="badge">Psychic</span>
    <span class="badge">Helping Hand</span><span class="badge">Protect</span></h5></div>
</div>
<div id="lang-FR"><div class="pokemon"> Wimessir [Femelle] <b>Ability:</b> Créa-Psy</div></div>"""


def match(p1, p2, s1, s2):
    def player(name, status):
        return {"name": name, "id": h.rk9.normalize_name(name), "record": None, "status": status}
    return {"table": 1, "p1": player(p1, s1) if p1 else None, "p2": player(p2, s2) if p2 else None}


class ParseTests(unittest.TestCase):
    def test_events_finds_vg_id_name_and_location(self):
        [ev] = h.parse_events(EVENTS_HTML)
        self.assertEqual(ev["id"], "BA002-JL3KVbvivVKNAc")
        self.assertEqual(ev["name"], "2027 Baltimore Pokémon Regional Championships")
        self.assertEqual(ev["location"], "Baltimore, US")
        self.assertTrue(h.wanted_by_default(ev))

    def test_roster_reads_masters_row(self):
        self.assertEqual(h.parse_roster(ROSTER_HTML, "Wolfe Glick"),
                         {"standing": 15, "teamlist": "/teamlist/public/BA002/abc"})
        self.assertIsNone(h.parse_roster(ROSTER_HTML, "Someone Else"))

    def test_teamlist_reads_english_block(self):
        [mon] = h.parse_teamlist(TEAMLIST_HTML)
        self.assertEqual(mon["species"], "Indeedee-F")
        self.assertEqual(mon["ability"], "Psychic Surge")
        self.assertEqual(mon["item"], "Colbur Berry")
        self.assertEqual(mon["moves"], ["Follow Me", "Psychic", "Helping Hand", "Protect"])

    def test_species_forms(self):
        self.assertEqual(h.species_name("Zoroark [Hisuian Form]"), "Zoroark-Hisui")
        self.assertEqual(h.species_name("Landorus [Incarnate Forme]"), "Landorus")
        self.assertEqual(h.species_name("Ogerpon [Wellspring Mask]"), "Ogerpon-Wellspring")
        self.assertEqual(h.species_name("Urshifu [Rapid Strike Style]"), "Urshifu-Rapid-Strike")


class RoundTests(unittest.TestCase):
    def run_rounds(self, rounds):
        def fake_fetch_round(_tid, _pod, rnd):
            return rounds.get(rnd, [])
        orig_fetch, orig_page = h.rk9.fetch_round, h.rk9.parse_pairings_page
        h.rk9.fetch_round = fake_fetch_round
        h.rk9.parse_pairings_page = lambda _html, _pod: ({}, set(rounds))
        try:
            return h.scrape_rounds("T", "", "wolfeglick", lambda: None)
        finally:
            h.rk9.fetch_round, h.rk9.parse_pairings_page = orig_fetch, orig_page

    def test_bye_round_is_swiss_and_bracket_is_labelled(self):
        filler = [match("A", "B", "winner", "loser")] * 20
        rounds = {
            1: [match("Wolfe Glick", "X", "winner", "loser")] + filler,
            2: [match("Y", "Wolfe Glick", "winner", "loser")] + filler,
            # Last Swiss round: leaders get byes, so it is small but not the bracket.
            3: [match("Wolfe Glick", None, "winner", None)] + [match("A", "B", "winner", "loser")] * 4,
            4: [match("Wolfe Glick", "Z", "winner", "loser")] + [match("A", "B", "winner", "loser")] * 3,
            5: [match("Wolfe Glick", "Q", "loser", "winner"), match("A", "B", "winner", "loser")],
            6: [match("Q", "B", "winner", "loser")],
        }
        rows, swiss, cut = self.run_rounds(rounds)
        self.assertEqual((swiss, cut), (3, 8))
        self.assertEqual([(r["label"], r["result"]) for r in rows],
                         [("R1", "W"), ("R2", "L"), ("R3", "BYE"), ("Top 8", "W"), ("Top 4", "L")])

    def test_stops_when_wolfe_is_gone(self):
        rounds = {1: [match("Wolfe Glick", "X", "loser", "winner")] * 20,
                  2: [match("A", "B", "winner", "loser")] * 20}
        rows, swiss, cut = self.run_rounds(rounds)
        self.assertEqual(len(rows), 1)
        self.assertEqual((swiss, cut), (None, None))


if __name__ == "__main__":
    unittest.main()
