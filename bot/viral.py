"""
Viral Growth Engine — Phase 1
Fast, clean, shareable football updates that grow the channel organically.
"""
import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from api.football import get_live_scores, get_todays_matches

logger = logging.getLogger(__name__)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@FOOTBALLAIOFFICIAL")
BOT_LINK = "https://t.me/PitchMasterAIBot"
CHANNEL_LINK = "https://t.me/FOOTBALLAIOFFICIAL"
STREAM_1 = "https://supersport.com/"
STREAM_2 = "https://sporty.com/"
AFFILIATE_LINK = os.getenv("AFFILIATE_LINK", "https://reffpa.com/L?tag=d_5683483m_97c_&site=5683483&ad=97")

# Track last known scores to detect goals/cards
_last_scores = {}
_posted_big_match_ids = set()


async def post(bot: Bot, text: str):
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except TelegramError as e:
        logger.error(f"Viral post failed: {e}")


def affiliate_line() -> str:
    if AFFILIATE_LINK:
        return f"\n🎰 [Best odds on 1xBet]({AFFILIATE_LINK}) — _18+ Gamble responsibly_"
    return ""


def forward_prompt() -> str:
    prompts = [
        "\n📢 *Share this with a football fan!*",
        "\n🔁 *Forward this live update to your group!*",
        "\n⚽ *Know a football fan? Send them this!*",
        "\n📲 *Follow for live updates all season!*",
    ]
    import random
    return random.choice(prompts)


# ─── GOAL ALERT (fastest growth method) ─────────────────────────────────────
async def check_and_post_goal_alerts(bot: Bot):
    """
    Checks live scores every 2 minutes.
    When a goal is detected — posts INSTANTLY.
    This is the #1 viral growth driver.
    """
    global _last_scores
    data = await get_live_scores()
    matches = data.get("matches", [])

    for m in matches:
        match_id = m.get("id", "")
        home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
        away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
        score = m.get("score", {}).get("fullTime", {})
        h = score.get("home", 0) or 0
        a = score.get("away", 0) or 0
        minute = m.get("minute", "?")
        comp = m.get("competition", {}).get("name", "")
        status = m.get("status", "")

        prev = _last_scores.get(match_id, {"home": 0, "away": 0, "status": ""})

        # ── GOAL DETECTED ────────────────────────────────
        if h > prev["home"]:
            # Home team scored
            text = (
                f"⚽ *GOAL!*\n\n"
                f"*{home} {h}–{a} {away}*\n"
                f"⏱ {minute}' | _{comp}_\n\n"
                f"🔴 Live updates coming...\n"
                f"📊 Scores: {BOT_LINK}"
                f"{forward_prompt()}"
            )
            await post(bot, text)

        elif a > prev["away"]:
            # Away team scored
            text = (
                f"⚽ *GOAL!*\n\n"
                f"*{home} {h}–{a} {away}*\n"
                f"⏱ {minute}' | _{comp}_\n\n"
                f"🔴 Live updates coming...\n"
                f"📊 Scores: {BOT_LINK}"
                f"{forward_prompt()}"
            )
            await post(bot, text)

        # ── HALF TIME ────────────────────────────────────
        if status == "HALF_TIME" and prev["status"] != "HALF_TIME":
            text = (
                f"🔔 *HALF TIME*\n\n"
                f"*{home} {h}–{a} {away}*\n"
                f"_{comp}_\n\n"
                f"What do you expect in the second half?\n"
                f"💬 {BOT_LINK}"
                f"{forward_prompt()}"
            )
            await post(bot, text)

        # ── FULL TIME ────────────────────────────────────
        if status == "FINISHED" and prev["status"] not in ("FINISHED", ""):
            result = "Draw" if h == a else (f"{home} win" if h > a else f"{away} win")
            text = (
                f"🏁 *FULL TIME*\n\n"
                f"*{home} {h}–{a} {away}*\n"
                f"_{comp}_\n\n"
                f"Result: *{result}*\n\n"
                f"📊 Match stats & predictions: {BOT_LINK}"
                f"{affiliate_line()}"
                f"{forward_prompt()}"
            )
            await post(bot, text)

        # Update last known state
        _last_scores[match_id] = {"home": h, "away": a, "status": status}

    # Clean up finished matches older than current session
    current_ids = {m.get("id") for m in matches}
    _last_scores = {k: v for k, v in _last_scores.items() if k in current_ids}


# ─── BIG MATCH HYPE POST ─────────────────────────────────────────────────────
BIG_MATCH_TEAMS = [
    "real madrid", "barcelona", "manchester city", "manchester united",
    "liverpool", "arsenal", "chelsea", "tottenham", "juventus",
    "ac milan", "inter milan", "bayern", "psg", "everton", "dortmund",
]

