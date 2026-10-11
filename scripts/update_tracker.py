#!/usr/bin/env python3
"""Pull Wolfe Glick's live tournament data from Limitless VGC and publish it to a gist.

Environment:
  GIST_ID          (required) gist that holds glick_live.json
  GH_PAT           (required) token with the `gist` scope
  TOURNAMENT_ID    (optional) Limitless tournament id; discovered automatically when omitted
  PLAYER_ID        (optional) Limitless username to track; otherwise matched by PLAYER_NAME
  PLAYER_NAME      (optional) display name to match, default "Wolfe Glick"
  STREAM_URL       (optional) link for the stream badge, default Wolfe's Twitch
  LIMITLESS_API_KEY (optional) sent as X-Access-Key if your key is needed
  LOOKBACK_DAYS    (optional) how far back discovery looks, default 3
  DRY_RUN          (optional) "1" prints the payload instead of patching the gist

Only the standard library is used so the workflow needs no pip install.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

import rk9

LIMITLESS_API = "https://play.limitlesstcg.com/api"
LIMITLESS_WEB = "https://play.limitlesstcg.com"
GITHUB_API = "https://api.github.com"
GIST_FILENAME = "glick_live.json"
DEFAULT_PLAYER_NAME = "Wolfe Glick"
DEFAULT_STREAM_URL = "https://www.twitch.tv/wolfeyvgc"
OPW_FLOOR = 0.25  # Pokémon tiebreaker rules floor each opponent's win rate at 25%.


# --------------------------------------------------------------------------- HTTP


def http_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, body: Any = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", "glick-tracker/1.0")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            raw = res.read()
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:300]
        raise RuntimeError(f"{method} {url} -> HTTP {err.code}: {detail}") from err
    return json.loads(raw) if raw else None


def limitless(path: str, **params: Any) -> Any:
    query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    headers = {}
    if key := os.environ.get("LIMITLESS_API_KEY"):
        headers["X-Access-Key"] = key
    return http_json(f"{LIMITLESS_API}{path}{'?' + query if query else ''}", headers=headers)


def github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def read_previous_payload(gist_id: str, token: str) -> dict | None:
    try:
        gist = http_json(f"{GITHUB_API}/gists/{gist_id}", headers=github_headers(token))
        content = (gist.get("files") or {}).get(GIST_FILENAME, {}).get("content")
        return json.loads(content) if content else None
    except (RuntimeError, json.JSONDecodeError) as err:
        print(f"warning: could not read previous payload: {err}", file=sys.stderr)
        return None


def write_payload(gist_id: str, token: str, payload: dict) -> None:
    http_json(
        f"{GITHUB_API}/gists/{gist_id}",
        method="PATCH",
        headers=github_headers(token),
        body={"files": {GIST_FILENAME: {"content": json.dumps(payload, indent=2)}}},
    )


# --------------------------------------------------------------------- Discovery


def normalize(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def find_player(standings: list[dict], player_id: str | None, player_name: str) -> dict | None:
    if player_id:
        return next((s for s in standings if normalize(s.get("player")) == normalize(player_id)), None)
    target = normalize(player_name)
    return next((s for s in standings if normalize(s.get("name")) == target), None)


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def discover_tournament(player_id: str | None, player_name: str, now: datetime, lookback_days: int):
    """Return (tournament_id, standings, player_row) for the newest recent VGC event Wolfe is in."""
    tournaments = limitless("/tournaments", game="VGC", limit=50) or []
    cutoff = now - timedelta(days=lookback_days)
    recent = [t for t in tournaments if (d := parse_date(t.get("date"))) and cutoff <= d <= now + timedelta(days=1)]
    recent.sort(key=lambda t: t.get("date") or "", reverse=True)
    for t in recent:
        try:
            standings = limitless(f"/tournaments/{t['id']}/standings") or []
        except RuntimeError as err:
            print(f"warning: skipping {t.get('id')}: {err}", file=sys.stderr)
            continue
        if row := find_player(standings, player_id, player_name):
            return t["id"], standings, row
    return None, None, None


# ------------------------------------------------------------------- Team sheet


def _first(d: dict, *keys: str) -> Any:
    for k in keys:
        if d.get(k):
            return d[k]
    return None


def parse_team(decklist: Any) -> list[dict]:
    """Normalize a Limitless VGC team list (OTS) into the dashboard's team schema."""
    if isinstance(decklist, dict):
        decklist = _first(decklist, "pokemon", "team", "decklist") or []
    if not isinstance(decklist, list):
        return []
    team = []
    for mon in decklist[:6]:
        if not isinstance(mon, dict):
            continue
        moves = _first(mon, "attacks", "moves") or []
        team.append(
            {
                "species": _first(mon, "name", "species", "id") or "Unknown",
                "item": _first(mon, "item"),
                "ability": _first(mon, "ability"),
                "tera": _first(mon, "tera", "teraType", "tera_type"),
                "moves": [m if isinstance(m, str) else str(_first(m, "name") or "") for m in moves][:4],
            }
        )
    return team


