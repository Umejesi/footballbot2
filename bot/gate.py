"""
Gate — wraps any command handler with a subscription check.
Usage in main.py: app.add_handler(CommandHandler("live", gate(live_handle)))
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from bot.middleware import is_subscribed, subscription_keyboard, subscription_message


def gate(func):
    """Decorator that checks channel subscription before running any handler."""
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user:
            return

        subscribed = await is_subscribed(ctx.bot, user.id)
        if not subscribed:
            await update.message.reply_text(
                subscription_message(user.first_name or "there"),
                reply_markup=subscription_keyboard(),
            )
            return

        return await func(update, ctx)
    return wrapper