async def post_big_match_hype(bot: Bot):
    """
    Before big games — hype post that drives shares.
    Posted at 5PM on match days.
    """
    global _posted_big_match_ids
    data = await get_todays_matches()
    matches = data.get("matches", [])

    for m in matches:
        match_id = str(m.get("id", ""))
        if match_id in _posted_big_match_ids:
            continue

        home = m["homeTeam"].get("name", "?").lower()
        away = m["awayTeam"].get("name", "?").lower()
        home_short = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
        away_short = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
        comp = m.get("competition", {}).get("name", "")
        utc = m.get("utcDate", "")

        is_big = any(t in home or t in away for t in BIG_MATCH_TEAMS)
        is_ucl = "champions" in comp.lower() or "europa" in comp.lower()

        if not (is_big or is_ucl):
            continue

        try:
            dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
            t = dt.strftime("%H:%M UTC")
        except Exception:
            t = "TBD"

        # Special rivalry names
        match_title = f"{home_short} vs {away_short}"
        combined = f"{home} {away}"
        if "real madrid" in combined and "barcelona" in combined:
            match_title = "🔥 El Clásico — Real Madrid vs Barcelona"
        elif "manchester city" in combined and "manchester united" in combined:
            match_title = "🔥 Manchester Derby"
        elif "arsenal" in combined and "tottenham" in combined:
            match_title = "🔥 North London Derby"
        elif "liverpool" in combined and "everton" in combined:
            match_title = "🔥 Merseyside Derby"

        text = (
            f"🚨 *TONIGHT'S BIG MATCH*\n\n"
            f"*{match_title}*\n"
            f"_{comp}_\n"
            f"⏰ Kick-off: *{t}*\n\n"
            f"Who wins this? 👇\n\n"
            f"📺 Watch live:\n"
            f"• [SuperSport]({STREAM_1})\n"
            f"• [Sporty]({STREAM_2})\n\n"
            f"🎯 Predict the score: {BOT_LINK}"
            f"{affiliate_line()}"
            f"{forward_prompt()}"
        )
        await post(bot, text)
        _posted_big_match_ids.add(match_id)
        await asyncio.sleep(3)


# ─── DAILY FIXTURES (retention engine) ───────────────────────────────────────
async def post_daily_fixtures_viral(bot: Bot):
    """
    Every morning — today's fixtures.
    Clean, readable, shareable.
    """
    data = await get_todays_matches()
    matches = data.get("matches", [])
    now = datetime.now()

    if not matches:
        text = (
            f"📅 *{now.strftime('%A %d %B')}*\n\n"
            f"No matches today — rest day! ⚽\n\n"
            f"Tomorrow's fixtures coming soon.\n"
            f"🔔 Stay tuned: {CHANNEL_LINK}"
        )
        await post(bot, text)
        return

    # Group by league
    by_comp = {}
    for m in matches:
        comp = m.get("competition", {}).get("name", "Other")
        if comp not in by_comp:
            by_comp[comp] = []
        by_comp[comp].append(m)

    lines = [
        f"📅 *TODAY'S MATCHES*",
        f"_{now.strftime('%A %d %B %Y')}_\n",
    ]

    for comp, comp_matches in list(by_comp.items())[:6]:
        lines.append(f"🏆 *{comp}*")
        for m in comp_matches[:5]:
            home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
            away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
            utc = m.get("utcDate", "")
            try:
                dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
                t = dt.strftime("%H:%M")
            except Exception:
                t = "TBD"
            lines.append(f"   ⚽ {home} vs {away}  |  {t} UTC")
        lines.append("")

    lines.append(f"🔴 *Live updates during matches here!*")
    lines.append(f"🎯 Predictions: {BOT_LINK}")
    lines.append(forward_prompt())

    await post(bot, "\n".join(lines))


# ─── LIVE SCORE SNAPSHOT ─────────────────────────────────────────────────────
async def post_live_snapshot(bot: Bot):
    """
    Full live score board — posted every 10 mins during match hours.
    Clean and fast.
    """
    data = await get_live_scores()
    matches = data.get("matches", [])
    if not matches:
        return

    lines = [f"🔴 *LIVE NOW — {datetime.now().strftime('%H:%M')}*\n"]
    for m in matches[:10]:
        home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
        away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
        score = m.get("score", {}).get("fullTime", {})
        h = score.get("home", 0) or 0
        a = score.get("away", 0) or 0
        minute = m.get("minute", "")
        min_str = f"⏱{minute}'" if minute else "🔴"
        lines.append(f"`{home}  {h}–{a}  {away}` {min_str}")

    lines.append(f"\n📊 Full stats & predictions: {BOT_LINK}")
    await post(bot, "\n".join(lines))


# ─── CONSISTENCY REMINDER (internal use) ─────────────────────────────────────
async def post_no_matches_filler(bot: Bot):
    """
    On quiet days — keep channel active with football content.
    """
    from datetime import datetime
    day = datetime.now().weekday()

    fillers = [
        (
            f"⚽ *FOOTBALL FACT OF THE DAY*\n\n"
            f"Did you know? Lionel Messi has scored more goals than any player in football history.\n\n"
            f"🤖 Ask our AI anything: {BOT_LINK}/ask"
        ),
        (
            f"🏆 *THIS WEEK IN FOOTBALL*\n\n"
            f"Big matches coming up this week across EPL, UCL, La Liga and more.\n\n"
            f"📅 Today's fixtures: {BOT_LINK}/matches"
        ),
        (
            f"🧠 *FOOTBALL QUIZ*\n\n"
            f"Who holds the record for most UCL goals?\n\n"
            f"A) Ronaldo\n"
            f"B) Messi\n"
            f"C) Raul\n"
            f"D) Benzema\n\n"
            f"💬 Reply with your answer!\n"
            f"✅ Answer in 2 hours."
        ),
    ]

    text = fillers[day % len(fillers)]
    await post(bot, text)
