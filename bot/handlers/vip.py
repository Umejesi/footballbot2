from telegram import Update
from telegram.ext import ContextTypes
from db.crud import get_or_create_user, add_points


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.first_name or "", user.username or "")
    add_points(user.id, 10, "vip_interest")

    await update.message.reply_text(
        f"💎 *VIP Waitlist*\n\n"
        f"You're registered, {user.first_name}!\n\n"
        f"You'll be among the first to access:\n"
        f"• Deep match analysis\n"
        f"• Early predictions\n"
        f"• Exclusive team news\n"
        f"• Priority AI access\n\n"
        f"🎁 *+10 points* added for your interest!\n\n"
        f"_We'll notify you when VIP launches._",
        parse_mode="Markdown"
    )
