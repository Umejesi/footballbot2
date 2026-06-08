"""
Subscription gate — checks if user has joined @FOOTBALLAIOFFICIAL
before they can use any bot feature. Done in a calm, friendly way.
"""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError

CHANNEL_ID = os.getenv("CHANNEL_ID", "@FOOTBALLAIOFFICIAL")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "FOOTBALLAIOFFICIAL")
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME}"


async def is_subscribed(bot, user_id: int) -> bool:
    """Check if user is a member of the channel."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramError:
        return True  # If check fails, don't block the user


async def send_join_prompt(update: Update):
    """Send a calm, friendly prompt to join the channel."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 Join FootballAI Official", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ I've Joined — Let Me In", callback_data="check_subscription")],
    ])

    await update.message.reply_text(
        "Hey! Just one small thing before we get started. 👋\n\n"
        "We have a channel where we post live scores, match previews, "
        "daily tips, transfer news, and predictions — everything a football fan loves.\n\n"
        "Join the channel first, then come right back. "
        "It only takes a second! ⚽\n\n"
        "Once you're in, tap *I've Joined* below and everything unlocks.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def check_subscription_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handles the 'I've Joined' button tap."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    name = query.from_user.first_name or "champ"
    subscribed = await is_subscribed(ctx.bot, user_id)

    if subscribed:
        await query.edit_message_text(
            f"You're all set, {name}! Welcome to FootballAI ⚽🔥\n\n"
            "Here's what you can do:\n\n"
            "📡 /live — Live scores right now\n"
            "📅 /matches — Today's fixtures\n"
            "📊 /table — League standings\n"
            "⚽ /topscorers — Golden boot race\n"
            "🤖 /ask — Ask Football AI anything\n"
            "🔮 /preview — AI match preview\n"
            "⚖️ /compare — Compare two teams\n"
            "🎯 /predict — Lock in a prediction\n"
            "🏆 /leaderboard — Top predictors\n"
            "✅ /checkin — Daily bonus points\n"
            "💰 /rewards — Your points & referral link\n\n"
            "Or just type any football question and I'll answer. Let's go! 🚀"
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📣 Join FootballAI Official", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I've Joined — Let Me In", callback_data="check_subscription")],
        ])
        await query.edit_message_text(
            f"Hmm, looks like you haven't joined yet, {name}.\n\n"
            "No worries — just tap the button below, join the channel, "
            "then come back and tap *I've Joined*. Takes about 3 seconds! ⚽",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
