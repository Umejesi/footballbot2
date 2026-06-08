from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = "users"
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
    # Learning — favourite team and topics
    favourite_team = Column(String, default="")
    preferred_leagues = Column(String, default="")
    interaction_count = Column(Integer, default=0)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)
    is_scored = Column(Boolean, default=False)
    points_earned = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class PointsLog(Base):
    __tablename__ = "points_log"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    """Stores chat history per user so AI remembers context."""
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AIFeedback(Base):
    """Stores corrections and feedback so AI improves over time."""
    __tablename__ = "ai_feedback"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    original_question = Column(Text, nullable=False)
    original_answer = Column(Text, nullable=False)
    correction = Column(Text, nullable=True)   # what user said was wrong
    rating = Column(Integer, nullable=True)    # 1-5 stars
    created_at = Column(DateTime, default=datetime.utcnow)


class BotKnowledge(Base):
    """Things the AI has learned from users over time."""
    __tablename__ = "bot_knowledge"
    id = Column(Integer, primary_key=True)
    topic = Column(String, nullable=False)     # e.g. "team_nickname"
    key = Column(String, nullable=False)       # e.g. "man city"
    value = Column(Text, nullable=False)       # e.g. "Manchester City"
    source = Column(String, default="user")    # who taught it
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
