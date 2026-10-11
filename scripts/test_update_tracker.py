"""Offline tests for update_tracker.build_payload. Run: python3 -m unittest discover scripts"""

import unittest
from datetime import datetime, timezone

import update_tracker as ut

NOW = datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)
DETAILS = {
    "name": "Test Regional",
    "players": 6,
    "phases": [
        {"phase": 1, "type": "SWISS", "rounds": 3, "mode": "BO3"},
        {"phase": 2, "type": "SINGLE_ELIMINATION", "rounds": 1, "mode": "BO3"},
    ],
}
TEAM = [
    {"id": "incineroar", "name": "Incineroar", "item": "Safety Goggles", "ability": "Intimidate",
     "attacks": ["Fake Out", "Flare Blitz", "Knock Off", "Parting Shot"], "tera": "Ghost"},
]


def row(pid, name, w, l, placing, drop=None, decklist=None):
    return {"player": pid, "name": name, "placing": placing, "drop": drop,
            "record": {"wins": w, "losses": l, "ties": 0}, "decklist": decklist}


class BuildPayloadTest(unittest.TestCase):
    def setUp(self):
        self.standings = [
            row("wolfe", "Wolfe Glick", 2, 0, 1, decklist=TEAM),
            row("a", "Alice", 1, 1, 2),
            row("b", "Bob", 1, 1, 3),
            row("c", "Cara", 1, 1, 4),
            row("d", "Dan", 1, 1, 5),
            row("e", "Eve", 0, 2, 6),
        ]
        self.pairings = [
            {"round": 1, "phase": 1, "table": 1, "player1": "wolfe", "player2": "a", "winner": "wolfe"},
            {"round": 1, "phase": 1, "table": 2, "player1": "b", "player2": "c", "winner": "b"},
            {"round": 1, "phase": 1, "table": 3, "player1": "d", "player2": "e", "winner": "d"},
            {"round": 2, "phase": 1, "table": 1, "player1": "wolfe", "player2": "b", "winner": "wolfe"},
            {"round": 2, "phase": 1, "table": 2, "player1": "a", "player2": "d", "winner": "a"},
            {"round": 2, "phase": 1, "table": 3, "player1": "c", "player2": "e", "winner": "c"},
            {"round": 3, "phase": 1, "table": 7, "player1": "c", "player2": "wolfe"},
        ]

    def build(self, previous=None, pairings=None):
        return ut.build_payload("t1", DETAILS, self.standings, pairings or self.pairings,
                                self.standings[0], previous, NOW, "https://twitch.tv/x")

    def test_mid_swiss(self):
        p = self.build()
        self.assertEqual(p["status"], "Round 3 Swiss")
        self.assertEqual(p["record"], {"w": 2, "l": 0, "t": 0})
        self.assertEqual(p["table"], 7)
        self.assertTrue(p["currentMatchPending"])
        self.assertEqual([m["result"] for m in p["matches"]], ["W", "W", None])
        self.assertEqual(p["matches"][2]["opponent"], "Cara")
        self.assertEqual(p["opw"], 50.0)  # Alice 1-1, Bob 1-1
        self.assertEqual(p["topCutSize"], 2)
        self.assertEqual(p["team"][0]["moves"][0], "Fake Out")
        self.assertIsNone(p["roundStartedAt"])  # first observation: unknown start

    def test_clinch_and_elimination_math(self):
        # 2-0 with one round left in a top 2: four 1-1 players can each reach 6 points, so not clinched.
        self.assertEqual(self.build()["topCutStatus"], "alive")
        me = self.standings[0]
        self.assertEqual(ut.top_cut_math(me, self.standings, 1, 3, 4), "alive")
        self.assertEqual(ut.top_cut_math(self.standings[5], self.standings, 1, 3, 1), "eliminated")
        solo = [me, row("z", "Zed", 0, 2, 2)]
        self.assertEqual(ut.top_cut_math(me, solo, 1, 3, 1), "clinched")

    def test_round_timer_carries_over(self):
        prev = self.build()
        prev["roundKey"] = "1-2"
        stamped = self.build(previous=prev)
        self.assertEqual(stamped["roundStartedAt"], "2026-10-11T18:00:00Z")
        again = self.build(previous=stamped)
        self.assertEqual(again["roundStartedAt"], "2026-10-11T18:00:00Z")

    def test_top_cut_and_finish(self):
        pairings = [dict(p) for p in self.pairings]
        pairings[-1]["winner"] = "wolfe"
        pairings.append({"round": 4, "phase": 2, "player1": "wolfe", "player2": "a"})
        p = self.build(pairings=pairings)
        self.assertEqual(p["phase"], "topcut")
        self.assertEqual(p["status"], "Finals")
        self.assertEqual(p["topCutStatus"], "clinched")
        pairings[-1]["winner"] = "wolfe"
        done = self.build(pairings=pairings)
        self.assertEqual(done["phase"], "finished")
        self.assertEqual(done["status"], "Final standing #1")

    def test_bye(self):
        pairings = self.pairings[:1] + [{"round": 2, "phase": 1, "player1": "wolfe", "player2": ""}]
        p = self.build(pairings=pairings)
        self.assertEqual(p["matches"][1]["result"], "BYE")


if __name__ == "__main__":
    unittest.main()
