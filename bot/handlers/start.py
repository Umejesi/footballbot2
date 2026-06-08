from telegram import Update
from telegram.ext import ContextTypes
from db.crud import get_or_create_user, apply_referral, get_referral_by_code


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = ctx.args

    user_obj, is_new = get_or_create_user(
        telegram_id=user.id,
        first_name=user.first_name or "",
        username=user.username or "",
    )

    # Handle referral link
    if is_new and args:
        ref_code = args[0]
        referrer = get_referral_by_code(ref_code)
        if referrer and referrer.telegram_id != user.id:
            apply_referral(user.id, referrer.telegram_id)
            try:
                await ctx.bot.send_message(
                    chat_id=referrer.telegram_id,
                    text=f"🎉 *{user.first_name}* joined using your referral link!\n+100 points added!",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    if is_new:
        msg = (
            f"⚽ *Welcome to FootballAI Bot, {user.first_name}!*\n\n"
            f"🎁 You've received *50 welcome points!*\n\n"
            f"Here's what I can do:\n\n"
            f"📡 *Live & Fixtures*\n"
            f"/live — Live scores right now\n"
            f"/matches — Today's fixtures\n"
            f"/table — League standings\n"
            f"/topscorers — Golden boot race\n\n"
            f"🤖 *AI Features*\n"
            f"/ask [question] — Ask Football AI anything\n"
            f"/preview [Home] vs [Away] — Match preview\n"
            f"/compare [Team1] vs [Team2] — Compare teams\n\n"
            f"🎯 *Predictions & Rewards*\n"
            f"/predict [Home] [Score] [Away] — Lock in a prediction\n"
            f"/leaderboard — Top predictors\n"
            f"/checkin — Daily bonus points\n"
            f"/rewards — Your points & referral link\n\n"
            f"/help — Full command list"
        )
    else:
        msg = (
            f"Welcome back, *{user.first_name}!* ⚽\n\n"
            f"You have *{user_obj.points} points*.\n"
            f"Use /help to see all commands."
        )

    await update.message.reply_text(msg, parse_mode="Markdown")
