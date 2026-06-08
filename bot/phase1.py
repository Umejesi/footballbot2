"""
Phase 1 — The Foundation
Reliable football news source that builds habit, trust and retention.
"""
import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from api.football import (
    get_live_scores, get_todays_matches, get_standings,
    format_live_scores, format_todays_matches
)
from ai.chat import generate_match_insight

logger = logging.getLogger(__name__)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@FOOTBALLAIOFFICIAL")
BOT_LINK = "https://t.me/PitchMasterAIBot"

# ── Streaming links ──────────────────────────────────────────────────────────
STREAM_LINK_1 = "https://supersport.com/"
STREAM_LINK_2 = "https://sporty.com/"

# ── Affiliate link (add your 1xBet link here when ready) ────────────────────
AFFILIATE_LINK = os.getenv("AFFILIATE_LINK", "https://reffpa.com/L?tag=d_5683483m_97c_&site=5683483&ad=97")  # Set in Railway variables

# Big match keywords
BIG_MATCH_KEYWORDS = [
    "real madrid", "barcelona", "manchester", "liverpool", "arsenal",
    "chelsea", "juventus", "milan", "bayern", "psg", "el clasico",
    "derby", "champions league", "ucl", "europa", "tottenham", "everton",
]


async def post(bot: Bot, text: str):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")
    except TelegramError as e:
        logger.error(f"Post failed: {e}")


async def is_big_match(home: str, away: str) -> bool:
    combined = f"{home} {away}".lower()
    return any(kw in combined for kw in BIG_MATCH_KEYWORDS)


def get_affiliate_line() -> str:
    """Returns affiliate line if link is set, otherwise empty."""
    if AFFILIATE_LINK:
        return f"\n🎰 *Best odds:* [1xBet]({AFFILIATE_LINK}) — _18+ | Gamble responsibly_"
    return ""


# ─── 1. LIVE SCORE FEED ─────────────────────────────────────────────────────
async def post_live_feed(bot: Bot):
    data = await get_live_scores()
    matches = data.get("matches", [])
    if not matches:
        return

    lines = ["🔴 *LIVE SCORES*\n"]
    for m in matches[:12]:
        home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
        away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
        score = m.get("score", {}).get("fullTime", {})
        h = score.get("home", 0) or 0
        a = score.get("away", 0) or 0
        minute = m.get("minute", "")
        comp = m.get("competition", {}).get("name", "")
        min_str = f" ⏱{minute}'" if minute else ""
        lines.append(f"`{home}  {h} — {a}  {away}`{min_str}")
        if comp:
            lines.append(f"  _{comp}_\n")

    lines.append(f"\n🤖 *Predict the result:* {BOT_LINK}")
    await post(bot, "\n".join(lines))


# ─── 2. DAILY FIXTURES DROP ─────────────────────────────────────────────────
async def post_daily_fixtures(bot: Bot):
    data = await get_todays_matches()
    matches = data.get("matches", [])
    now = datetime.now()

    header = (
        f"📅 *TODAY'S FIXTURES*\n"
        f"_{now.strftime('%A %d %B %Y')}_\n\n"
    )

    if not matches:
        await post(bot, header + "No matches today. Rest day! ⚽")
        return

    lines = [header]
    by_comp = {}
    for m in matches:
        comp = m.get("competition", {}).get("name", "Other")
        if comp not in by_comp:
            by_comp[comp] = []
        by_comp[comp].append(m)

    for comp, comp_matches in list(by_comp.items())[:5]:
        lines.append(f"*{comp}*")
        for m in comp_matches[:4]:
            home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
            away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
            utc = m.get("utcDate", "")
            try:
                dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
                t = dt.strftime("%H:%M UTC")
            except Exception:
                t = "TBD"
            lines.append(f"  ⚽ {home} vs {away} — {t}")
        lines.append("")

    lines.append(f"🎯 *Make predictions:* {BOT_LINK}")
    await post(bot, "\n".join(lines))


