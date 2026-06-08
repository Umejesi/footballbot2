from telegram import Update
from telegram.ext import ContextTypes


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *FootballAI Bot — All Commands*\n\n"
        "━━━━━ 📡 LIVE DATA ━━━━━\n"
        "/live — Live scores right now\n"
        "/matches — Today's fixtures\n"
        "/table [league] — League standings\n"
        "/topscorers [league] — Top goal scorers\n\n"
        "━━━━━ 🤖 AI FEATURES ━━━━━\n"
        "/ask [question] — Ask Football AI\n"
        "/preview [Home] vs [Away] — Match preview\n"
        "/compare [Team1] vs [Team2] — Compare teams\n\n"
        "━━━━━ 🎯 PREDICTIONS ━━━━━\n"
        "/predict [Home] [Score] [Away]\n"
        "  Example: /predict Arsenal 2-1 Chelsea\n"
        "/leaderboard — Top predictors\n\n"
        "━━━━━ 💰 REWARDS ━━━━━\n"
        "/checkin — Daily bonus points\n"
        "/rewards — Points balance & referral link\n\n"
        "━━━━━ LEAGUE SHORTCUTS ━━━━━\n"
        "Use with /table or /topscorers:\n"
        "`pl` Premier League\n"
        "`ucl` Champions League\n"
        "`laliga` La Liga\n"
        "`seriea` Serie A\n"
        "`bundesliga` Bundesliga\n\n"
        "_Example: /table laliga_",
        parse_mode="Markdown",
    )
