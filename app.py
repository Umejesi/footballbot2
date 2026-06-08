import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import asyncio
from dotenv import load_dotenv
load_dotenv()

# ── Database ─────────────────────────────────────────────────────
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String, default="")
    username = Column(String, default="")
    points = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_checkin = Column(DateTime, nullable=True)
    referral_code = Column(String, unique=True, nullable=True)
    referred_by = Column(Integer, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)
    is_scored = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    role = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ── DB helpers ───────────────────────────────────────────────────
def get_or_create_user(telegram_id, first_name, username=""):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        session.close()
        return user, False
    code = str(uuid.uuid4())[:8].upper()
    user = User(telegram_id=telegram_id, first_name=first_name,
                username=username or "", points=50, referral_code=code)
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return user, True

def get_user(telegram_id):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user

def add_points(telegram_id, amount):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.points += amount
        session.commit()
    session.close()

def save_prediction(telegram_id, home_team, away_team, home_goals, away_goals):
    session = Session()
    pred = Prediction(telegram_id=telegram_id, home_team=home_team.title(),
                      away_team=away_team.title(), home_goals=home_goals, away_goals=away_goals)
    session.add(pred)
    session.commit()
    pred_id = pred.id
    session.close()
    return pred_id

def get_leaderboard(limit=10):
    session = Session()
    users = session.query(User).order_by(User.points.desc()).limit(limit).all()
    result = [(u.first_name or u.username or "Anonymous", u.points) for u in users]
    session.close()
    return result

def do_checkin(telegram_id):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        session.close()
        return 0, 0, False
    now = datetime.utcnow()
    if user.last_checkin:
        diff = now - user.last_checkin
        if diff < timedelta(hours=20):
            session.close()
            return 0, user.streak, True
        user.streak = user.streak + 1 if diff < timedelta(hours=36) else 1
    else:
        user.streak = 1
    pts = min(5 + (user.streak - 1) * 5, 30)
    user.points += pts
    user.last_checkin = now
    session.commit()
    streak = user.streak
    session.close()
    return pts, streak, False

def save_message(telegram_id, role, message):
    session = Session()
    try:
        msg = Conversation(telegram_id=telegram_id, role=role, message=message)
        session.add(msg)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

def get_history(telegram_id, limit=8):
    session = Session()
    try:
        msgs = session.query(Conversation).filter_by(telegram_id=telegram_id)\
            .order_by(Conversation.created_at.desc()).limit(limit).all()
        return list(reversed(msgs))
    except Exception:
        return []
    finally:
        session.close()

# ── Football API ─────────────────────────────────────────────────
import httpx

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
FOOTBALL_BASE = "https://api.football-data.org/v4"
FOOTBALL_HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}
LEAGUES = {"pl":2021,"ucl":2001,"laliga":2014,"seriea":2019,"bundesliga":2002,"ligue1":2015}

async def football_get(endpoint):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{FOOTBALL_BASE}{endpoint}", headers=FOOTBALL_HEADERS)
            return r.json()
        except Exception as e:
            return {"error": str(e), "matches": [], "standings": [], "scorers": []}

async def get_live_scores(): return await football_get("/matches?status=LIVE")
async def get_todays_matches():
    today = datetime.now().strftime("%Y-%m-%d")
    return await football_get(f"/matches?dateFrom={today}&dateTo={today}")
async def get_standings(league_key="pl"):
    return await football_get(f"/competitions/{LEAGUES.get(league_key.lower(),2021)}/standings")
async def get_top_scorers(league_key="pl"):
    return await football_get(f"/competitions/{LEAGUES.get(league_key.lower(),2021)}/scorers?limit=10")

