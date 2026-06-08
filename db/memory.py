from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
engine = create_engine(DATABASE_URL)
MemoryBase = declarative_base()
MemorySession = sessionmaker(bind=engine)


class Conversation(MemoryBase):
    __tablename__ = "conversations"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    role = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LearnedFact(MemoryBase):
    __tablename__ = "learned_facts"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    fact = Column(Text, nullable=False)
    learned_from = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPreference(MemoryBase):
    __tablename__ = "user_preferences"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    preference = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


MemoryBase.metadata.create_all(engine)


def save_message(telegram_id: int, role: str, message: str):
    session = MemorySession()
    try:
        msg = Conversation(telegram_id=telegram_id, role=role, message=message)
        session.add(msg)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_history(telegram_id: int, limit: int = 10) -> list:
    session = MemorySession()
    try:
        msgs = session.query(Conversation)\
            .filter_by(telegram_id=telegram_id)\
            .order_by(Conversation.created_at.desc())\
            .limit(limit).all()
        return list(reversed(msgs))
    except Exception:
        return []
    finally:
        session.close()


def save_learned_fact(fact: str, category: str, learned_from: int = None):
    session = MemorySession()
    try:
        existing = session.query(LearnedFact).filter_by(fact=fact).first()
        if not existing:
            lf = LearnedFact(fact=fact, category=category, learned_from=learned_from)
            session.add(lf)
            session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_learned_facts(limit: int = 20) -> list:
    session = MemorySession()
    try:
        facts = session.query(LearnedFact)\
            .order_by(LearnedFact.created_at.desc())\
            .limit(limit).all()
        return [f.fact for f in facts]
    except Exception:
        return []
    finally:
        session.close()


def save_user_preference(telegram_id: int, preference: str):
    session = MemorySession()
    try:
        pref = UserPreference(telegram_id=telegram_id, preference=preference)
        session.add(pref)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def get_user_preferences(telegram_id: int) -> list:
    session = MemorySession()
    try:
        prefs = session.query(UserPreference)\
            .filter_by(telegram_id=telegram_id)\
            .order_by(UserPreference.created_at.desc())\
            .limit(5).all()
        return [p.preference for p in prefs]
    except Exception:
        return []
    finally:
        session.close()
