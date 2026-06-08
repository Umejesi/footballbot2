from db.models import Session, User, Prediction, PointsLog
from datetime import datetime, timedelta
import uuid


def get_or_create_user(telegram_id: int, first_name: str, username: str = "") -> tuple:
    """Returns (user, is_new)"""
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        session.close()
        return user, False

    code = str(uuid.uuid4())[:8].upper()
    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username or "",
        points=50,  # welcome bonus
        referral_code=code,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return user, True


def get_user(telegram_id: int):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user


def add_points(telegram_id: int, amount: int, reason: str):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.points += amount
        log = PointsLog(telegram_id=telegram_id, amount=amount, reason=reason)
        session.add(log)
        session.commit()
    session.close()


def save_prediction(telegram_id: int, home_team: str, away_team: str,
                    home_goals: int, away_goals: int) -> int:
    session = Session()
    pred = Prediction(
        telegram_id=telegram_id,
        home_team=home_team.title(),
        away_team=away_team.title(),
        home_goals=home_goals,
        away_goals=away_goals,
    )
    session.add(pred)
    session.commit()
    pred_id = pred.id
    session.close()
    return pred_id


def score_predictions(home_team: str, away_team: str,
                      actual_home: int, actual_away: int):
    """Call this after a match ends to award points."""
    session = Session()
    preds = session.query(Prediction).filter_by(
        home_team=home_team.title(),
        away_team=away_team.title(),
        is_scored=False,
    ).all()

    results = []
    for pred in preds:
        pts = 0
        if pred.home_goals == actual_home and pred.away_goals == actual_away:
            pts = 50  # exact score
        elif (pred.home_goals > pred.away_goals) == (actual_home > actual_away):
            pts = 20  # correct winner
        elif (pred.home_goals == pred.away_goals) == (actual_home == actual_away):
            pts = 10  # correct draw

        pred.is_scored = True
        pred.points_earned = pts

        if pts > 0:
            user = session.query(User).filter_by(telegram_id=pred.telegram_id).first()
            if user:
                user.points += pts
                log = PointsLog(telegram_id=pred.telegram_id, amount=pts,
                                reason=f"prediction_{home_team}_vs_{away_team}")
                session.add(log)
        results.append((pred.telegram_id, pts))

    session.commit()
    session.close()
    return results


def get_leaderboard(limit: int = 10):
    session = Session()
    users = session.query(User).order_by(User.points.desc()).limit(limit).all()
    result = [(u.first_name or u.username or "Anonymous", u.points) for u in users]
    session.close()
    return result


def do_checkin(telegram_id: int) -> tuple:
    """Returns (points_earned, new_streak, already_checked_in)"""
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
        if diff < timedelta(hours=36):
            user.streak += 1
        else:
            user.streak = 1
    else:
        user.streak = 1

    pts = min(5 + (user.streak - 1) * 5, 30)
    user.points += pts
    user.last_checkin = now
    log = PointsLog(telegram_id=telegram_id, amount=pts, reason="daily_checkin")
    session.add(log)
    session.commit()
    streak = user.streak
    session.close()
    return pts, streak, False


def get_referral_by_code(code: str):
    session = Session()
    user = session.query(User).filter_by(referral_code=code.upper()).first()
    session.close()
    return user


def apply_referral(new_user_id: int, referrer_id: int):
    session = Session()
    new_user = session.query(User).filter_by(telegram_id=new_user_id).first()
    if new_user and not new_user.referred_by:
        new_user.referred_by = referrer_id
        new_user.points += 25  # bonus for new user
        referrer = session.query(User).filter_by(telegram_id=referrer_id).first()
        if referrer:
            referrer.points += 100  # bonus for referrer
            log = PointsLog(telegram_id=referrer_id, amount=100, reason="referral_bonus")
            session.add(log)
        session.commit()
    session.close()