# ─── 3. BIG MATCH ALERT ─────────────────────────────────────────────────────
async def post_big_match_alerts(bot: Bot):
    data = await get_todays_matches()
    matches = data.get("matches", [])

    for m in matches:
        home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
        away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
        comp = m.get("competition", {}).get("name", "")
        utc = m.get("utcDate", "")

        if not await is_big_match(home, away):
            continue

        try:
            dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
            t = dt.strftime("%H:%M UTC")
        except Exception:
            t = "TBD"

        match_name = f"{home} vs {away}"
        combined = f"{home} {away}".lower()
        if "real madrid" in combined and "barcelona" in combined:
            match_name = "⚡ El Clásico — Real Madrid vs Barcelona"
        elif "manchester" in combined and "city" in combined:
            match_name = "⚡ Manchester Derby"
        elif "arsenal" in combined and "tottenham" in combined:
            match_name = "⚡ North London Derby"
        elif "liverpool" in combined and "everton" in combined:
            match_name = "⚡ Merseyside Derby"

        text = (
            f"🚨 *BIG MATCH ALERT*\n\n"
            f"*{match_name}*\n"
            f"_{comp}_\n"
            f"⏰ Kick-off: *{t}*\n\n"
            f"Don't miss this one! 🔥"
            f"{get_affiliate_line()}\n\n"
            f"🎯 *Predict the score:* {BOT_LINK}"
        )
        await post(bot, text)
        await asyncio.sleep(2)


# ─── 4. MATCH INSIGHT ───────────────────────────────────────────────────────
async def post_match_insights(bot: Bot):
    data = await get_todays_matches()
    matches = data.get("matches", [])

    for m in matches[:3]:
        home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
        away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
        comp = m.get("competition", {}).get("name", "")

        insight = await generate_match_insight(home, away, stage="preview")

        text = (
            f"📊 *MATCH INSIGHT*\n"
            f"*{home} vs {away}*\n"
            f"_{comp}_\n\n"
            f"{insight}\n\n"
            f"_No guaranteed wins. Football is unpredictable._"
            f"{get_affiliate_line()}\n\n"
            f"🎯 {BOT_LINK}"
        )
        await post(bot, text)
        await asyncio.sleep(3)


# ─── 5. STREAMING LINKS ─────────────────────────────────────────────────────
async def post_stream_links(bot: Bot):
    data = await get_todays_matches()
    matches = data.get("matches", [])

    big_matches = []
    for m in matches:
        home = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
        away = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
        comp = m.get("competition", {}).get("name", "")
        utc = m.get("utcDate", "")
        try:
            dt = datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ")
            t = dt.strftime("%H:%M UTC")
        except Exception:
            t = "TBD"
        if await is_big_match(home, away):
            big_matches.append((home, away, comp, t))

    # Always post stream links even if no big matches today
    lines = ["📺 *WATCH LIVE FOOTBALL*\n"]

    if big_matches:
        lines.append("*Tonight's big matches:*")
        for home, away, comp, t in big_matches[:4]:
            lines.append(f"⚽ {home} vs {away} — {t}")
            lines.append(f"   _{comp}_\n")
    else:
        lines.append("Check today's fixtures with /matches\n")

    lines.append("*🔴 Stream live now:*")
    lines.append(f"• [SuperSport]({STREAM_LINK_1}) — Premium HD streams")
    lines.append(f"• [Sporty]({STREAM_LINK_2}) — Free live streams\n")
    lines.append("_If one link is offline, try the other. Use a VPN if blocked._")
    lines.append(f"\n🤖 Live scores: {BOT_LINK}")

    await post(bot, "\n".join(lines))


# ─── 6. VIP TEASER ──────────────────────────────────────────────────────────
async def post_vip_teaser(bot: Bot):
    text = (
        f"💎 *VIP INSIGHTS — Coming Soon*\n\n"
        f"We're building something for serious football fans:\n\n"
        f"• Deep match analysis before kickoff\n"
        f"• Early value picks before odds move\n"
        f"• Exclusive team & injury news\n"
        f"• Priority AI access\n\n"
        f"_No spam. No fake tips. Just smarter football._\n\n"
        f"📲 Register interest: {BOT_LINK}\n"
        f"Type /vip to join the waitlist."
    )
    await post(bot, text)