# ------------------------------------------------------------------ Calculations


def match_points(record: dict | None) -> int:
    record = record or {}
    return 3 * int(record.get("wins") or 0) + int(record.get("ties") or 0)


def games_played(record: dict | None) -> int:
    record = record or {}
    return sum(int(record.get(k) or 0) for k in ("wins", "losses", "ties"))


def win_rate(record: dict | None) -> float | None:
    played = games_played(record)
    if not played:
        return None
    return max(OPW_FLOOR, int((record or {}).get("wins") or 0) / played)


def compute_opw(opponent_ids: list[str], by_player: dict[str, dict]) -> float | None:
    rates = [r for o in opponent_ids if (r := win_rate(by_player.get(o, {}).get("record"))) is not None]
    return round(100 * sum(rates) / len(rates), 2) if rates else None


def top_cut_math(me: dict, standings: list[dict], my_remaining: int, swiss_rounds: int, cut_size: int) -> str:
    """Return 'clinched', 'eliminated' or 'alive' using worst/best-case match points.

    Clinched: fewer than `cut_size` other players can reach Wolfe's current points even if he loses out.
    Eliminated: at least `cut_size` players already have more points than his best possible finish.
    Ties on points are treated as "could go either way", so both checks are conservative.
    """
    my_min = match_points(me.get("record"))
    my_max = my_min + 3 * my_remaining
    others = [s for s in standings if s.get("player") != me.get("player")]
    active = [s for s in others if not s.get("drop")]

    already_ahead = sum(1 for s in active if match_points(s.get("record")) > my_max)
    if already_ahead >= cut_size:
        return "eliminated"

    def best_case(s: dict) -> int:
        remaining = max(0, swiss_rounds - games_played(s.get("record")))
        return match_points(s.get("record")) + 3 * remaining

    can_catch = sum(1 for s in active if best_case(s) >= my_min)
    return "clinched" if can_catch < cut_size else "alive"


# ---------------------------------------------------------------------- Payload


def classify_phases(details: dict) -> tuple[set[int], dict[int, int], int, int | None]:
    """Return (swiss phase numbers, rounds per phase, total swiss rounds, top cut size)."""
    swiss_phases: set[int] = set()
    rounds_by_phase: dict[int, int] = {}
    swiss_rounds = 0
    cut_size = None
    for p in details.get("phases") or []:
        num, rounds = int(p.get("phase") or 0), int(p.get("rounds") or 0)
        rounds_by_phase[num] = rounds
        if "SWISS" in str(p.get("type", "")).upper():
            swiss_phases.add(num)
            swiss_rounds += rounds
        elif cut_size is None and rounds:
            cut_size = 2**rounds
    return swiss_phases, rounds_by_phase, swiss_rounds, cut_size


def bracket_label(remaining: int) -> str:
    return {2: "Finals", 4: "Top 4"}.get(remaining, f"Top {remaining}")


