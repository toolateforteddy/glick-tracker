#!/usr/bin/env python3
"""Collect Wolfe Glick's finished RK9 events into src/data/history.json for the Past Events section.

History is static: run this by hand after an event ends and commit the result, so finished
events are never re-scraped by the live sync. Events already in the file are skipped, and so
are events whose roster was already checked and didn't include Wolfe.

    python3 scripts/rk9_history.py                       # scan NA events, ICs and Worlds since --since
    python3 scripts/rk9_history.py BA002-JL3KVbvivVKNAc  # add specific RK9 tournament ids
    python3 scripts/rk9_history.py --since 2025-09-01 --dry-run

Cost per event: one roster page; for events Wolfe played, also his team list and one page per
round he played. Requests are spaced out like the live scraper's back-fill.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rk9  # noqa: E402
from update_tracker import bracket_label  # noqa: E402

HISTORY_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "history.json"
PLAYER_NAME = os.environ.get("PLAYER_NAME", "Wolfe Glick")
REQUEST_GAP_SECONDS = 2.0
# Wolfe is US-based: by default only scan North American events plus Internationals and Worlds.
DEFAULT_REGIONS = (", US", ", CA")
ALWAYS_SCAN = ("International", "World")


# ------------------------------------------------------------------------ Parsing


def parse_events(html: str) -> list[dict]:
    """Every row of rk9.gg/events/pokemon that has a VG tournament."""
    events = []
    for row in rk9.parse_html(html).find_all(lambda n: n.tag == "tr"):
        span = rk9.parse_date_range(row.text())
        if not span:
            continue
        vg = next((a.attrs["href"] for a in row.find_all(lambda n: n.tag == "a")
                   if "/tournament/" in a.attrs.get("href", "")
                   and a.text().strip().upper() in ("VG", "VGC")), None)
        if not vg:
            continue
        # Columns: dates, event logo, name, location, links. Find the name cell rather than
        # counting, in case the logo column is missing.
        cells = [c for c in row.children if not isinstance(c, str) and c.tag == "td"]
        name_at = next((i for i, c in enumerate(cells)
                        if c.find(lambda n: n.tag == "a" and "/event/" in n.attrs.get("href", ""))), 2)
        name_cell = cells[name_at] if name_at < len(cells) else None
        name_link = name_cell and name_cell.find(lambda n: n.tag == "a")
        events.append({
            "id": vg.rstrip("/").rsplit("/", 1)[-1],
            "name": (name_link or name_cell).text() if name_cell else "",
            "location": cells[name_at + 1].text() if name_at + 1 < len(cells) else "",
            "start": span[0],
            "end": span[1],
        })
    return events


def wanted_by_default(event: dict) -> bool:
    return (event["location"].endswith(DEFAULT_REGIONS)
            or any(word in event["name"] for word in ALWAYS_SCAN))


def parse_roster(html: str, player_name: str) -> dict | None:
    """Wolfe's Masters roster row: final standing and the public team list link, if any."""
    target = rk9.normalize_name(player_name)
    for row in rk9.parse_html(html).find_all(lambda n: n.tag == "tr"):
        cells = [c for c in row.children if not isinstance(c, str) and c.tag == "td"]
        if len(cells) < 3 or rk9.normalize_name(cells[1].text() + cells[2].text()) != target:
            continue
        texts = [c.text() for c in cells]
        if "Masters" not in texts:
            continue
        link = row.find(lambda n: n.tag == "a" and "/teamlist/" in n.attrs.get("href", ""))
        standing = texts[-1] if texts[-1].isdigit() else None
        return {"standing": int(standing) if standing else None,
                "teamlist": link.attrs["href"] if link else None}
    return None


# Form words RK9 prints that Showdown's sprite ids leave out or spell differently.
DEFAULT_FORMS = {"Incarnate", "Unremarkable", "Male", "Teal"}
REGION_FORMS = {"Alolan": "Alola", "Galarian": "Galar", "Hisuian": "Hisui", "Paldean": "Paldea"}


