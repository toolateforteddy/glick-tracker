"""RK9 (rk9.gg) support for update_tracker: Play! Pokémon Regionals, ICs and Worlds.

RK9 has no API, so this reads its HTML. To keep load light it fetches one pairings page per
sync and only asks for older rounds it hasn't seen yet; finished rounds are cached in the gist.

The RK9 data is converted into the same shapes the Limitless API returns (details, standings,
pairings) so update_tracker.build_payload can do the rest.
"""

from __future__ import annotations

import math
import re
import time
import urllib.error
import urllib.request
from datetime import date
from html.parser import HTMLParser
from typing import Callable

RK9 = "https://rk9.gg"
# Identify ourselves clearly so site owners know who is polling and how to ask us to stop.
USER_AGENT = (
    "glick-tracker/1.0 (non-commercial fan tracker for one player; about one page per round, "
    "backs off when idle; source: https://github.com/toolateforteddy/glick-tracker; "
    "to ask us to stop: https://github.com/toolateforteddy/glick-tracker/issues)"
)
MASTERS_POD = 2
MAX_ROUNDS = 25
REQUEST_GAP_SECONDS = 1.5

RECORD_RE = re.compile(r"\((\d+)\s*-\s*(\d+)\s*-\s*(\d+)\)")
ROUND_REF_RE = re.compile(r"P(\d+)R(\d+)$")
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}


# ----------------------------------------------------------------------- Minimal DOM


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")
    children: list[Node]

    def __init__(self, tag: str, attrs: dict[str, str], parent: Node | None):
        self.tag, self.attrs, self.children, self.parent = tag, attrs, [], parent

    @property
    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())

    def text(self) -> str:
        return " ".join(
            " ".join(c.split()) if isinstance(c, str) else c.text() for c in self.children
        ).strip()

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find_all(self, pred: Callable[[Node], bool]) -> list[Node]:
        return [n for n in self.iter() if pred(n)]

    def find(self, pred: Callable[[Node], bool]) -> Node | None:
        return next((n for n in self.iter() if pred(n)), None)


VOID = {"br", "img", "input", "meta", "link", "hr", "source", "area", "base", "col", "wbr"}


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: v or "" for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: v or "" for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.children.append(data)


def parse_html(html: str) -> Node:
    b = _Builder()
    b.feed(html)
    return b.root


# --------------------------------------------------------------------------- HTTP