def build_payload(
    tournament_id: str,
    details: dict,
    standings: list[dict],
    pairings: list[dict],
    me: dict,
    previous: dict | None,
    now: datetime,
    stream: str | None,
) -> dict:
    my_id = me.get("player")
    by_player: dict[Any, dict] = {s.get("player"): s for s in standings}
    swiss_phases, rounds_by_phase, swiss_rounds, cut_size = classify_phases(details)
    if not swiss_phases:
        swiss_phases = {1}

    def is_swiss(p: dict) -> bool:
        return int(p.get("phase") or 1) in swiss_phases

    def decided(p: dict) -> bool:
        return p.get("winner") not in (None, "") or not p.get("player2")

    # First round number of each phase, to turn bracket rounds into "Top 8" style labels.
    first_round: dict[int, int] = {}
    for p in pairings:
        ph = int(p.get("phase") or 1)
        first_round[ph] = min(first_round.get(ph, 10**6), int(p.get("round") or 0))

    def label_for(p: dict) -> str:
        if is_swiss(p):
            return f"R{p.get('round')}"
        if cut_size:
            idx = int(p.get("round") or 0) - first_round.get(int(p.get("phase") or 1), 0)
            return bracket_label(max(2, cut_size >> idx))
        return str(p.get("match") or f"R{p.get('round')}")

    mine = sorted(
        (p for p in pairings if my_id in (p.get("player1"), p.get("player2"))),
        key=lambda p: (int(p.get("phase") or 1), int(p.get("round") or 0)),
    )

    matches: list[dict[str, Any]] = []
    opponents: list[str] = []
    for p in mine:
        opp = p.get("player2") if p.get("player1") == my_id else p.get("player1")
        winner = p.get("winner")
        if not opp:
            result = "BYE"
        elif winner in (None, ""):
            result = None
        elif str(winner) == str(my_id):
            result = "W"
        elif str(winner) == "0":
            result = "T"
        else:
            result = "L"  # includes -1 (double loss)
        if opp and is_swiss(p) and result is not None:
            opponents.append(opp)
        matches.append(
            {
                "round": int(p.get("round") or 0),
                "phase": "swiss" if is_swiss(p) else "topcut",
                "label": label_for(p),
                "opponent": (by_player.get(opp) or {}).get("name") or opp,
                "opponentId": opp,
                "result": result,
                # Limitless pairings only report the match winner, not game counts.
                "score": p.get("score"),
            }
        )

    # Tournament-wide progress.
    latest = max(pairings, key=lambda p: (int(p.get("phase") or 1), int(p.get("round") or 0)), default=None)
    latest_key = (int(latest.get("phase") or 1), int(latest.get("round") or 0)) if latest else None
    round_open = any(
        (int(p.get("phase") or 1), int(p.get("round") or 0)) == latest_key and not decided(p) for p in pairings
    )
    last_phase = max(rounds_by_phase) if rounds_by_phase else 1
    phase_rounds_played = len({int(p.get("round") or 0) for p in pairings if int(p.get("phase") or 1) == last_phase})
    finished = bool(latest) and not round_open and phase_rounds_played >= rounds_by_phase.get(last_phase, 10**6)

    current = next((m for m in reversed(matches) if m["result"] is None), None)
    in_topcut = any(m["phase"] == "topcut" for m in matches)

    if finished:
        phase, status = "finished", f"Final standing #{me.get('placing')}" if me.get("placing") else "Tournament complete"
    elif latest and int(latest.get("phase") or 1) not in swiss_phases:
        phase = "topcut"
        last_cut = next((m for m in reversed(matches) if m["phase"] == "topcut"), None)
        if current:
            status = current["label"]
        elif last_cut and last_cut["result"] == "W":
            status = f"Won {last_cut['label']} · awaiting next round"
        elif last_cut:
            status = f"Eliminated in {last_cut['label']}"
        else:
            status = "Top Cut in progress"
    elif latest_key:
        phase, status = "swiss", f"Round {latest_key[1]} Swiss"
    else:
        phase, status = "swiss", "Awaiting Round 1 pairings"
    if me.get("drop") and not finished:
        status = f"Dropped after Round {me.get('drop')}"

    # Top cut status.
    my_swiss_done = sum(1 for m in matches if m["phase"] == "swiss" and m["result"] is not None)
    swiss_over = phase in ("topcut", "finished") or (swiss_rounds and my_swiss_done >= swiss_rounds and not round_open)
    if in_topcut:
        cut_status = "clinched"
    elif me.get("drop"):
        cut_status = "eliminated"
    elif not cut_size:
        cut_status = "alive"
    elif swiss_over:
        placing = me.get("placing")
        cut_status = "clinched" if placing and placing <= cut_size else "eliminated"
    else:
        cut_status = top_cut_math(me, standings, max(0, swiss_rounds - my_swiss_done), swiss_rounds, cut_size)

    # Round timer: stamp the moment we first see a new round's pairings. We only know that
    # time if the previous run saw an earlier round, so the first observation stays null.
    round_key = f"{latest_key[0]}-{latest_key[1]}" if latest_key else None
    started_at = None
    if previous and previous.get("tournamentId") == tournament_id and round_key:
        if previous.get("roundKey") == round_key:
            started_at = previous.get("roundStartedAt")
        elif previous.get("roundKey"):
            started_at = now.isoformat().replace("+00:00", "Z")

    record = me.get("record") or {}

    return {
        "updatedAt": now.isoformat().replace("+00:00", "Z"),
        "tournament": details.get("name") or tournament_id,
        "tournamentId": tournament_id,
        "tournamentUrl": f"{LIMITLESS_WEB}/tournament/{tournament_id}/standings",
        "status": status,
        "phase": phase,
        "round": latest_key[1] if latest_key else None,
        "roundKey": round_key,
        "swissRounds": swiss_rounds or None,
        "topCutSize": cut_size,
        "players": details.get("players") or len(standings),
        "record": {
            "w": int(record.get("wins") or 0),
            "l": int(record.get("losses") or 0),
            "t": int(record.get("ties") or 0),
        },
        "standing": me.get("placing"),
        "opw": compute_opw(opponents, by_player),
        "topCutAlive": cut_status != "eliminated",
        "topCutStatus": cut_status,
        "stream": stream,
        "roundStartedAt": started_at,
        "currentMatchPending": current is not None,
        "team": parse_team(me.get("decklist")),
        "matches": matches,
    }


