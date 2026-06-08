# ⚽ FootballAI Telegram Bot

A full-featured football Telegram bot with live scores, AI predictions, prediction pools, and a rewards system.

## Setup

### 1. Get your API keys
- **Telegram bot token**: Message @BotFather on Telegram → /newbot
- **Football data**: Sign up at https://www.football-data.org (free)
- **Anthropic API**: Get key at https://console.anthropic.com

### 2. Configure your keys
```bash
cp .env.example .env
# Open .env and paste your keys
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the bot
```bash
python -m bot.main
```

---

## Commands

| Command | What it does |
|---|---|
| `/start` | Register + welcome message |
| `/live` | Live scores right now |
| `/matches` | Today's fixtures |
| `/table [league]` | League standings |
| `/topscorers [league]` | Top goal scorers |
| `/ask [question]` | Ask Football AI anything |
| `/preview [Home] vs [Away]` | AI match preview |
| `/compare [Team1] vs [Team2]` | AI team comparison |
| `/predict Arsenal 2-1 Chelsea` | Lock in a prediction |
| `/leaderboard` | Top predictors |
| `/checkin` | Daily points |
| `/rewards` | Balance + referral link |
| `/help` | All commands |

## League shortcuts (use with /table and /topscorers)
- `pl` — Premier League
- `ucl` — Champions League
- `laliga` — La Liga
- `seriea` — Serie A
- `bundesliga` — Bundesliga

## Scoring predictions after a match
```bash
python score_match.py "Arsenal" "Chelsea" 2 1
```
This awards points to all users who predicted Arsenal vs Chelsea.

---

## Points system
| Action | Points |
|---|---|
| Join (welcome bonus) | 50 |
| Correct exact scoreline | 50 |
| Correct winner | 20 |
| Correct draw | 10 |
| Daily check-in | 5–30 (streak bonus) |
| Refer a friend | 100 |

## Project structure
```
footballbot/
├── bot/
│   ├── main.py              # Entry point — run this
│   └── handlers/            # One file per command group
├── api/
│   └── football.py          # Fetches data from football-data.org
├── ai/
│   └── chat.py              # Claude AI integration
├── db/
│   ├── models.py            # Database tables
│   └── crud.py              # Read/write helpers
├── score_match.py           # Award points after a match
├── .env.example             # Copy this to .env and fill keys
└── requirements.txt
```
