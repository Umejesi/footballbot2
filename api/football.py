import httpx
import os
from datetime import datetime, timedelta

API_KEY = os.getenv("FOOTBALL_API_KEY", "")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

LEAGUES = {
    "pl": 2021,
    "ucl": 2001,
    "laliga": 2014,
    "seriea": 2019,
    "bundesliga": 2002,
    "ligue1": 2015,
}


async def _get(endpoint: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e), "matches": [], "standings": [], "scorers": []}


async def get_live_scores() -> dict:
    return await _get("/matches?status=LIVE")


async def get_todays_matches() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    return await _get(f"/matches?dateFrom={today}&dateTo={today}")


async def get_tomorrows_matches() -> dict:
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return await _get(f"/matches?dateFrom={tomorrow}&dateTo={tomorrow}")


async def get_this_week_matches() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    return await _get(f"/matches?dateFrom={today}&dateTo={week}")


async def get_standings(league_key: str = "pl") -> dict:
    league_id = LEAGUES.get(league_key.lower(), 2021)
    return await _get(f"/competitions/{league_id}/standings")


async def get_top_scorers(league_key: str = "pl") -> dict:
    league_id = LEAGUES.get(league_key.lower(), 2021)
    return await _get(f"/competitions/{league_id}/scorers?limit=10")


def _format_matches(matches: list, title: str, empty_msg: str) -> str:
    if not matches:
        return empty_msg

    lines = [f"{title}\n"]
    for m in matches[:15]:
        home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name", "?")
        away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name", "?")
        utc_date = m.get("utcDate", "")
        try:
            dt = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%SZ")
            time_str = dt.strftime("%H:%M UTC")
        except Exception:
            time_str = "TBD"
        comp = m.get("competition", {}).get("name", "")
        lines.append(f"• `{home} vs {away}` — {time_str}")
        if comp:
            lines[-1] += f"\n  _{comp}_"
    return "\n".join(lines)


def format_live_scores(data: dict) -> str:
    matches = data.get("matches", [])
    if not matches:
        return "No live matches right now.\n\nUse /matches for today's fixtures or /tomorrow for tomorrow's games."

    lines = ["🔴 *LIVE SCORES*\n"]
    for m in matches[:10]:
        home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name", "?")
        away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name", "?")
        score = m.get("score", {}).get("fullTime", {})
        h = score.get("home") if score.get("home") is not None else "-"
        a = score.get("away") if score.get("away") is not None else "-"
        minute = m.get("minute", "")
        min_str = f" {minute}'" if minute else ""
        lines.append(f"`{home}  {h} - {a}  {away}`{min_str}")
    return "\n".join(lines)


def format_todays_matches(data: dict) -> str:
    return _format_matches(
        data.get("matches", []),
        "📅 *TODAY'S FIXTURES*",
        "No matches scheduled today.\n\nTry /tomorrow to see tomorrow's games!"
    )


def format_tomorrows_matches(data: dict) -> str:
    return _format_matches(
        data.get("matches", []),
        "📅 *TOMORROW'S FIXTURES*",
        "No matches scheduled tomorrow either.\n\nTry /week to see this week's games!"
    )


def format_week_matches(data: dict) -> str:
    return _format_matches(
        data.get("matches", []),
        "📅 *THIS WEEK'S FIXTURES*",
        "No matches found this week on the free API plan.\n\nTry asking the AI: /ask upcoming Premier League matches"
    )


def format_standings(data: dict) -> str:
    standings = data.get("standings", [])
    if not standings:
        return "Could not fetch standings right now. Try again shortly!"

    table = standings[0].get("table", [])
    comp = data.get("competition", {}).get("name", "League Table")
    lines = [f"📊 *{comp.upper()}*\n"]
    lines.append("`Pos  Team               Pts`")
    for row in table[:10]:
        pos = row.get("position", "-")
        team = (row.get("team", {}).get("shortName") or
                row.get("team", {}).get("name", "?"))[:16]
        pts = row.get("points", 0)
        won = row.get("won", 0)
        draw = row.get("draw", 0)
        lost = row.get("lost", 0)
        lines.append(f"`{str(pos).ljust(4)} {team.ljust(18)} {pts}`  W{won} D{draw} L{lost}")
    return "\n".join(lines)


def format_top_scorers(data: dict) -> str:
    scorers = data.get("scorers", [])
    if not scorers:
        return "Could not fetch top scorers right now. Try again shortly!"

    lines = ["⚽ *TOP SCORERS*\n"]
    medals = ["🥇", "🥈", "🥉"] + ["   "] * 20
    for i, s in enumerate(scorers[:10]):
        name = s.get("player", {}).get("name", "?")
        team = (s.get("team", {}).get("shortName") or
                s.get("team", {}).get("name", "?"))
        goals = s.get("goals", 0)
        assists = s.get("assists", 0) or 0
        lines.append(f"{medals[i]} *{name}* ({team}) — {goals} ⚽ {assists} 🅰️")
    return "\n".join(lines)