def fetch(path: str) -> str:
    req = urllib.request.Request(f"{RK9}{path}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as err:
        raise RuntimeError(f"GET {RK9}{path} -> HTTP {err.code}") from err


# ------------------------------------------------------------------------ Parsing


def normalize_name(name: str | None) -> str:
    """'Wolfe Glick [US]' -> 'wolfeglick'."""
    name = re.sub(r"\[[^\]]*\]", "", name or "")
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _parse_player(node: Node | None) -> dict | None:
    if node is None:
        return None
    # Each real player cell has a <span class="name">; the "Player 1"/"Player 2" header row
    # (also a .match row) and empty bye cells don't.
    name_node = node.find(lambda n: "name" in n.classes)
    if name_node is None:
        return None
    name = " ".join(re.sub(r"\[[^\]]*\]", "", name_node.text()).split())
    if not name:
        return None
    # The live round carries the record as data-* attributes on <span class="record">; the
    # per-round fragments print it as text, "(6-3-0) 18 pts".
    record = None
    rec_node = node.find(lambda n: "record" in n.classes and "data-wins" in n.attrs)
    if rec_node is not None:
        try:
            record = {k: int(rec_node.attrs.get(f"data-{k}") or 0) for k in ("wins", "losses", "ties")}
        except ValueError:
            record = None
    if record is None and (m := RECORD_RE.search(node.text())):
        record = {"wins": int(m[1]), "losses": int(m[2]), "ties": int(m[3])}
    classes = node.classes
    status = next((s for s in ("winner", "loser", "tie", "dropped") if s in classes), None)
    return {"name": name, "id": normalize_name(name), "record": record, "status": status}


def parse_matches(container: Node) -> list[dict]:
    matches = []
    for m in container.find_all(lambda n: "match" in n.classes):
        p1 = _parse_player(m.find(lambda n: "player1" in n.classes))
        p2 = _parse_player(m.find(lambda n: "player2" in n.classes))
        if not p1 and not p2:
            continue
        table_node = m.find(lambda n: "tablenumber" in n.classes or "table-number" in n.classes)
        table_text = table_node.text() if table_node else ""
        if not table_node:
            tm = re.search(r"Table\s*(\d+)", m.text())
            table_text = tm[1] if tm else ""
        digits = re.search(r"\d+", table_text)
        matches.append({"table": int(digits[0]) if digits else None, "p1": p1, "p2": p2})
    return matches


def parse_pairings_page(html: str, pod: int) -> tuple[dict[int, list[dict]], set[int]]:
    """Return ({round: matches} for rounds whose content is on the page, all round numbers linked)."""
    root = parse_html(html)
    rounds_seen: set[int] = set()
    for n in root.iter():
        ref = (n.attrs.get("href") or n.attrs.get("data-bs-target") or n.attrs.get("id") or "").lstrip("#")
        if (m := ROUND_REF_RE.search(ref)) and int(m[1]) == pod:
            rounds_seen.add(int(m[2]))

    by_round: dict[int, list[dict]] = {}
    for pane in root.find_all(lambda n: bool(ROUND_REF_RE.fullmatch(n.attrs.get("id", "")))):
        m = ROUND_REF_RE.fullmatch(pane.attrs["id"])
        if m and int(m[1]) == pod and (found := parse_matches(pane)):
            by_round[int(m[2])] = found
    return by_round, rounds_seen


def fetch_round(tournament_id: str, pod: int, rnd: int) -> list[dict]:
    html = fetch(f"/pairings/{tournament_id}?pod={pod}&rnd={rnd}")
    by_round, _ = parse_pairings_page(html, pod)
    if rnd in by_round:
        return by_round[rnd]
    # The per-round endpoint returns a bare fragment without the P{pod}R{rnd} wrapper.
    return parse_matches(parse_html(html)) if not by_round else []


# ---------------------------------------------------------------------- Discovery


def parse_date_range(text: str) -> tuple[date, date] | None:
    """'October 9-11, 2026' or 'October 31-November 1, 2026' -> (start, end)."""
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2})\s*[-–]\s*(?:([A-Za-z]+)\s+)?(\d{1,2}),\s*(\d{4})", text)
    if not m:
        return None
    m1, d1, m2, d2, year = m[1].lower(), int(m[2]), (m[3] or m[1]).lower(), int(m[4]), int(m[5])
    if m1 not in MONTHS or m2 not in MONTHS:
        return None
    start, end = date(year, MONTHS[m1], d1), date(year, MONTHS[m2], d2)
    return (start, end) if start <= end else (start, date(year + 1, MONTHS[m2], d2))


def discover_vg_tournament(today: date) -> tuple[str, str] | None:
    """Find the VG tournament of a Pokémon event running today. Returns (tournament id, event name)."""
    root = parse_html(fetch("/events/pokemon"))
    for row in root.find_all(lambda n: n.tag == "tr"):
        span = parse_date_range(row.text())
        if not span or not (span[0] <= today <= span[1]):
            continue
        for a in row.find_all(lambda n: n.tag == "a"):
            href = a.attrs.get("href", "")
            if "/tournament/" in href and a.text().strip().upper() in ("VG", "VGC"):
                name_link = row.find(lambda n: n.tag == "a" and "/event/" in n.attrs.get("href", ""))
                name = name_link.text() if name_link else row.text()
                return href.rstrip("/").rsplit("/", 1)[-1], name
    return None


# ----------------------------------------------------------- Conversion to payload


def _add(record: dict | None, status: str | None) -> dict:
    r = dict(record or {"wins": 0, "losses": 0, "ties": 0})
    if status == "winner":
        r["wins"] += 1
    elif status == "loser":
        r["losses"] += 1
    elif status == "tie":
        r["ties"] += 1
    return r


def _result_from_previous(row: dict, my_id: str) -> str | None:
    return {"W": my_id, "L": row.get("opponentId") or "?", "T": "0"}.get(row.get("result") or "")


