"""
Channel Manager — handles all automatic posts to @FOOTBALLAIOFFICIAL
"""
import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from api.football import (
    get_live_scores, get_todays_matches, get_standings,
    get_top_scorers, format_live_scores, format_todays_matches,
    format_standings, format_top_scorers
)
from ai.chat import ask_football_ai, generate_match_preview

logger = logging.getLogger(__name__)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@FOOTBALLAIOFFICIAL")
BOT_LINK = "https://t.me/PitchMasterAIBot"


async def post_to_channel(bot: Bot, text: str, parse_mode: str = "Markdown"):
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode=parse_mode)
        logger.info(f"Posted to channel: {text[:60]}...")
    except TelegramError as e:
        logger.error(f"Channel post failed: {e}")


async def post_morning_show(bot: Bot):
    data = await get_todays_matches()
    fixtures = format_todays_matches(data)
    matches = data.get("matches", [])
    now = datetime.now()

    greeting = (
        f"🌅 *GOOD MORNING FOOTBALL FANS!*\n"
        f"_{now.strftime('%A, %B %d %Y')}_\n\n"
    )
    if not matches:
        text = greeting + "No matches today — enjoy the rest day! ⚽\n\n📲 Bot: " + BOT_LINK
    else:
        text = (
            greeting + fixtures +
            f"\n\n🎯 *Make your predictions:* {BOT_LINK}\n"
            f"_Turn on notifications so you never miss a goal!_"
        )
    await post_to_channel(bot, text)


async def post_live_scores(bot: Bot):
    data = await get_live_scores()
    matches = data.get("matches", [])
    if not matches:
        return
    text = format_live_scores(data)
    text += f"\n\n💬 *Predict the final score:*\n{BOT_LINK}"
    await post_to_channel(bot, text)


async def post_match_previews(bot: Bot):
    data = await get_todays_matches()
    matches = data.get("matches", [])
    if not matches:
        return

    for match in matches[:3]:
        home = match["homeTeam"].get("shortName") or match["homeTeam"].get("name", "?")
        away = match["awayTeam"].get("shortName") or match["awayTeam"].get("name", "?")
        comp = match.get("competition", {}).get("name", "")
        preview = await generate_match_preview(home, away)
        text = (
            f"📋 *MATCH PREVIEW*\n"
            f"_{comp}_\n\n"
            f"*{home} vs {away}*\n\n"
            f"{preview}\n\n"
            f"🎯 *Lock in your prediction:*\n{BOT_LINK}"
        )
        await post_to_channel(bot, text)
        await asyncio.sleep(3)


async def post_league_table(bot: Bot, league: str = "pl"):
    data = await get_standings(league)
    text = format_standings(data)
    text += f"\n\n📊 _Updated standings — who's your team?_\n{BOT_LINK}"
    await post_to_channel(bot, text)


async def post_top_scorers(bot: Bot, league: str = "pl"):
    data = await get_top_scorers(league)
    text = format_top_scorers(data)
    text += f"\n\n⚽ _Who wins the golden boot this season?_\n{BOT_LINK}"
    await post_to_channel(bot, text)


async def post_daily_tip(bot: Bot):
    tips_prompts = [
        "Give one sharp football prediction tip for today based on current form. Be specific about a real match. Under 100 words. End with: Not financial advice.",
        "Share one fascinating football stat or fact that fans would find surprising. Be specific with numbers.",
        "Give a top FPL (Fantasy Premier League) tip for this week — who to captain or transfer in and why.",
        "Share a tactical insight about a top team's recent performances. What are they doing differently?",
        "Predict which player will have a standout performance this weekend and give 2 reasons why.",
    ]
    day = datetime.now().weekday()
    prompt = tips_prompts[day % len(tips_prompts)]
    tip = await ask_football_ai(prompt)
    emojis = ["💡", "📊", "🎯", "⚡", "🔥", "🧠", "⚽"]
    emoji = emojis[day % len(emojis)]
    text = (
        f"{emoji} *DAILY FOOTBALL TIP*\n"
        f"_{datetime.now().strftime('%A %d %B')}_\n\n"
        f"{tip}\n\n"
        f"🤖 *More AI analysis:* {BOT_LINK}"
    )
    await post_to_channel(bot, text)


async def post_weekend_predictions(bot: Bot):
    data = await get_todays_matches()
    matches = data.get("matches", [])

    if not matches:
        text = (
            "🔮 *WEEKEND PREDICTIONS*\n\n"
            "Ask our AI for predictions on any match!\n\n"
            f"👇 {BOT_LINK}\n"
            "/ask predict [Home] vs [Away]"
        )
        await post_to_channel(bot, text)
        return

    prompt = "Give confident predictions for these matches: "
    prompt += ", ".join([
        f"{m['homeTeam'].get('shortName','?')} vs {m['awayTeam'].get('shortName','?')}"
        for m in matches[:5]
    ])
    prompt += ". For each give a scoreline and one-line reason. Under 200 words total."

    predictions = await ask_football_ai(prompt)
    text = (
        f"🔮 *WEEKEND PREDICTIONS*\n"
        f"_{datetime.now().strftime('%A %d %B')}_\n\n"
        f"{predictions}\n\n"
        f"⚠️ _For entertainment only. Not financial advice._\n\n"
        f"🎯 *Your prediction:* {BOT_LINK}"
    )
    await post_to_channel(bot, text)


async def post_trivia(bot: Bot):
    prompt = """Create one football trivia question with 4 multiple choice options (A, B, C, D).
Format exactly like this:
🧠 TRIVIA TIME!

[Question here]

A) Option one
B) Option two
C) Option three
D) Option four

💬 Reply with your answer!
✅ Answer revealed in 2 hours."""
    trivia = await ask_football_ai(prompt)
    await post_to_channel(bot, trivia)


async def post_transfer_news(bot: Bot):
    prompt = """Give a transfer news roundup for today. Include 2-3 current transfer rumours or confirmed moves with clubs involved and likelihood. Keep under 200 words. Be specific about real clubs and players."""
    news = await ask_football_ai(prompt)
    text = (
        f"📰 *TRANSFER NEWS ROUNDUP*\n"
        f"_{datetime.now().strftime('%A %d %B')}_\n\n"
        f"{news}\n\n"
        f"💬 _What do you think about these deals?_"
    )
    await post_to_channel(bot, text)


async def post_motivation(bot: Bot):
    prompt = """Share an iconic football quote from a manager or player, then write 2 sentences about why it's relevant to football fans today. Keep it inspiring and under 80 words."""
    quote = await ask_football_ai(prompt)
    text = (
        f"💬 *FOOTBALL WISDOM*\n\n"
        f"{quote}\n\n"
        f"⚽ _Tag a friend who needs to hear this!_"
    )
    await post_to_channel(bot, text)