# ------------------------------------------------------------------------- Main


def parse_paste(text: str) -> list[dict]:
    """Parse a Showdown/PokePaste export into the dashboard's team schema."""
    team = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue
        head, _, item = lines[0].partition(" @ ")
        head = re.sub(r"\((M|F)\)", "", head).strip()
        nick = re.search(r"\(([^)]+)\)\s*$", head)
        mon: dict[str, Any] = {"species": nick[1] if nick else head, "item": item.strip() or None,
                               "ability": None, "tera": None, "moves": []}
        for line in lines[1:]:
            if line.startswith("Ability:"):
                mon["ability"] = line.split(":", 1)[1].strip()
            elif line.startswith("Tera Type:"):
                mon["tera"] = line.split(":", 1)[1].strip()
            elif line.startswith("-"):
                mon["moves"].append(line[1:].strip())
        team.append(mon)
    return team[:6]


def team_override() -> list[dict] | None:
    """Team from TEAM_PASTE (export text) or TEAM_PASTE_URL (a pokepast.es link), if set."""
    if text := os.environ.get("TEAM_PASTE", "").strip():
        return parse_paste(text)
    if url := os.environ.get("TEAM_PASTE_URL", "").strip():
        if "pokepast.es" in url and not url.rstrip("/").endswith("/json"):
            url = url.rstrip("/") + "/json"
        data = http_json(url)
        return parse_paste(data.get("paste", "") if isinstance(data, dict) else str(data))
    return None


def run_rk9(rk9_id: str, name: str | None, player_name: str, previous: dict | None,
            now: datetime, stream: str) -> dict | None:
    """Build a payload from RK9, or None if Wolfe isn't in this tournament's Masters pairings."""
    pod = int(os.environ.get("RK9_POD") or rk9.MASTERS_POD)
    swiss = int(os.environ.get("RK9_SWISS_ROUNDS") or 0) or None
    cut = int(os.environ.get("RK9_TOP_CUT") or 8)
    rounds, info = rk9.scrape(rk9_id, pod, previous, player_name)
    if not rounds:
        return None
    details, standings, pairings, me = rk9.build_inputs(
        rk9_id, name or os.environ.get("RK9_EVENT_NAME") or info["name"] or rk9_id, rounds, player_name, previous, swiss, cut)
    if not me:
        return None
    payload = build_payload(rk9_id, details, standings, pairings, me, previous, now, stream)

    # Remember each opponent's latest record so OPW works after they leave the pairings.
    records = {s["player"]: s["record"] for s in standings}
    for m in payload["matches"]:
        if m["opponentId"] in records:
            m["opponentRecord"] = records[m["opponentId"]]
    payload["source"] = "rk9"
    payload["tournamentUrl"] = f"{rk9.RK9}/tournament/{rk9_id}"
    payload["players"] = info["players"]
    payload["team"] = team_override() or rk9.team_from_payload(previous, rk9_id)
    if not (previous and previous.get("tournamentId") == rk9_id and previous.get("roundKey") == payload["roundKey"]):
        # A new round just went up: let it play out before scraping again.
        snooze = int(os.environ.get("RK9_SNOOZE_MINUTES") or 40)
        payload["snoozeUntil"] = (now + timedelta(minutes=snooze)).isoformat().replace("+00:00", "Z")
    else:
        payload["snoozeUntil"] = None
    return payload


