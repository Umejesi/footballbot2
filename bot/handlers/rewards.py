from telegram import Update
from telegram.ext import ContextTypes
from db.crud import get_or_create_user, get_user, do_checkin


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_obj, _ = get_or_create_user(user.id, user.first_name or "", user.username or "")
    user_obj = get_user(user.id)

    ref_link = f"https://t.me/PitchMasterAIBot?start={user_obj.referral_code}"

    await update.message.reply_text(
        f"💰 *Your Rewards Dashboard*\n\n"
        f"👤 *{user.first_name}*\n"
        f"🏆 Points: *{user_obj.points:,} pts*\n"
        f"🔥 Daily streak: *{user_obj.streak} days*\n\n"
        f"*How to earn more:*\n"
        f"✅ /checkin — Daily bonus (up to 30 pts)\n"
        f"⚽ /predict correct score — 50 pts\n"
        f"🏅 Correct winner — 20 pts\n"
        f"👥 Refer a friend — 100 pts\n"
        f"📚 Quiz correct answer — 10 pts\n\n"
        f"*Your referral link:*\n"
        f"`{ref_link}`\n\n"
        f"_Share this link — you earn 100 pts for every friend who joins!_",
        parse_mode="Markdown",
    )


async def checkin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.first_name or "", user.username or "")

    pts, streak, already = do_checkin(user.id)

    if already:
        await update.message.reply_text(
            "✅ Already checked in today!\n\n"
            f"Current streak: *{streak} days* 🔥\n"
            "Come back tomorrow for more points!",
            parse_mode="Markdown",
        )
        return

    streak_msg = f"🔥 *{streak}-day streak!*" if streak > 1 else "Day 1 — keep it going!"
    next_pts = min(5 + streak * 5, 30)
    await update.message.reply_text(
        f"✅ *Check-in complete!*\n\n"
        f"+{pts} points added!\n"
        f"{streak_msg}\n\n"
        f"Come back tomorrow for *{next_pts} pts!*\n"
        f"Use /rewards to see your balance.",
        parse_mode="Markdown",
    )
