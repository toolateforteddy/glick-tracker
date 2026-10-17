"""Offline tests for update_tracker.build_payload. Run: python3 -m unittest discover scripts"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

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
        self.assertNotIn("table", p)
        self.assertTrue(all("table" not in m for m in p["matches"]))
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


class IdleBackoffTest(unittest.TestCase):
    ENV = {"GIST_ID": "g", "GH_PAT": "t", "RK9_TOURNAMENT_ID": "", "TOURNAMENT_ID": ""}

    def run_main(self, previous, discovered=None):
        fixed = datetime(2026, 10, 11, 18, 0, 30, tzinfo=timezone.utc)
        with mock.patch.dict("os.environ", self.ENV), \
             mock.patch.object(ut, "datetime", wraps=datetime) as dt, \
             mock.patch.object(ut, "read_previous_payload", return_value=previous), \
             mock.patch.object(ut.rk9, "discover_vg_tournament", return_value=discovered) as disc, \
             mock.patch.object(ut, "discover_tournament", return_value=(None, [], None)), \
             mock.patch.object(ut, "write_payload") as write:
            dt.now.return_value = fixed
            self.assertEqual(ut.main(), 0)
        return disc, write

    def test_not_found_backs_off_an_hour(self):
        disc, write = self.run_main({"tournament": "Old", "record": {"w": 1, "l": 0}})
        disc.assert_called_once()
        written = write.call_args.args[2]
        self.assertEqual(written["snoozeUntil"], "2026-10-11T19:00:30Z")
        self.assertEqual(written["tournament"], "Old")  # last payload kept for the page
        self.assertEqual(written["idleSince"], "2026-10-11T18:00:30Z")

    def test_gives_up_for_the_weekend_after_six_hours(self):
        # 18:00:30 Sunday; idle since 12:00 -> stop until Monday 06:00 UTC.
        _, write = self.run_main({"idleSince": "2026-10-11T12:00:00Z", "snoozeUntil": "2026-10-11T18:00:00Z"})
        written = write.call_args.args[2]
        self.assertEqual(written["snoozeUntil"], "2026-10-12T06:00:00Z")
        self.assertEqual(written["idleSince"], "2026-10-11T12:00:00Z")

    def test_weekend_over(self):
        sat = datetime(2026, 10, 10, 13, 0, tzinfo=timezone.utc)
        early_mon = datetime(2026, 10, 12, 2, 0, tzinfo=timezone.utc)
        self.assertEqual(ut.weekend_over(sat), datetime(2026, 10, 12, 6, 0, tzinfo=timezone.utc))
        self.assertEqual(ut.weekend_over(early_mon), datetime(2026, 10, 12, 6, 0, tzinfo=timezone.utc))

    def test_weekday_give_up_wakes_before_the_next_weekend(self):
        # Louisville finished on a Monday afternoon; the old rule slept through the Nice weekend.
        mon = datetime(2026, 10, 12, 12, 46, tzinfo=timezone.utc)
        thu = datetime(2026, 10, 15, 23, 0, tzinfo=timezone.utc)
        self.assertEqual(ut.weekend_over(mon), datetime(2026, 10, 16, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(ut.weekend_over(thu), datetime(2026, 10, 16, 0, 0, tzinfo=timezone.utc))

    def test_checks_afresh_after_a_give_up_snooze_ends(self):
        # Gave up on a weekday until Friday 00:00; at that's wake-up start hourly checks again.
        previous = {"idleSince": "2026-10-11T12:00:00Z", "snoozeUntil": "2026-10-16T00:00:00Z"}
        fri = datetime(2026, 10, 16, 0, 0, 30, tzinfo=timezone.utc)
        idle = ut.idle_snooze(previous, fri)
        self.assertEqual(idle, {"snoozeUntil": "2026-10-16T01:00:30Z", "idleSince": "2026-10-16T00:00:30Z"})

    def test_wolfe_done(self):
        self.assertTrue(ut.wolfe_done({"phase": "finished"}))
        self.assertTrue(ut.wolfe_done({"phase": "swiss", "status": "Dropped after Round 6"}))
        lost = {"phase": "topcut", "matches": [{"phase": "swiss", "result": "W"}, {"phase": "topcut", "result": "L"}]}
        self.assertTrue(ut.wolfe_done(lost))
        won = {"phase": "topcut", "matches": [{"phase": "topcut", "result": "W"}]}
        self.assertFalse(ut.wolfe_done(won))
        self.assertFalse(ut.wolfe_done({"phase": "swiss", "status": "Round 10 Swiss", "matches": []}))

    def test_snoozed_run_makes_no_requests(self):
        disc, write = self.run_main({"snoozeUntil": "2026-10-11T18:30:00Z"})
        disc.assert_not_called()
        write.assert_not_called()


class LoopTest(unittest.TestCase):
    def run_loop(self, results, minutes="60"):
        clock = [datetime(2026, 10, 11, 18, 0, tzinfo=timezone.utc)]

        def sleep(seconds):
            clock[0] += timedelta(seconds=seconds)

        with mock.patch.dict("os.environ", {"LOOP_MINUTES": minutes}), \
             mock.patch.object(ut, "datetime", wraps=datetime) as dt, \
             mock.patch.object(ut, "sync_once", side_effect=results) as once, \
             mock.patch.object(ut.time, "sleep", side_effect=sleep) as slept:
            dt.now.side_effect = lambda tz=None: clock[0]
            self.assertEqual(ut.main(), 0)
        return once, slept

    def test_checks_every_ten_minutes_until_the_run_ends(self):
        once, slept = self.run_loop([(0, None)] * 6)
        self.assertEqual(once.call_count, 6)
        self.assertEqual([c.args[0] for c in slept.call_args_list], [600.0] * 5)

    def test_sleeps_through_a_snooze(self):
        once, slept = self.run_loop([(0, "2026-10-11T18:40:00Z"), (0, None), (0, None)])
        self.assertEqual(slept.call_args_list[0].args[0], 2400.0)
        self.assertEqual(once.call_count, 3)

    def test_stops_when_snoozed_past_the_end(self):
        once, slept = self.run_loop([(0, "2026-10-12T06:00:00Z")])
        once.assert_called_once()
        slept.assert_not_called()

    def test_a_failed_pass_does_not_end_the_loop(self):
        once, _ = self.run_loop([RuntimeError("boom")] + [(0, None)] * 5)
        self.assertEqual(once.call_count, 6)


if __name__ == "__main__":
    unittest.main()
