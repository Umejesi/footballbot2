import os
import random
import logging
import google.generativeai as genai
from api.football import get_todays_matches, get_live_scores, get_standings, get_top_scorers
from db.memory import (
    save_message, get_history, save_learned_fact,
    get_learned_facts, save_user_preference, get_user_preferences
)

logger = logging.getLogger(__name__)

# Load all Gemini keys
GEMINI_KEYS = [k for k in [
    os.getenv("GEMINI_KEY_1"), os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"), os.getenv("GEMINI_KEY_4"),
    os.getenv("GEMINI_KEY_5"), os.getenv("GEMINI_KEY_6"),
    os.getenv("GEMINI_KEY_7"), os.getenv("GEMINI_KEY_8"),
    os.getenv("GEMINI_KEY_9"),
] if k]

if not GEMINI_KEYS and os.getenv("GEMINI_API_KEY"):
    GEMINI_KEYS = [os.getenv("GEMINI_API_KEY")]

logger.info(f"Gemini keys loaded: {len(GEMINI_KEYS)}")

CORRECTION_SIGNALS = ["wrong", "incorrect", "actually", "not true",
                      "mistake", "should be", "correction"]
PREFERENCE_SIGNALS = ["my team", "i support", "i follow", "favourite team",
                      "i'm a fan", "i watch"]


async def _call_gemini(prompt: str) -> str:
    if not GEMINI_KEYS:
        return "AI unavailable — no API keys set."

    keys_to_try = GEMINI_KEYS.copy()
    random.shuffle(keys_to_try)

    for i, key in enumerate(keys_to_try):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )
            result = response.text.strip()
            logger.info(f"Gemini success with key {i+1}")
            return result
        except Exception as e:
            err = str(e)
            logger.error(f"Key {i+1} failed: {err[:80]}")
            if "quota" in err.lower() or "429" in err:
                continue
            if "403" in err or "permission" in err.lower():
                continue
            continue

    return "AI is taking a breather. Try again in a moment! ⏳"


async def _get_live_context() -> str:
    context_parts = []
    try:
        live = await get_live_scores()
        live_matches = live.get("matches", [])
        if live_matches:
            context_parts.append(f"LIVE NOW ({len(live_matches)} matches):")
            for m in live_matches[:8]:
                h = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
                a = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
                sc = m.get("score", {}).get("fullTime", {})
                hg = sc.get("home", 0) or 0
                ag = sc.get("away", 0) or 0
                context_parts.append(f"  {h} {hg}-{ag} {a}")

        fixtures = await get_todays_matches()
        today = fixtures.get("matches", [])
        if today:
            context_parts.append(f"TODAY'S FIXTURES ({len(today)}):")
            for m in today[:10]:
                h = m["homeTeam"].get("shortName", m["homeTeam"].get("name", "?"))
                a = m["awayTeam"].get("shortName", m["awayTeam"].get("name", "?"))
                comp = m.get("competition", {}).get("name", "")
                context_parts.append(f"  {h} vs {a} ({comp})")

        # Add standings for context
        standings = await get_standings("pl")
        table = standings.get("standings", [{}])[0].get("table", [])[:5]
        if table:
            context_parts.append("\nPL TOP 5:")
            for row in table:
                team = row.get("team", {}).get("shortName", "?")
                pts = row.get("points", 0)
                context_parts.append(f"  {row.get('position')}. {team} — {pts}pts")

    except Exception as e:
        logger.error(f"Live context error: {e}")

    return "\n".join(context_parts) if context_parts else "No live data right now."


def _detect_learning(user_message: str, ai_response: str, telegram_id: int):
    msg_lower = user_message.lower()
    if any(s in msg_lower for s in CORRECTION_SIGNALS):
        save_learned_fact(
            f"Correction: '{user_message}' (re: '{ai_response[:80]}')",
            "correction", learned_from=telegram_id
        )
    if any(s in msg_lower for s in PREFERENCE_SIGNALS):
        save_user_preference(telegram_id, user_message)


async def ask_football_ai(question: str, telegram_id: int = 0) -> str:
    live_context = await _get_live_context()
    history = get_history(telegram_id, limit=6) if telegram_id else []
    learned = get_learned_facts(limit=10)
    prefs = get_user_preferences(telegram_id) if telegram_id else []

    learned_str = "\n".join(f"• {f}" for f in learned) if learned else ""
    prefs_str = "\n".join(f"• {p}" for p in prefs) if prefs else ""

    history_str = ""
    if history:
        history_str = "\nCONVERSATION HISTORY:\n"
        for msg in history[-4:]:
            role = "User" if msg.role == "user" else "AI"
            history_str += f"{role}: {msg.message}\n"

    prompt = f"""You are FootballAI — a sharp, passionate football analyst on Telegram (@PitchMasterAIBot).

REAL-TIME FOOTBALL DATA (use this):
{live_context}
{history_str}
{"THINGS I LEARNED: " + learned_str if learned_str else ""}
{"THIS USER PREFERS: " + prefs_str if prefs_str else ""}

RULES:
- Under 180 words for Telegram
- ALWAYS use the real live data above — never give generic answers
- Never say you lack real-time data
- Give specific confident analysis based on CURRENT standings/form
- Vary your predictions — don't repeat the same teams
- Betting tips end with: Not financial advice.
- If user corrects you, acknowledge and update

User question: {question}"""

    if telegram_id:
        save_message(telegram_id, "user", question)

    response = await _call_gemini(prompt)

    if telegram_id:
        save_message(telegram_id, "assistant", response)
        _detect_learning(question, response, telegram_id)

    return response


async def generate_match_insight(home: str, away: str,
                                  home_score: int = None,
                                  away_score: int = None,
                                  stage: str = "preview") -> str:
    if stage == "preview":
        prompt = f"Pre-match insight for {home} vs {away}. Include recent form, key players, simple prediction. Max 120 words. Be specific."
    elif stage == "halftime":
        prompt = f"Half-time: {home} {home_score}-{away_score} {away}. 80-word half-time summary."
    else:
        prompt = f"Full-time: {home} {home_score}-{away_score} {away}. 100-word match summary."
    return await _call_gemini(prompt)


async def generate_match_preview(home: str, away: str) -> str:
    prompt = f"Match preview for {home} vs {away} for Telegram. 3 paragraphs: form, key players, predicted scoreline. Under 200 words."
    return await _call_gemini(prompt)


async def compare_teams(team1: str, team2: str) -> str:
    prompt = f"Compare {team1} vs {team2}: form, attack, defence, key players, H2H. Who wins today? Under 200 words."
    return await _call_gemini(prompt)
