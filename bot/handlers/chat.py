from telegram import Update
from telegram.ext import ContextTypes
from ai.chat import ask_football_ai
from db.crud import get_or_create_user

GREETINGS = ["hi", "hello", "hey", "sup", "yo", "hiya", "good morning",
             "good afternoon", "good evening", "what's up", "whats up"]
THANKS = ["thanks", "thank you", "thank u", "thx", "appreciated", "nice one"]
GOODBYES = ["bye", "goodbye", "later", "see you", "cya", "take care"]
ABOUT = ["what can you do", "what are you", "who are you", "what is this", "how does this work"]
FOOTBALL_WORDS = [
    "predict", "who will win", "best player", "transfer", "match", "goal",
    "premier league", "champions league", "la liga", "serie a", "bundesliga",
    "arsenal", "chelsea", "liverpool", "manchester", "barcelona", "real madrid",
    "messi", "ronaldo", "haaland", "mbappe", "fixture", "score", "table",
    "standings", "injury", "lineup", "formation", "tactics", "manager", "coach",
    "referee", "penalty", "football", "soccer", "ucl", "epl", "fifa", "ballon",
    "wrong", "actually", "correct", "my team", "i support", "favourite",
]


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    get_or_create_user(user.id, user.first_name or "", user.username or "")
    text = update.message.text.lower().strip()
    name = user.first_name or "champ"

    # Greetings
    if any(text == g or text.startswith(g) for g in GREETINGS):
        await update.message.reply_text(
            f"Hey {name}! ⚽\n\n"
            f"I'm *FootballAI Bot* — your personal football assistant!\n\n"
            f"Ask me anything:\n"
            f"• _Who will win the Champions League?_\n"
            f"• _Predict Arsenal vs Chelsea_\n"
            f"• _Best striker right now?_\n\n"
            f"Or use /help to see all commands 👇",
            parse_mode="Markdown",
        )
        return

    # Thanks
    if any(t in text for t in THANKS):
        await update.message.reply_text(
            f"You're welcome {name}! ⚽\nAlways here for football talk!"
        )
        return

    # Goodbyes
    if any(text == g or text.startswith(g) for g in GOODBYES):
        await update.message.reply_text(
            f"Later {name}! ⚽ Come back anytime! 🔥"
        )
        return

    # About
    if any(a in text for a in ABOUT):
        await update.message.reply_text(
            f"I'm *FootballAI Bot* ⚽🤖\n\n"
            f"📡 /live — Live scores\n"
            f"📅 /matches — Today's fixtures\n"
            f"📊 /table — League standings\n"
            f"⚽ /topscorers — Top scorers\n"
            f"🤖 /ask — Ask AI anything\n"
            f"🔮 /preview — Match preview\n"
            f"⚖️ /compare — Compare teams\n"
            f"🎯 /predict — Make a prediction\n"
            f"💰 /rewards — Your points\n"
            f"✅ /checkin — Daily bonus\n\n"
            f"Just type any football question! 🔥",
            parse_mode="Markdown",
        )
        return

    # Football questions or anything with ? — send to AI with user ID for memory
    if any(word in text for word in FOOTBALL_WORDS) or "?" in text or len(text) > 15:
        await update.message.chat.send_action("typing")
        answer = await ask_football_ai(update.message.text, telegram_id=user.id)
        await update.message.reply_text(f"🤖 {answer}", parse_mode="Markdown")
        return

    # Fallback
    await update.message.reply_text(
        f"⚽ Ask me a football question, {name}!\n\n"
        f"Example: _Who will win the Premier League?_\n"
        f"Or use /help to see all commands.",
        parse_mode="Markdown",
    )
