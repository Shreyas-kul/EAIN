from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.db.session import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True, default="default")
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(64), nullable=True)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class TelemetryLog(Base):
    __tablename__ = "telemetry_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(64), index=True, default="default")
    model = Column(String(64), nullable=False)
    strategy = Column(String(32), default="none")
    tokens_saved = Column(Integer, default=0)
    cost_saved = Column(Float, default=0.0)
    total_cost_usd = Column(Float, default=0.0)
    total_latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
