# The Glick Tracker

A zero-cost, live fan dashboard for following Wolfe Glick through VGC tournaments.

- **Dashboard**: Vite + React + Tailwind + Lucide, built to static files and served from GitHub Pages.
- **Data**: `scripts/update_tracker.py` pulls standings, pairings and the open team sheet from
  [Limitless VGC](https://play.limitlesstcg.com) and writes `glick_live.json` to a gist.
- **Live updates**: the page re-fetches the gist's raw URL every 30 seconds with a `?t=` cache buster.

## Setup

1. **Secrets** (Settings → Secrets and variables → Actions):
   - `GIST_ID`: id of the gist holding `glick_live.json`
   - `GH_PAT`: a token with the `gist` scope
   - `LIMITLESS_API_KEY` (optional): only if Limitless requires a key for your usage
2. **Variables** (optional):
   - `VITE_GIST_RAW_URL`: raw URL the dashboard polls. Defaults to
     `https://gist.githubusercontent.com/toolateforteddy/f63b15c0e419f0d8cd3bdce9ceb01372/raw/glick_live.json`
   - `TOURNAMENT_ID`: pin a Limitless tournament instead of auto-discovery
   - `PLAYER_ID`: Limitless username to track (otherwise matched by the name "Wolfe Glick")
   - `STREAM_URL`: link for the stream badge (defaults to Wolfe's Twitch)
3. **Pages**: Settings → Pages → Source: **GitHub Actions**.

## Workflows

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `deploy.yml` | push to `main` | `npm ci && npm run build`, deploys `./dist` to Pages |
| `sync.yml` | every 10 min on weekend tournament hours (UTC), or manual | runs `update_tracker.py` |

Run **Sync tournament data** manually with a `tournament_id` to track a specific event.

## Local development

```bash
npm install
npm run dev            # polls the live gist
# open http://localhost:5173/?demo to preview with bundled sample data

DRY_RUN=1 TOURNAMENT_ID=<id> python3 scripts/update_tracker.py   # print the payload, no gist write
python3 -m unittest discover scripts                              # script tests
```

## How the numbers are computed

- **OPW%**: average of Swiss opponents' match win rates, each floored at 25% (byes excluded).
- **Top cut**: from match points (W=3, T=1). *Cut Clinched* when fewer players than the cut size can
  still reach Wolfe's current points; *Eliminated* when at least that many already have more points
  than his best possible finish; otherwise *Alive*. After Swiss it uses his final placing.
- **Round timer**: the sync stamps the time it first sees a new round's pairings, so it is accurate to
  the sync interval. Before a new round has been observed it shows
  "Match in progress - awaiting slip submission".
- **Game scores**: Limitless pairings report only the match winner, so the Games column shows "—"
  unless a score is present in the data.