def build_inputs(
    tournament_id: str,
    name: str,
    rounds: dict[int, list[dict]],
    player_name: str,
    previous: dict | None,
    swiss_rounds: int | None,
    cut_size: int | None,
):
    """Turn scraped RK9 rounds into (details, standings, pairings, me) for build_payload.

    `rounds` holds the rounds fetched this run; earlier rounds come from Wolfe's match rows in
    the previous payload. The latest round in `rounds` must be the current one.
    """
    my_id = normalize_name(player_name)
    latest_round = max(rounds)

    def phase_of(rnd: int) -> int:
        return 2 if swiss_rounds and rnd > swiss_rounds else 1

    # With the round count unknown, never let a finished round read as the end of the event.
    phases = [{"phase": 1, "type": "SWISS", "rounds": swiss_rounds or latest_round + 1}]
    if swiss_rounds and cut_size:
        phases.append({"phase": 2, "type": "SINGLE_ELIMINATION", "rounds": cut_size.bit_length() - 1})
    details = {"name": name, "phases": phases}

    pairings: list[dict] = []
    known: dict[str, dict] = {}  # latest record we know for each player, keyed by id

    # Wolfe's earlier matches from the cached payload.
    cached_rounds: set[int] = set()
    if previous and previous.get("tournamentId") == tournament_id:
        for row in previous.get("matches") or []:
            rnd = int(row.get("round") or 0)
            if rnd in rounds or row.get("result") is None:
                continue
            cached_rounds.add(rnd)
            pairings.append({
                "round": rnd, "phase": phase_of(rnd), "table": None,
                "player1": my_id, "player2": row.get("opponentId") or "",
                "winner": _result_from_previous(row, my_id),
            })
            if row.get("opponentId") and row.get("opponentRecord"):
                known[row["opponentId"]] = {
                    "player": row["opponentId"], "name": row.get("opponent"),
                    "record": row["opponentRecord"], "drop": True,
                }

    # Rounds fetched now, oldest first so later records overwrite earlier ones.
    shown: list[tuple[int, dict, str | None]] = []
    for rnd in sorted(rounds):
        for m in rounds[rnd]:
            p1, p2 = m["p1"], m["p2"]
            ids = [p["id"] for p in (p1, p2) if p]
            if rnd != latest_round and my_id not in ids:
                continue  # only Wolfe's matches matter from older rounds
            winner = None
            for p in (p1, p2):
                if p and p["status"] == "winner":
                    winner = p["id"]
            if winner is None and any(p and p["status"] == "tie" for p in (p1, p2)):
                winner = "0"
            if winner is None and p1 and p2 and p1["status"] == "loser" and p2["status"] == "loser":
                winner = "-1"
            if not p2 or not p1:
                winner = winner or (p1 or p2)["id"]  # bye
            pairings.append({
                "round": rnd, "phase": phase_of(rnd), "table": m["table"],
                "player1": p1["id"] if p1 else "", "player2": p2["id"] if p2 else "",
                "winner": winner,
            })
            for p in (p1, p2):
                if p and p["record"] is not None:
                    status = (p["status"] if p1 and p2 else "winner") if winner is not None else None
                    shown.append((rnd, p, status))

    # RK9 shows a record next to each name. Work out from Wolfe's own history whether it is the
    # record entering the round or already includes its result, then apply that to everyone.
    entering = True
    mine_shown = next((p["record"] for rnd, p, st in reversed(shown) if p["id"] == my_id and st), None)
    if mine_shown is not None:
        before = {"wins": 0, "losses": 0, "ties": 0}
        last = max(r for r, p, st in shown if p["id"] == my_id and st)
        for pr in pairings:
            if my_id not in (pr["player1"], pr["player2"]) or pr["round"] >= last:
                continue
            w = str(pr["winner"])
            key = "wins" if w == my_id or not pr["player2"] else "ties" if w == "0" else "losses"
            before[key] += 1
        entering = mine_shown == before
    for rnd, p, status in shown:
        known[p["id"]] = {
            "player": p["id"], "name": p["name"],
            "record": _add(p["record"], status) if entering else dict(p["record"]),
            "drop": rnd != latest_round,
        }

    # Rounds Wolfe sat out entirely still need a placeholder so round counts stay right.
    for rnd in range(1, latest_round + 1):
        if rnd not in rounds and rnd not in cached_rounds:
            pairings.append({"round": rnd, "phase": phase_of(rnd), "table": None,
                             "player1": "", "player2": "", "winner": "-1"})

    standings = list(known.values())
    me = known.get(my_id)
    if me is None:
        return details, standings, pairings, None

    # Rank by match points among players still in the latest round; ties share a rank.
    def pts(s: dict) -> int:
        return 3 * s["record"]["wins"] + s["record"]["ties"]

    active = [s for s in standings if not s["drop"]]
    for s in active:
        s["placing"] = 1 + sum(1 for o in active if pts(o) > pts(s))
    return details, standings, pairings, me


def rounds_to_fetch(previous: dict | None, tournament_id: str, latest_round: int) -> list[int]:
    """Older rounds Wolfe's history is missing, plus the latest round."""
    have = set()
    if previous and previous.get("tournamentId") == tournament_id:
        have = {int(m.get("round") or 0) for m in previous.get("matches") or [] if m.get("result")}
    missing = [r for r in range(1, latest_round) if r not in have]
    return missing + [latest_round]


