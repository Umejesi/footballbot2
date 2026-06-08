from telegram import Update
from telegram.ext import ContextTypes
from api.football import get_standings, format_standings

LEAGUE_ALIASES = {
    "pl": "pl", "premier": "pl", "premier league": "pl", "epl": "pl",
    "ucl": "ucl", "champions": "ucl", "champions league": "ucl", "cl": "ucl",
    "laliga": "laliga", "la liga": "laliga", "spain": "laliga",
    "seriea": "seriea", "serie a": "seriea", "italy": "seriea",
    "bundesliga": "bundesliga", "germany": "bundesliga", "bl": "bundesliga",
    "ligue1": "ligue1", "ligue 1": "ligue1", "france": "ligue1",
}


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    league_key = "pl"
    if ctx.args:
        raw = " ".join(ctx.args).lower()
        league_key = LEAGUE_ALIASES.get(raw, raw)

    data = await get_standings(league_key)
    text = format_standings(data)
    await update.message.reply_text(text, parse_mode="Markdown")
