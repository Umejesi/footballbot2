from telegram import Update
from telegram.ext import ContextTypes
from api.football import get_top_scorers, format_top_scorers

LEAGUE_ALIASES = {
    "pl": "pl", "premier": "pl", "epl": "pl",
    "ucl": "ucl", "champions": "ucl",
    "laliga": "laliga", "la liga": "laliga",
    "seriea": "seriea", "serie a": "seriea",
    "bundesliga": "bundesliga",
}


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    league_key = "pl"
    if ctx.args:
        raw = " ".join(ctx.args).lower()
        league_key = LEAGUE_ALIASES.get(raw, raw)

    data = await get_top_scorers(league_key)
    text = format_top_scorers(data)
    await update.message.reply_text(text, parse_mode="Markdown")