def snoozed(previous: dict | None, now: datetime) -> bool:
    until = parse_date((previous or {}).get("snoozeUntil"))
    return bool(previous and previous.get("source") == "rk9" and until and now < until)


def main() -> int:
    gist_id = os.environ.get("GIST_ID", "").strip()
    token = os.environ.get("GH_PAT", "").strip()
    dry_run = os.environ.get("DRY_RUN") == "1"
    if not dry_run and not (gist_id and token):
        print("error: GIST_ID and GH_PAT are required", file=sys.stderr)
        return 1

    tournament_id = os.environ.get("TOURNAMENT_ID", "").strip() or None
    rk9_id = os.environ.get("RK9_TOURNAMENT_ID", "").strip() or None
    player_id = os.environ.get("PLAYER_ID", "").strip() or None
    player_name = os.environ.get("PLAYER_NAME", "").strip() or DEFAULT_PLAYER_NAME
    stream = os.environ.get("STREAM_URL", "").strip() or DEFAULT_STREAM_URL
    lookback = int(os.environ.get("LOOKBACK_DAYS") or 3)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    previous = read_previous_payload(gist_id, token) if gist_id and token else None

    payload = None
    if not tournament_id:
        # RK9 (Regionals, ICs, Worlds) first: an explicit id, or an event running today.
        if previous and snoozed(previous, now) and os.environ.get("FORCE") != "1":
            print(f"RK9 scraping snoozed until {previous['snoozeUntil']}; gist left as is.")
            return 0
        rk9_name = None
        if not rk9_id:
            try:
                found = rk9.discover_vg_tournament(now.date())
            except RuntimeError as err:
                print(f"warning: RK9 discovery failed: {err}", file=sys.stderr)
                found = None
            if found:
                rk9_id, rk9_name = found
        if rk9_id:
            payload = run_rk9(rk9_id, rk9_name, player_name, previous, now, stream)
            if payload is None and os.environ.get("RK9_TOURNAMENT_ID"):
                print(f"error: {player_name} not found in RK9 tournament {rk9_id}", file=sys.stderr)
                return 1
            if payload is None:
                print(f"{player_name} is not in RK9 tournament {rk9_id}; trying Limitless.")

    if payload is None:
        if tournament_id:
            standings = limitless(f"/tournaments/{tournament_id}/standings") or []
            me = find_player(standings, player_id, player_name)
            if not me:
                print(f"error: {player_id or player_name} not found in tournament {tournament_id}", file=sys.stderr)
                return 1
        else:
            tournament_id, standings, me = discover_tournament(player_id, player_name, now, lookback)
            if not tournament_id:
                print(f"No VGC tournament in the last {lookback} days includes {player_id or player_name}; gist left as is.")
                return 0
        details = limitless(f"/tournaments/{tournament_id}/details") or {}
        pairings = limitless(f"/tournaments/{tournament_id}/pairings") or []
        payload = build_payload(tournament_id, details, standings, pairings, me, previous, now, stream)
        payload["source"] = "limitless"
        if override := team_override():
            payload["team"] = override

    if dry_run:
        print(json.dumps(payload, indent=2))
        return 0
    write_payload(gist_id, token, payload)
    print(f"Updated gist {gist_id}: {payload['tournament']} · {payload['status']} · "
          f"{payload['record']['w']}-{payload['record']['l']}-{payload['record']['t']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