def fmt_live(data):
    matches = data.get("matches", [])
    if not matches: return "No live matches right now.\nUse /matches for upcoming fixtures."
    lines = ["🔴 *LIVE SCORES*\n"]
    for m in matches[:10]:
        h = m["homeTeam"].get("shortName", m["homeTeam"].get("name","?"))
        a = m["awayTeam"].get("shortName", m["awayTeam"].get("name","?"))
        sc = m.get("score",{}).get("fullTime",{})
        hg = sc.get("home",0) or 0; ag = sc.get("away",0) or 0
        lines.append(f"`{h} {hg} - {ag} {a}`")
    return "\n".join(lines)

def fmt_matches(data):
    matches = data.get("matches",[])
    if not matches: return "No matches scheduled today."
    lines = ["📅 *TODAY'S FIXTURES*\n"]
    for m in matches[:15]:
        h = m["homeTeam"].get("shortName", m["homeTeam"].get("name","?"))
        a = m["awayTeam"].get("shortName", m["awayTeam"].get("name","?"))
        try:
            dt = datetime.strptime(m.get("utcDate",""), "%Y-%m-%dT%H:%M:%SZ")
            t = dt.strftime("%H:%M UTC")
        except: t = "TBD"
        lines.append(f"• `{h} vs {a}` — {t}")
    return "\n".join(lines)

def fmt_standings(data):
    standings = data.get("standings",[])
    if not standings: return "Could not fetch standings."
    table = standings[0].get("table",[])
    comp = data.get("competition",{}).get("name","League")
    lines = [f"📊 *{comp.upper()}*\n", "`Pos  Team               Pts`"]
    for row in table[:10]:
        pos = row.get("position","-")
        team = (row.get("team",{}).get("shortName") or row.get("team",{}).get("name","?"))[:16]
        pts = row.get("points",0)
        lines.append(f"`{str(pos).ljust(4)} {team.ljust(18)} {pts}`")
    return "\n".join(lines)

def fmt_scorers(data):
    scorers = data.get("scorers",[])
    if not scorers: return "Could not fetch top scorers."
    lines = ["⚽ *TOP SCORERS*\n"]
    medals = ["🥇","🥈","🥉"]+["   "]*20
    for i,s in enumerate(scorers[:10]):
        name = s.get("player",{}).get("name","?")
        team = s.get("team",{}).get("shortName") or s.get("team",{}).get("name","?")
        goals = s.get("goals",0)
        lines.append(f"{medals[i]} *{name}* ({team}) — {goals} goals")
    return "\n".join(lines)

# ── Gemini AI ─────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY","")