def species_name(raw: str) -> str:
    """RK9 'Indeedee [Female]' -> 'Indeedee-F', 'Zoroark [Hisuian Form]' -> 'Zoroark-Hisui'."""
    m = re.fullmatch(r"(.+?)\s*\[(.+)\]", raw.strip())
    if not m:
        return raw.strip()
    base, form = m[1], m[2].strip()
    if form == "Female":
        return f"{base}-F"
    words = re.sub(r"\b(Form|Forme|Style|Mode|Cloak|Mask)\b", "", form.replace(base, "")).split()
    words = [REGION_FORMS.get(w, w) for w in words if w not in DEFAULT_FORMS]
    return "-".join([base, *words])


def parse_teamlist(html: str) -> list[dict]:
    """The English block of an RK9 public team list."""
    root = rk9.parse_html(html)
    block = root.find(lambda n: n.attrs.get("id") == "lang-EN") or root
    team = []
    for mon in block.find_all(lambda n: n.tag == "div" and "pokemon" in n.classes):
        text = mon.text()
        head = re.split(r"\s+EN\b|\s+Ability:", text, maxsplit=1)[0]
        ability = re.search(r"Ability:\s*(.+?)\s+Held Item:", text)
        item = re.search(r"Held Item:\s*(.+?)\s+(?:Stat Alignment:|Tera Type:|$)", text)
        tera = re.search(r"Tera Type:\s*(.+?)\s+(?:Stat Alignment:|$)", text)
        moves = [b.text() for b in mon.find_all(lambda n: "badge" in n.classes) if b.text()]
        team.append({
            "species": species_name(head.replace("\xa0", " ")),
            "item": item[1].strip() if item else None,
            "ability": ability[1].strip() if ability else None,
            "tera": tera[1].strip() if tera else None,
            "moves": moves[:4],
        })
    return team


# ------------------------------------------------------------------------- Rounds


def my_match(matches: list[dict], my_id: str) -> dict | None:
    for m in matches:
        for me, opp in ((m["p1"], m["p2"]), (m["p2"], m["p1"])):
            if me and me["id"] == my_id:
                if opp is None:
                    result = "BYE"
                elif me["status"] == "winner":
                    result = "W"
                elif me["status"] == "tie":
                    result = "T"
                elif me["status"] == "loser" or (opp and opp["status"] == "winner"):
                    result = "L"
                else:
                    result = None
                return {"opponent": opp["name"] if opp else None,
                        "opponentId": opp["id"] if opp else None, "result": result}
    return None


def scrape_rounds(tournament_id: str, html: str, my_id: str,
                  pause) -> tuple[list[dict], int | None, int | None]:
    """Wolfe's matches, the number of Swiss rounds and the top cut size (None if he missed cut).

    `html` is the event's main pairings page; earlier rounds are fetched one at a time.
    """
    by_round, linked = rk9.parse_pairings_page(html, rk9.MASTERS_POD)
    latest = max(linked | set(by_round), default=0)

    # (round, matches in round if it could be a bracket round else 0, Wolfe's match)
    played: list[tuple[int, int, dict]] = []
    for rnd in range(1, latest + 1):
        if rnd not in by_round:
            pause()
            by_round[rnd] = rk9.fetch_round(tournament_id, rk9.MASTERS_POD, rnd)
        mine = my_match(by_round[rnd], my_id)
        if mine is None:
            if played:
                break  # dropped, missed day 2 or eliminated
            continue
        # Bracket rounds have no byes; a late Swiss round can be just as small (ICs give the
        # leaders byes in the last round), so a round with a bye never starts the bracket.
        has_bye = any(not (m["p1"] and m["p2"]) for m in by_round[rnd])
        played.append((rnd, 0 if has_bye else len(by_round[rnd]), mine))

    # The bracket starts at the first bye-free round of 8 or fewer matches after a Swiss round:
    # Swiss rounds of a Regional are far wider than a Top 16.
    swiss_rounds = cut_size = None
    for (_, prev_n, _), (rnd, n, _) in zip(played, played[1:]):
        if 0 < n <= 8 and (prev_n == 0 or prev_n > 8):
            swiss_rounds, cut_size = rnd - 1, 2 * n
            break

    rows = []
    for rnd, _, m in played:
        in_cut = swiss_rounds is not None and rnd > swiss_rounds
        label = bracket_label(max(2, cut_size >> (rnd - swiss_rounds - 1))) if in_cut else f"R{rnd}"
        rows.append({"round": rnd, "phase": "topcut" if in_cut else "swiss", "label": label,
                     **m, "score": None})
    return rows, swiss_rounds, cut_size


