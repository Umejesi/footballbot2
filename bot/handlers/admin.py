import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.channel import (
    post_daily_tip, post_transfer_news, post_weekend_predictions,
    post_trivia, post_top_scorers, post_league_table, post_motivation,
)
from bot.phase1 import (
    post_live_feed, post_daily_fixtures, post_big_match_alerts,
    post_match_insights, post_vip_teaser, post_stream_links,
)

ADMIN_ID = int(os.getenv("ADMIN_ID", "0") if os.getenv("ADMIN_ID", "0").isdigit() else "0")


def is_admin(user_id: int) -> bool:
    return ADMIN_ID > 0 and user_id == ADMIN_ID


async def post_now(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    post_type = " ".join(ctx.args).lower() if ctx.args else ""
    bot = ctx.bot

    post_map = {
        "live": (post_live_feed, "Live scores"),
        "fixtures": (post_daily_fixtures, "Daily fixtures"),
        "bigmatch": (post_big_match_alerts, "Big match alerts"),
        "insight": (post_match_insights, "Match insights"),
        "stream": (post_stream_links, "Stream links"),
        "vip": (post_vip_teaser, "VIP teaser"),
        "tip": (post_daily_tip, "Daily tip"),
        "transfer": (post_transfer_news, "Transfer news"),
        "predictions": (post_weekend_predictions, "Weekend predictions"),
        "trivia": (post_trivia, "Trivia"),
        "scorers": (post_top_scorers, "Top scorers"),
        "table": (post_league_table, "League table"),
        "motivation": (post_motivation, "Motivation"),
    }

    if not post_type or post_type not in post_map:
        options = "\n".join([f"  /postnow {k}" for k in post_map])
        await update.message.reply_text(f"Usage: /postnow [type]\n\n{options}")
        return

    func, name = post_map[post_type]
    await update.message.reply_text(f"📤 Posting {name}...")
    await func(bot)
    await update.message.reply_text(f"✅ Done!")


async def broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /broadcast Your message")
        return
    channel_id = os.getenv("CHANNEL_ID", "")
    if not channel_id:
        await update.message.reply_text("❌ CHANNEL_ID not set.")
        return
    await ctx.bot.send_message(chat_id=channel_id, text=" ".join(ctx.args), parse_mode="Markdown")
    await update.message.reply_text("✅ Sent!")


async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return
    from db.models import Session, User, Prediction
    import sqlalchemy
    session = Session()
    total_users = session.query(User).count()
    total_preds = session.query(Prediction).count()
    total_points = session.query(sqlalchemy.func.sum(User.points)).scalar() or 0
    session.close()
    await update.message.reply_text(
        f"📊 *Bot Stats*\n\n"
        f"👥 Users: *{total_users:,}*\n"
        f"🎯 Predictions: *{total_preds:,}*\n"
        f"🏆 Points awarded: *{total_points:,}*",
        parse_mode="Markdown"
    )