async def gemini(prompt, history=None):
    if not GEMINI_API_KEY: return "AI unavailable — GEMINI_API_KEY not set."
    messages = []
    if history:
        for m in history:
            messages.append({"role":"user" if m.role=="user" else "model","parts":[{"text":m.message}]})
    messages.append({"role":"user","parts":[{"text":prompt}]})
    for model in ["gemini-1.5-flash","gemini-1.5-pro","gemini-pro"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(url, json={"contents":messages,"generationConfig":{"temperature":0.7,"maxOutputTokens":500}})
                data = r.json()
                if "error" in data:
                    if "not found" in data["error"].get("message","").lower(): continue
                    if "quota" in data["error"].get("message","").lower(): return "AI is busy. Try again in a moment! ⏳"
                    continue
                candidates = data.get("candidates",[])
                if candidates:
                    parts = candidates[0].get("content",{}).get("parts",[])
                    if parts: return parts[0].get("text","").strip()
        except: continue
    return "AI unavailable right now. Try again shortly!"

async def ask_ai(question, telegram_id=0):
    live = await get_live_scores()
    fixtures = await get_todays_matches()
    ctx = []
    for m in live.get("matches",[])[:5]:
        h = m["homeTeam"].get("shortName",m["homeTeam"].get("name","?"))
        a = m["awayTeam"].get("shortName",m["awayTeam"].get("name","?"))
        sc = m.get("score",{}).get("fullTime",{})
        ctx.append(f"{h} {sc.get('home',0)}-{sc.get('away',0)} {a} (LIVE)")
    for m in fixtures.get("matches",[])[:8]:
        h = m["homeTeam"].get("shortName",m["homeTeam"].get("name","?"))
        a = m["awayTeam"].get("shortName",m["awayTeam"].get("name","?"))
        ctx.append(f"{h} vs {a}")
    history = get_history(telegram_id) if telegram_id else []
    prompt = f"""You are FootballAI — a smart football analyst bot on Telegram.
Today's data: {chr(10).join(ctx) if ctx else 'No live matches right now'}
Date: {datetime.now().strftime('%A %d %B %Y')}
Rules: under 180 words, be specific, use real data above, never say you lack real-time data.
Question: {question}"""
    if telegram_id: save_message(telegram_id,"user",question)
    response = await gemini(prompt, history[-4:] if history else None)
    if telegram_id: save_message(telegram_id,"assistant",response)
    return response

# ── Subscription check ────────────────────────────────────────────
CHANNEL_ID = os.getenv("CHANNEL_ID","@FOOTBALLAIOFFICIAL")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME","FOOTBALLAIOFFICIAL")
CHANNEL_LINK = f"https://t.me/{CHANNEL_USERNAME}"
ADMIN_ID = int(os.getenv("ADMIN_ID","0") if str(os.getenv("ADMIN_ID","0")).isdigit() else "0")

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member","administrator","creator")
    except TelegramError:
        return True

async def send_join_prompt(update):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("📣 Join FootballAI Official",url=CHANNEL_LINK)],[InlineKeyboardButton("✅ I've Joined — Let Me In",callback_data="check_sub")]])
    await update.message.reply_text(
        "Hey! Just one small thing before we get started. 👋\n\n"
        "Join our channel first — we post live scores, tips, previews and predictions there daily.\n\n"
        "Takes 3 seconds! Once you've joined, tap *I've Joined* below. ⚽",
        reply_markup=kb, parse_mode="Markdown")

# ── Handlers ──────────────────────────────────────────────────────
from telegram import Update
from telegram.ext import ContextTypes

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    _, is_new = get_or_create_user(user.id, user.first_name or "", user.username or "")
    if is_new:
        await update.message.reply_text(
            f"⚽ *Welcome to FootballAI Bot, {user.first_name}!*\n\n🎁 You've received *50 welcome points!*\n\n"
            f"📡 /live — Live scores\n📅 /matches — Today's fixtures\n📊 /table — Standings\n"
            f"⚽ /topscorers — Top scorers\n🤖 /ask — Ask AI anything\n🔮 /preview — Match preview\n"
            f"🎯 /predict — Make a prediction\n🏆 /leaderboard — Top predictors\n"
            f"✅ /checkin — Daily points\n💰 /rewards — Your balance\n/help — All commands",
            parse_mode="Markdown")
    else:
        u = get_user(user.id)
        await update.message.reply_text(f"Welcome back, *{user.first_name}!* ⚽\nYou have *{u.points} points*.",parse_mode="Markdown")