def build_event(event: dict, roster: dict, team: list[dict], rows: list[dict],
                swiss_rounds: int | None, cut_size: int | None, players: int | None) -> dict:
    record = {"w": 0, "l": 0, "t": 0}
    for r in rows:
        key = {"W": "w", "BYE": "w", "L": "l", "T": "t"}.get(r["result"] or "")
        if key:
            record[key] += 1
    return {
        "id": event["id"],
        "name": event["name"],
        "location": event.get("location") or None,
        "startDate": event["start"].isoformat(),
        "endDate": event["end"].isoformat(),
        "url": f"{rk9.RK9}/tournament/{event['id']}",
        "players": players,
        "placing": roster["standing"],
        "record": record,
        "swissRounds": swiss_rounds,
        "topCutSize": cut_size,
        "madeTopCut": any(r["phase"] == "topcut" for r in rows),
        "team": team,
        "matches": rows,
    }


# --------------------------------------------------------------------------- Main


def load_history() -> dict:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return {"events": [], "checked": []}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ids", nargs="*", help="RK9 tournament ids to add (skips the default scan)")
    ap.add_argument("--since", default="2025-09-01", help="earliest event start date to scan")
    ap.add_argument("--dry-run", action="store_true", help="print instead of writing history.json")
    args = ap.parse_args()

    history = load_history()
    done = {e["id"] for e in history["events"]} | set(history.get("checked") or [])
    my_id = rk9.normalize_name(PLAYER_NAME)
    today = date.today()

    def pause():
        time.sleep(REQUEST_GAP_SECONDS)

    events = parse_events(rk9.fetch("/events/pokemon"))
    if args.ids:
        by_id = {e["id"]: e for e in events}
        todo = [by_id.get(i) or {"id": i, "name": i, "location": "", "start": today, "end": today}
                for i in args.ids]
    else:
        since = date.fromisoformat(args.since)
        todo = [e for e in events if since <= e["start"] and e["end"] < today and wanted_by_default(e)]
    todo = [e for e in todo if e["id"] not in done]

    for event in sorted(todo, key=lambda e: e["start"]):
        pause()
        roster = parse_roster(rk9.fetch(f"/roster/{event['id']}"), PLAYER_NAME)
        if roster is None:
            print(f"-  {event['name']}: not on the Masters roster", file=sys.stderr)
            history.setdefault("checked", []).append(event["id"])
            continue
        team: list[dict] = []
        if roster["teamlist"]:
            pause()
            team = parse_teamlist(rk9.fetch(roster["teamlist"]))
        pause()
        pairings_html = rk9.fetch(f"/pairings/{event['id']}")
        info = rk9.parse_page_info(pairings_html)
        if event["name"] == event["id"] and info["name"]:
            event["name"] = info["name"]
        rows, swiss_rounds, cut_size = scrape_rounds(event["id"], pairings_html, my_id, pause)
        if not rows:
            print(f"-  {event['name']}: registered but played no rounds", file=sys.stderr)
            history.setdefault("checked", []).append(event["id"])
            continue
        entry = build_event(event, roster, team, rows, swiss_rounds, cut_size, info["players"])
        rec = entry["record"]
        print(f"+  {event['name']}: #{entry['placing']}, {rec['w']}-{rec['l']}-{rec['t']}", file=sys.stderr)
        history["events"].append(entry)

    history["events"].sort(key=lambda e: e["startDate"], reverse=True)
    history["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = json.dumps(history, indent=2, ensure_ascii=False) + "\n"
    if args.dry_run:
        print(out)
    else:
        HISTORY_PATH.write_text(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
