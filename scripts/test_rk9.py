"""Offline tests for the RK9 scraper. Run: python3 -m unittest discover scripts"""

import unittest
from datetime import date, datetime, timezone
from unittest import mock

import rk9
import update_tracker as ut

NOW = datetime(2026, 10, 11, 15, 0, tzinfo=timezone.utc)
rk9.REQUEST_GAP_SECONDS = 0


def player(cls, name, rec):
    return f'<div class="col-5 {cls}"><span class="name">{name}</span><br>({rec}) pts</div>'


def match(table, p1, p2, s1="", s2=""):
    right = player(f"player2 {s2}", *p2) if p2 else '<div class="col-5 player2"></div>'
    return (f'<div class="row row-cols-3 match no-gutter complete">{player(f"player1 {s1}", *p1)}'
            f'<div class="col-2"><span class="tablenumber">{table}</span></div>{right}</div>')


def page(rounds, pod=2):
    tabs = "".join(f'<a class="nav-link" href="#P{pod}R{r}">Round {r}</a>' for r in rounds)
    latest = max(rounds)
    body = "".join(rounds[latest])
    return f'<html><body><ul>{tabs}</ul><div class="tab-pane" id="P{pod}R{latest}">{body}</div></body></html>'


R1 = [match(1, ("Wolfe Glick [US]", "0-0-0"), ("Alice A", "0-0-0"), "winner", "loser"),
      match(2, ("Bob B", "0-0-0"), ("Cara C", "0-0-0"), "winner", "loser")]
R2 = [match(5, ("Bob B", "1-0-0"), ("Wolfe Glick [US]", "1-0-0"), "loser", "winner"),
      match(6, ("Alice A", "0-1-0"), ("Cara C", "0-1-0"), "winner", "loser")]
R3 = [match(9, ("Wolfe Glick [US]", "2-0-0"), ("Alice A", "1-1-0")),
      match(10, ("Bob B", "1-1-0"), ("Cara C", "0-2-0"), "tie", "tie")]


class ParseTest(unittest.TestCase):
    def test_parse_page(self):
        by_round, linked = rk9.parse_pairings_page(page({1: R1, 2: R2, 3: R3}), 2)
        self.assertEqual(linked, {1, 2, 3})
        self.assertEqual(list(by_round), [3])
        m = by_round[3][0]
        self.assertEqual(m["table"], 9)
        self.assertEqual(m["p1"]["id"], "wolfeglick")
        self.assertEqual(m["p2"]["record"], {"wins": 1, "losses": 1, "ties": 0})
        self.assertIsNone(m["p1"]["status"])

    def test_live_markup(self):
        # Trimmed from the live Louisville 2027 page (2026-10-11): a lazy-loaded pane holding only
        # the header row, and the current round with records in data-* attributes and a bye.
        html = (
            '<h4 class="mb-0">2027 Louisville Pokémon VGC Regional Championships</h4>'
            '<div>Last uploaded: 14 seconds ago — 1099 players</div>'
            '<a class="nav-link" href="#P2R9-tab">Round 9</a><a class="nav-link" href="#P2R10-tab">Round 10</a>'
            '<div class="current-tables tab-pane" id="P2R9"><div class="row match no-gutter">'
            '<div class="col-5 player player1"><strong>Player 1</strong></div><div class="col-2"><strong>Table #</strong></div>'
            '<div class="col-5 player player2"><strong>Player 2</strong></div></div>'
            '<div hx-get="/pairings/LO002?pod=2&rnd=9" class="text-center"></div></div>'
            '<div class="current-tables tab-pane" id="P2R10">'
            '<div class="row row-cols-3 match no-gutter complete"><div class="col-5 player player1 winner outcome">'
            '<span class="name">Wolfe<br> Glick [US]<br></span><span class="record" data-wins="7" data-losses="3" '
            'data-ties="0" data-points="21"></span><br></div><div class="col-2"></div><div class="col-5 player player2"></div></div>'
            '<div class="row row-cols-3 match no-gutter complete"><div class="col-5 player player1 loser">'
            '<span class="name">Carson<br> Confer [US]<br></span><span class="record" data-wins="9" data-losses="1" data-ties="0"></span></div>'
            '<div class="col-2"> Table<br><span class="tablenumber "> 379 </span></div>'
            '<div class="col-5 player player2 winner outcome result"><span class="name">Paul<br> Chua [US]<br></span>'
            '<span class="record" data-wins="10" data-losses="0" data-ties="0"></span></div></div></div>')
        by_round, linked = rk9.parse_pairings_page(html, 2)
        self.assertEqual(linked, {9, 10})
        self.assertEqual(list(by_round), [10])  # the header-only pane is not a match
        bye, m = by_round[10]
        self.assertEqual(bye["p1"], {"name": "Wolfe Glick", "id": "wolfeglick", "status": "winner",
                                     "record": {"wins": 7, "losses": 3, "ties": 0}})
        self.assertIsNone(bye["p2"])
        self.assertIsNone(bye["table"])
        self.assertEqual((m["table"], m["p2"]["record"]["wins"]), (379, 10))
        self.assertEqual(rk9.parse_page_info(html),
                         {"name": "2027 Louisville Pokémon VGC Regional Championships", "players": 1099})

    def test_fragment_markup(self):
        # Per-round fragments (?pod=2&rnd=9) print the record as text instead.
        html = ('<div class="row row-cols-3 match no-gutter complete"><div class="col-5 player player1 loser">'
                '<span class="name">Wolfe<br> Glick [US]<br></span> (6-3-0) 18 pts <br></div>'
                '<div class="col-2"> Table<br><span class="tablenumber "> 437 </span><br></div>'
                '<div class="col-5 player player2 winner"><span class="name">Kimari<br> Gammage [US]<br></span>'
                ' (7-2-0) 21 pts <br></div></div>')
        with mock.patch.object(rk9, "fetch", return_value=html):
            (m,) = rk9.fetch_round("LO002", 2, 9)
        self.assertEqual((m["table"], m["p1"]["id"], m["p1"]["status"]), (437, "wolfeglick", "loser"))
        self.assertEqual(m["p1"]["record"], {"wins": 6, "losses": 3, "ties": 0})

    def test_date_ranges(self):
        self.assertEqual(rk9.parse_date_range("October 9-11, 2026: 2027 Louisville"),
                         (date(2026, 10, 9), date(2026, 10, 11)))
        self.assertEqual(rk9.parse_date_range("October 31-November 1, 2026"),
                         (date(2026, 10, 31), date(2026, 11, 1)))

    def test_discover(self):
        html = ('<table><tr><td>October 9-11, 2026</td><td><a href="/event/pokemon-louisville-2027">'
                '2027 Louisville Pokémon Regional Championships</a></td><td>'
                '<a href="/tournament/LO001-x">TCG</a> <a href="/tournament/LO002-drfp6esCSpyU3s">VG</a></td></tr></table>')
        with mock.patch.object(rk9, "fetch", return_value=html):
            self.assertEqual(rk9.discover_vg_tournament(date(2026, 10, 11)),
                             ("LO002-drfp6esCSpyU3s", "2027 Louisville Pokémon Regional Championships"))
            self.assertIsNone(rk9.discover_vg_tournament(date(2026, 10, 13)))


