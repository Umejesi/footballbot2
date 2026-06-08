from telegram import Update
from telegram.ext import ContextTypes
from db.crud import save_prediction, get_leaderboard, get_or_create_user


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.first_name or "", user.username or "")

    if not ctx.args or len(ctx.args) < 3:
        await update.message.reply_text(
            "How to make a prediction:\n\n"
            "/predict [Home Team] [Score] [Away Team]\n\n"
            "*Examples:*\n"
            "/predict Arsenal 2-1 Chelsea\n"
            "/predict ManCity 0-0 Liverpool\n\n"
            "✅ Correct scoreline = *50 points*\n"
            "✅ Correct winner = *20 points*\n"
            "✅ Correct draw = *10 points*",
            parse_mode="Markdown",
        )
        return

    # Find the score part (contains a dash between two numbers)
    args = ctx.args
    score_idx = None
    for i, part in enumerate(args):
        if "-" in part and part.replace("-", "").isdigit():
            score_idx = i
            break

    if score_idx is None:
        await update.message.reply_text(
            "I couldn't read that score. Use format like: *2-1*\n\n"
            "Example: /predict Arsenal *2-1* Chelsea",
            parse_mode="Markdown",
        )
        return

    home_team = " ".join(args[:score_idx])
    score_str = args[score_idx]
    away_team = " ".join(args[score_idx + 1:])

    if not home_team or not away_team:
        await update.message.reply_text("Please include both team names.\nExample: /predict Arsenal 2-1 Chelsea")
        return

    try:
        home_goals, away_goals = map(int, score_str.split("-"))
    except ValueError:
        await update.message.reply_text("Score must be like 2-1 or 0-0.")
        return

    pred_id = save_prediction(user.id, home_team, away_team, home_goals, away_goals)

    result_emoji = "⚽" if home_goals != away_goals else "🤝"
    await update.message.reply_text(
        f"{result_emoji} *Prediction locked!*\n\n"
        f"*{home_team.title()} {home_goals} - {away_goals} {away_team.title()}*\n\n"
        f"Prediction #{pred_id} saved.\n"
        f"Points are awarded automatically after the match.\n\n"
        f"Good luck! 🍀",
        parse_mode="Markdown",
    )


async def leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = get_leaderboard(10)
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    lines = ["🏆 *TOP PREDICTORS*\n"]
    for i, (name, pts) in enumerate(rows):
        lines.append(f"{medals[i]} *{name}* — {pts:,} pts")

    if not rows:
        lines.append("No players yet. Be the first — use /predict!")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
