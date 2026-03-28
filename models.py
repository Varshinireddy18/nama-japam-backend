from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Date, Boolean, Text
from sqlalchemy.orm import relationship
import uuid
import datetime
from database import Base

# Helper: generates a UUID string compatible with both SQLite and PostgreSQL
def _uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    city = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    fcm_token = Column(String, nullable=True)

    groups_created = relationship("Group", back_populates="creator")
    memberships = relationship("UserGroup", back_populates="user")
    chant_logs = relationship("ChantLog", back_populates="user")
    daily_summaries = relationship("DailySummary", back_populates="user")

class OTPLog(Base):
    __tablename__ = "otp_logs"
    id = Column(String(36), primary_key=True, default=_uuid)
    phone = Column(String, index=True, nullable=False)
    otp = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Group(Base):
    __tablename__ = "groups"
    id = Column(String(36), primary_key=True, default=_uuid)
    temple_name = Column(String)
    group_name = Column(String, nullable=False)
    mantra_name = Column(String)
    mantra_text = Column(Text)
    target_count = Column(Integer)
    deadline = Column(DateTime)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

    creator = relationship("User", back_populates="groups_created")
    members = relationship("UserGroup", back_populates="group")
    chant_logs = relationship("ChantLog", back_populates="group")
    daily_summaries = relationship("DailySummary", back_populates="group")

class UserGroup(Base):
    __tablename__ = "user_groups"
    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    group_id = Column(String(36), ForeignKey("groups.id"))
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="memberships")
    group = relationship("Group", back_populates="members")

class ChantLog(Base):
    __tablename__ = "chant_logs"
    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    group_id = Column(String(36), ForeignKey("groups.id"))
    count = Column(Integer, nullable=False)
    method = Column(String)  # tap, mala, manual, voice
    chanted_at = Column(DateTime, default=datetime.datetime.utcnow)
    chant_date = Column(Date, default=datetime.date.today)

    user = relationship("User", back_populates="chant_logs")
    group = relationship("Group", back_populates="chant_logs")

class DailySummary(Base):
    __tablename__ = "daily_summaries"
    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    group_id = Column(String(36), ForeignKey("groups.id"))
    chant_date = Column(Date, default=datetime.date.today)
    total_count = Column(Integer, default=0)

    user = relationship("User", back_populates="daily_summaries")
    group = relationship("Group", back_populates="daily_summaries")
