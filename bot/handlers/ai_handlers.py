from telegram import Update
from telegram.ext import ContextTypes
from ai.chat import ask_football_ai, generate_match_preview, compare_teams
from db.crud import get_or_create_user


async def ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.first_name or "", user.username or "")

    question = " ".join(ctx.args) if ctx.args else ""
    if not question:
        await update.message.reply_text(
            "Ask me anything! Examples:\n\n"
            "/ask Who will win the Premier League?\n"
            "/ask Is Haaland better than Mbappe?\n"
            "/ask Predict Arsenal vs Chelsea\n"
            "/ask Best XI of 2024?"
        )
        return

    await update.message.chat.send_action("typing")
    answer = await ask_football_ai(question, telegram_id=user.id)
    await update.message.reply_text(f"🤖 *Football AI*\n\n{answer}", parse_mode="Markdown")


async def preview(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or "vs" not in " ".join(ctx.args).lower():
        await update.message.reply_text(
            "Usage: /preview [Home] vs [Away]\n"
            "Example: /preview Arsenal vs Chelsea"
        )
        return

    full = " ".join(ctx.args)
    parts = full.lower().split("vs")
    home = parts[0].strip().title()
    away = parts[1].strip().title() if len(parts) > 1 else "Opponent"

    await update.message.chat.send_action("typing")
    text = await generate_match_preview(home, away)
    await update.message.reply_text(
        f"📋 *Match Preview*\n_{home} vs {away}_\n\n{text}",
        parse_mode="Markdown",
    )


async def compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args or "vs" not in " ".join(ctx.args).lower():
        await update.message.reply_text(
            "Usage: /compare [Team1] vs [Team2]\n"
            "Example: /compare Man City vs Real Madrid"
        )
        return

    full = " ".join(ctx.args)
    parts = full.lower().split("vs")
    team1 = parts[0].strip().title()
    team2 = parts[1].strip().title() if len(parts) > 1 else "Opponent"

    await update.message.chat.send_action("typing")
    text = await compare_teams(team1, team2)
    await update.message.reply_text(
        f"⚖️ *Team Comparison*\n_{team1} vs {team2}_\n\n{text}",
        parse_mode="Markdown",
    )
