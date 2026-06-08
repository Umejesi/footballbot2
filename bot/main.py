import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from dotenv import load_dotenv
load_dotenv()

from bot.handlers.start import handle as start_handle
from bot.handlers.live import handle as live_handle
from bot.handlers.matches import handle as matches_handle
from bot.handlers.table import handle as table_handle
from bot.handlers.topscorers import handle as topscorers_handle
from bot.handlers.predict import handle as predict_handle
from bot.handlers.predict import leaderboard as leaderboard_handle
from bot.handlers.ai_handlers import ask, preview, compare
from bot.handlers.rewards import handle as rewards_handle
from bot.handlers.rewards import checkin as checkin_handle
from bot.handlers.help import handle as help_handle
from bot.handlers.admin import post_now, broadcast, stats
from bot.handlers.chat import handle_message
from bot.handlers.subscription import check_subscription_callback
from bot.handlers.vip import handle as vip_handle
from bot.middleware import require_subscription
from bot.scheduler import setup_scheduler
from db.models import init_db
from db.memory import MemoryBase, engine as memory_engine

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        CallbackQueryHandler, filters
    )

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found!")

    init_db()
    MemoryBase.metadata.create_all(memory_engine)
    logger.info("Database ready.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_handle))
    app.add_handler(CommandHandler("live",        require_subscription(live_handle)))
    app.add_handler(CommandHandler("matches",     require_subscription(matches_handle)))
    app.add_handler(CommandHandler("table",       require_subscription(table_handle)))
    app.add_handler(CommandHandler("topscorers",  require_subscription(topscorers_handle)))
    app.add_handler(CommandHandler("predict",     require_subscription(predict_handle)))
    app.add_handler(CommandHandler("leaderboard", require_subscription(leaderboard_handle)))
    app.add_handler(CommandHandler("ask",         require_subscription(ask)))
    app.add_handler(CommandHandler("preview",     require_subscription(preview)))
    app.add_handler(CommandHandler("compare",     require_subscription(compare)))
    app.add_handler(CommandHandler("rewards",     require_subscription(rewards_handle)))
    app.add_handler(CommandHandler("checkin",     require_subscription(checkin_handle)))
    app.add_handler(CommandHandler("help",        require_subscription(help_handle)))
    app.add_handler(CommandHandler("vip",         require_subscription(vip_handle)))
    app.add_handler(CommandHandler("postnow",     post_now))
    app.add_handler(CommandHandler("broadcast",   broadcast))
    app.add_handler(CommandHandler("botstats",    stats))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        require_subscription(handle_message)
    ))
    app.add_handler(CallbackQueryHandler(
        check_subscription_callback, pattern="^check_subscription$"
    ))

    scheduler = setup_scheduler(app.bot)
    scheduler.start()
    logger.info("Channel scheduler started.")
    logger.info("FootballAI Bot is running!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
