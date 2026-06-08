import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bot.channel import (
    post_daily_tip, post_transfer_news, post_weekend_predictions,
    post_trivia, post_top_scorers, post_league_table, post_motivation,
)
from bot.phase1 import (
    post_match_insights, post_vip_teaser,
)
from bot.viral import (
    post_daily_fixtures_viral, post_big_match_hype,
    post_live_snapshot, check_and_post_goal_alerts,
    post_no_matches_filler,
)

logger = logging.getLogger(__name__)


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Africa/Lagos")

    # ── VIRAL GROWTH ENGINE ──────────────────────────────

    # Goal alerts — check every 2 minutes (FASTEST growth driver)
    scheduler.add_job(
        check_and_post_goal_alerts,
        IntervalTrigger(minutes=2),
        args=[bot], id="goal_alerts", name="Goal alerts",
    )

    # Daily fixtures — 7:30AM every day (retention engine)
    scheduler.add_job(
        post_daily_fixtures_viral,
        CronTrigger(hour=7, minute=30),
        args=[bot], id="daily_fixtures", name="Daily fixtures",
    )

    # Big match hype — 5PM on match days
    scheduler.add_job(
        post_big_match_hype,
        CronTrigger(hour=17, minute=0),
        args=[bot], id="big_match_hype", name="Big match hype",
    )

    # Live score snapshot — every 10 mins 5PM-11PM
    scheduler.add_job(
        post_live_snapshot,
        CronTrigger(hour="17-23", minute="*/10"),
        args=[bot], id="live_snapshot", name="Live score snapshot",
    )

    # Filler on quiet days — 3PM daily
    scheduler.add_job(
        post_no_matches_filler,
        CronTrigger(hour=15, minute=0),
        args=[bot], id="filler", name="Filler content",
    )

    # ── EXISTING CONTENT SCHEDULE ────────────────────────

    # Match insights — 11AM
    scheduler.add_job(
        post_match_insights,
        CronTrigger(hour=11, minute=0),
        args=[bot], id="match_insights", name="Match insights",
    )

    # Daily tip — 12PM
    scheduler.add_job(
        post_daily_tip,
        CronTrigger(hour=12, minute=0),
        args=[bot], id="daily_tip", name="Daily tip",
    )

    # Trivia — 8PM
    scheduler.add_job(
        post_trivia,
        CronTrigger(hour=20, minute=0),
        args=[bot], id="trivia", name="Evening trivia",
    )

    # Transfer news — Mon/Wed/Fri 2PM
    scheduler.add_job(
        post_transfer_news,
        CronTrigger(day_of_week="mon,wed,fri", hour=14, minute=0),
        args=[bot], id="transfer_news", name="Transfer news",
    )

    # Weekend predictions — Sat 10AM
    scheduler.add_job(
        post_weekend_predictions,
        CronTrigger(day_of_week="sat", hour=10, minute=0),
        args=[bot], id="weekend_preds", name="Weekend predictions",
    )

    # League table — Mon 9AM
    scheduler.add_job(
        post_league_table,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        args=[bot], id="league_table", name="League table",
    )

    # Top scorers — Fri 9AM
    scheduler.add_job(
        post_top_scorers,
        CronTrigger(day_of_week="fri", hour=9, minute=0),
        args=[bot], id="top_scorers", name="Top scorers",
    )

    # Motivation — Sun 9AM
    scheduler.add_job(
        post_motivation,
        CronTrigger(day_of_week="sun", hour=9, minute=0),
        args=[bot], id="motivation", name="Sunday motivation",
    )

    # VIP teaser — Sun 6PM
    scheduler.add_job(
        post_vip_teaser,
        CronTrigger(day_of_week="sun", hour=18, minute=0),
        args=[bot], id="vip_teaser", name="VIP teaser",
    )

    logger.info("Scheduler ready — viral growth engine active.")
    return scheduler
