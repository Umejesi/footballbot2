from telegram import Update
from telegram.ext import ContextTypes
from api.football import get_live_scores, format_live_scores


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    data = await get_live_scores()
    text = format_live_scores(data)
    await update.message.reply_text(text, parse_mode="Markdown")