class RunTest(unittest.TestCase):
    def fake_fetch(self, path):
        if "rnd=" in path:
            rnd = int(path.rsplit("=", 1)[1])
            return "".join({1: R1, 2: R2, 3: R3}[rnd])
        return page({1: R1, 2: R2, 3: R3})

    def run_once(self, previous=None):
        with mock.patch.object(rk9, "fetch", side_effect=self.fake_fetch) as f, \
             mock.patch.dict("os.environ", {"RK9_SWISS_ROUNDS": "5", "RK9_TOP_CUT": "2"}):
            payload = ut.run_rk9("LO002", "Louisville", "Wolfe Glick", previous, NOW, "s")
        return payload, [c.args[0] for c in f.call_args_list]

    def test_first_run(self):
        p, calls = self.run_once()
        self.assertEqual(calls, ["/pairings/LO002", "/pairings/LO002?pod=2&rnd=1", "/pairings/LO002?pod=2&rnd=2"])
        self.assertEqual(p["status"], "Round 3 Swiss")
        self.assertEqual(p["record"], {"w": 2, "l": 0, "t": 0})
        self.assertEqual(p["table"], 9)
        self.assertEqual([m["result"] for m in p["matches"]], ["W", "W", None])
        self.assertEqual(p["matches"][1]["opponent"], "Bob B")
        self.assertEqual(p["standing"], 1)
        # Opponents: Alice 1-1 (entering R3) and Bob 1-1-1 after his R3 tie.
        self.assertEqual(p["opw"], round(100 * (0.5 + 1 / 3) / 2, 2))
        self.assertEqual(p["snoozeUntil"], "2026-10-11T15:40:00Z")
        self.assertEqual(p["source"], "rk9")

    def test_cached_rounds_not_refetched_and_snooze_clears(self):
        first, _ = self.run_once()
        second, calls = self.run_once(previous=first)
        self.assertEqual(calls, ["/pairings/LO002"])
        self.assertEqual(second["record"], {"w": 2, "l": 0, "t": 0})
        self.assertEqual(second["opw"], first["opw"])
        self.assertIsNone(second["snoozeUntil"])

    def test_snoozed(self):
        prev = {"source": "rk9", "snoozeUntil": "2026-10-11T15:30:00Z"}
        self.assertTrue(ut.snoozed(prev, NOW))
        self.assertFalse(ut.snoozed(prev, datetime(2026, 10, 11, 15, 31, tzinfo=timezone.utc)))

    def test_records_that_include_result(self):
        # Same event, but RK9 showing post-round records: detection must not double count.
        global R2
        saved = R2
        R2 = [match(5, ("Bob B", "1-1-0"), ("Wolfe Glick [US]", "2-0-0"), "loser", "winner"),
              match(6, ("Alice A", "1-1-0"), ("Cara C", "0-2-0"), "winner", "loser")]
        try:
            with mock.patch.object(rk9, "fetch", side_effect=lambda path: page({1: R1, 2: R2})
                                   if "rnd" not in path else "".join(R1)):
                p = ut.run_rk9("LO002", "L", "Wolfe Glick", None, NOW, "s")
        finally:
            R2 = saved
        self.assertEqual(p["record"], {"w": 2, "l": 0, "t": 0})


class PasteTest(unittest.TestCase):
    def test_parse_paste(self):
        team = ut.parse_paste("""Flutter Mane @ Booster Energy
Ability: Protosynthesis
Level: 50
Tera Type: Fairy
Timid Nature
- Moonblast
- Shadow Ball

Smacky (Incineroar) (M) @ Safety Goggles
Ability: Intimidate
- Fake Out
""")
        self.assertEqual(team[0]["species"], "Flutter Mane")
        self.assertEqual(team[0]["tera"], "Fairy")
        self.assertEqual(team[0]["moves"], ["Moonblast", "Shadow Ball"])
        self.assertEqual(team[1]["species"], "Incineroar")
        self.assertEqual(team[1]["item"], "Safety Goggles")


if __name__ == "__main__":
    unittest.main()
