from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.subscription import is_subscribed, send_join_prompt


def require_subscription(handler):
    """Decorator that checks channel subscription before running any handler."""
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return
        subscribed = await is_subscribed(ctx.bot, update.effective_user.id)
        if not subscribed:
            await send_join_prompt(update)
            return
        return await handler(update, ctx)
    wrapper.__name__ = handler.__name__
    return wrapper
