from telegram import Update
from telegram.ext import ContextTypes
from api.football import (
    get_todays_matches, get_tomorrows_matches, get_this_week_matches,
    format_todays_matches, format_tomorrows_matches, format_week_matches
)


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    data = await get_todays_matches()
    text = format_todays_matches(data)
    await update.message.reply_text(text, parse_mode="Markdown")


async def tomorrow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    data = await get_tomorrows_matches()
    text = format_tomorrows_matches(data)
    await update.message.reply_text(text, parse_mode="Markdown")


async def week(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    data = await get_this_week_matches()
    text = format_week_matches(data)
    await update.message.reply_text(text, parse_mode="Markdown")