async def cmd_live(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    await update.message.chat.send_action("typing")
    await update.message.reply_text(fmt_live(await get_live_scores()), parse_mode="Markdown")

async def cmd_matches(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    await update.message.chat.send_action("typing")
    await update.message.reply_text(fmt_matches(await get_todays_matches()), parse_mode="Markdown")

async def cmd_table(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    await update.message.chat.send_action("typing")
    league = " ".join(ctx.args).lower() if ctx.args else "pl"
    await update.message.reply_text(fmt_standings(await get_standings(league)), parse_mode="Markdown")

async def cmd_topscorers(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    await update.message.chat.send_action("typing")
    league = " ".join(ctx.args).lower() if ctx.args else "pl"
    await update.message.reply_text(fmt_scorers(await get_top_scorers(league)), parse_mode="Markdown")

async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    q = " ".join(ctx.args) if ctx.args else ""
    if not q: await update.message.reply_text("Ask me anything!\nExample: /ask Who will win the Premier League?"); return
    await update.message.chat.send_action("typing")
    await update.message.reply_text(f"🤖 {await ask_ai(q, update.effective_user.id)}", parse_mode="Markdown")

async def cmd_preview(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    if not ctx.args or "vs" not in " ".join(ctx.args).lower():
        await update.message.reply_text("Usage: /preview Arsenal vs Chelsea"); return
    full = " ".join(ctx.args); parts = full.lower().split("vs")
    home = parts[0].strip().title(); away = parts[1].strip().title() if len(parts)>1 else "Opponent"
    await update.message.chat.send_action("typing")
    text = await gemini(f"Write a 3-paragraph football match preview for {home} vs {away}. Include form, key players, and a predicted scoreline. Under 200 words.")
    await update.message.reply_text(f"📋 *{home} vs {away}*\n\n{text}", parse_mode="Markdown")

async def cmd_compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    if not ctx.args or "vs" not in " ".join(ctx.args).lower():
        await update.message.reply_text("Usage: /compare Man City vs Real Madrid"); return
    full = " ".join(ctx.args); parts = full.lower().split("vs")
    t1 = parts[0].strip().title(); t2 = parts[1].strip().title() if len(parts)>1 else "Opponent"
    await update.message.chat.send_action("typing")
    text = await gemini(f"Compare {t1} vs {t2} — form, attack, defence, key players. End with who you'd back today. Under 200 words.")
    await update.message.reply_text(f"⚖️ *{t1} vs {t2}*\n\n{text}", parse_mode="Markdown")

async def cmd_predict(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    args = ctx.args
    if not args or len(args) < 3:
        await update.message.reply_text("Usage: /predict Arsenal 2-1 Chelsea"); return
    score_idx = next((i for i,p in enumerate(args) if "-" in p and p.replace("-","").isdigit()), None)
    if score_idx is None: await update.message.reply_text("Score format: 2-1\nExample: /predict Arsenal 2-1 Chelsea"); return
    home = " ".join(args[:score_idx]); score = args[score_idx]; away = " ".join(args[score_idx+1:])
    try: hg, ag = map(int, score.split("-"))
    except: await update.message.reply_text("Score must be like 2-1 or 0-0"); return
    pid = save_prediction(update.effective_user.id, home, away, hg, ag)
    await update.message.reply_text(f"✅ *Prediction locked!*\n\n*{home.title()} {hg} - {ag} {away.title()}*\n\nPrediction #{pid} saved. Points awarded after the match! 🍀", parse_mode="Markdown")

async def cmd_leaderboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    rows = get_leaderboard(10)
    medals = ["🥇","🥈","🥉"]+[f"{i}." for i in range(4,11)]
    lines = ["🏆 *TOP PREDICTORS*\n"]
    for i,(name,pts) in enumerate(rows): lines.append(f"{medals[i]} *{name}* — {pts:,} pts")
    if not rows: lines.append("No players yet. Use /predict to join!")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_checkin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    user = update.effective_user; get_or_create_user(user.id, user.first_name or "")
    pts, streak, already = do_checkin(user.id)
    if already: await update.message.reply_text(f"✅ Already checked in today!\nStreak: *{streak} days* 🔥\nCome back tomorrow!", parse_mode="Markdown"); return
    await update.message.reply_text(f"✅ *Check-in complete!*\n\n+{pts} points!\n🔥 *{streak}-day streak!*\n\nUse /rewards to see your balance.", parse_mode="Markdown")

async def cmd_rewards(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    user = update.effective_user; u,_ = get_or_create_user(user.id, user.first_name or "")
    u = get_user(user.id)
    ref_link = f"https://t.me/{os.getenv('BOT_USERNAME','YourBot')}?start={u.referral_code}"
    await update.message.reply_text(
        f"💰 *Your Rewards*\n\n👤 {user.first_name}\n🏆 Points: *{u.points:,}*\n🔥 Streak: *{u.streak} days*\n\n"
        f"*Earn more:*\n✅ /checkin — Daily bonus\n🎯 Correct score — 50 pts\n👥 Refer friend — 100 pts\n\n"
        f"*Your referral link:*\n`{ref_link}`", parse_mode="Markdown")

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(ctx.bot, update.effective_user.id): await send_join_prompt(update); return
    await update.message.reply_text(
        "⚽ *FootballAI Bot — Commands*\n\n"
        "📡 /live — Live scores\n📅 /matches — Today's fixtures\n📊 /table [league] — Standings\n"
        "⚽ /topscorers — Top scorers\n🤖 /ask [question] — AI chat\n🔮 /preview [Home] vs [Away]\n"
        "⚖️ /compare [Team1] vs [Team2]\n🎯 /predict [Home] [Score] [Away]\n"
        "🏆 /leaderboard — Top predictors\n✅ /checkin — Daily points\n💰 /rewards — Balance\n\n"
        "Leagues: pl, ucl, laliga, seriea, bundesliga", parse_mode="Markdown")

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user = update.effective_user; get_or_create_user(user.id, user.first_name or "")
    if not await is_subscribed(ctx.bot, user.id): await send_join_prompt(update); return
    text = update.message.text.lower().strip(); name = user.first_name or "champ"
    greetings = ["hi","hello","hey","sup","yo","hiya","good morning","good afternoon","good evening"]
    if any(text == g or text.startswith(g) for g in greetings):
        await update.message.reply_text(f"Hey {name}! ⚽\nAsk me anything about football or use /help to see all commands!", parse_mode="Markdown"); return
    if any(t in text for t in ["thanks","thank you","thx"]):
        await update.message.reply_text(f"You're welcome {name}! ⚽"); return
    if any(t in text for t in ["bye","goodbye","later","see you"]):
        await update.message.reply_text(f"Later {name}! ⚽ Come back anytime! 🔥"); return
    if "?" in text or len(text) > 10:
        await update.message.chat.send_action("typing")
        await update.message.reply_text(f"🤖 {await ask_ai(update.message.text, user.id)}", parse_mode="Markdown"); return
    await update.message.reply_text(f"⚽ Ask me a football question, {name}!\nOr use /help to see all commands.", parse_mode="Markdown")

async def check_sub_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    user = query.from_user; name = user.first_name or "champ"
    if await is_subscribed(ctx.bot, user.id):
        await query.edit_message_text(f"You're all set, {name}! Welcome to FootballAI ⚽🔥\n\nType /help to see everything I can do!")
    else:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📣 Join FootballAI Official",url=CHANNEL_LINK)],[InlineKeyboardButton("✅ I've Joined — Let Me In",callback_data="check_sub")]])
        await query.edit_message_text(f"Hmm, looks like you haven't joined yet, {name}.\nJust tap below, join the channel, then tap I've Joined! ⚽", reply_markup=kb)

# ── Main ──────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def run():
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
    token = os.getenv("BOT_TOKEN")
    if not token: raise ValueError("BOT_TOKEN not set!")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("live", cmd_live))
    app.add_handler(CommandHandler("matches", cmd_matches))
    app.add_handler(CommandHandler("table", cmd_table))
    app.add_handler(CommandHandler("topscorers", cmd_topscorers))
    app.add_handler(CommandHandler("ask", cmd_ask))
    app.add_handler(CommandHandler("preview", cmd_preview))
    app.add_handler(CommandHandler("compare", cmd_compare))
    app.add_handler(CommandHandler("predict", cmd_predict))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    app.add_handler(CommandHandler("checkin", cmd_checkin))
    app.add_handler(CommandHandler("rewards", cmd_rewards))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="^check_sub$"))
    logger.info("FootballAI Bot is running!")
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot is LIVE on Telegram!")
        await asyncio.Event().wait()

def main():
    try: asyncio.run(run())
    except KeyboardInterrupt: logger.info("Bot stopped.")

if __name__ == "__main__":
    main()