def parse_page_info(html: str) -> dict:
    """Event name and player count from the pairings page header."""
    root = parse_html(html)
    h4 = root.find(lambda n: n.tag == "h4")
    m = re.search(r"([\d,]+)\s+players", root.text())
    return {"name": h4.text() if h4 else None, "players": int(m[1].replace(",", "")) if m else None}


def scrape(tournament_id: str, pod: int, previous: dict | None,
           player_name: str) -> tuple[dict[int, list[dict]], dict]:
    """Fetch the current round, plus any earlier rounds not cached in the previous payload.

    Older rounds are only fetched once Wolfe is found in the current round, so an event he
    isn't playing costs a single request. Also returns the page's event name and player count.
    """
    html = fetch(f"/pairings/{tournament_id}")
    info = parse_page_info(html)
    by_round, linked = parse_pairings_page(html, pod)
    latest = max(linked | set(by_round), default=0)
    if not latest:
        # No round tabs found: probe rounds until one comes back empty.
        for rnd in range(1, MAX_ROUNDS + 1):
            if not (found := fetch_round(tournament_id, pod, rnd)):
                break
            by_round[rnd] = found
        return by_round, info

    current = by_round.get(latest) or fetch_round(tournament_id, pod, latest)
    my_id = normalize_name(player_name)
    if not any(p and p["id"] == my_id for m in current for p in (m["p1"], m["p2"])):
        info["latest"] = latest  # lets the caller tell "never here" from "cut from this round"
        return {}, info

    wanted = rounds_to_fetch(previous, tournament_id, latest)
    rounds = {latest: current}
    for rnd in wanted[:-1]:
        if rnd not in by_round:
            time.sleep(REQUEST_GAP_SECONDS)  # back-fill one round at a time, gently
        rounds[rnd] = by_round.get(rnd) or fetch_round(tournament_id, pod, rnd)
    return {r: m for r, m in rounds.items() if m}, info


def team_from_payload(previous: dict | None, tournament_id: str) -> list[dict]:
    if previous and previous.get("tournamentId") == tournament_id:
        return previous.get("team") or []
    return []


# ------------------------------------------------------------- Top cut projection
#
# RK9 doesn't publish the round count or cut. Under the current Championship Series format,
# Day 1 Swiss is followed by more Swiss rounds on Day 2 for the players who made it, then an
# "asymmetrical" top 8: everyone with the same record as 8th place gets in. Wolfe's chances
# are projected from the field that is still playing, not decided by tiebreakers.


def estimate_swiss_rounds(players: int | None, active: int) -> int | None:
    """Total Swiss rounds, or None while Day 1 is still on (Day 2 size unknown yet).

    Day 1 is 9 rounds for 800+ players (Louisville 2027) and 8 below that. Day 2 is taken to
    run until about 8 players could still be undefeated on the day.
    """
    if not players or active >= players / 3:
        return None
    day1 = 9 if players >= 800 else 8
    return day1 + max(1, math.ceil(math.log2(max(active, 2) / 8)))


def projected_cut_line(points: list[int], remaining: int, cut: int = 8) -> int | None:
    """Match points the `cut`-th player is expected to finish on.

    Assumes points-paired Swiss where each score group splits evenly every round.
    """
    groups: dict[int, float] = {}
    for pts in points:
        groups[pts] = groups.get(pts, 0) + 1
    for _ in range(remaining):
        nxt: dict[int, float] = {}
        for pts, n in groups.items():
            nxt[pts + 3] = nxt.get(pts + 3, 0) + n / 2
            nxt[pts] = nxt.get(pts, 0) + n / 2
        groups = nxt
    total = 0.0
    for p in sorted(groups, reverse=True):
        total += groups[p]
        if total >= cut - 1e-9:
            return int(p)
    return None


def cut_status(my_points: int, my_losses: int, field: list[int], players: int | None,
               played: int, swiss_override: int | None, cut: int = 8) -> str | None:
    """'alive', 'bubble' (must win out) or 'eliminated' while Swiss is running; None if unknown."""
    total = swiss_override or estimate_swiss_rounds(players, len(field))
    if total is None:
        # Day 1: no Day 2 cut has ever let a 4-loss player through.
        return "eliminated" if my_losses >= 4 else None
    remaining = max(0, total - played)
    line = projected_cut_line(field, remaining, cut)
    if line is None:
        return None
    best = my_points + 3 * remaining
    if best < line:
        return "eliminated"
    return "bubble" if best == line else "alive"
