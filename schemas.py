from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

# User Schemas
class UserBase(BaseModel):
    name: Optional[str] = None
    phone: str
    city: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserSignup(BaseModel):
    name: str
    phone: str
    password: str
    fcm_token: Optional[str] = None

class UserLogin(BaseModel):
    phone: str
    password: str
    fcm_token: Optional[str] = None

class UserRegister(BaseModel):
    name: str

class User(UserBase):
    id: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Group Schemas
class GroupBase(BaseModel):
    temple_name: Optional[str] = None
    group_name: str
    mantra_name: Optional[str] = None
    mantra_text: Optional[str] = None
    target_count: Optional[int] = None
    deadline: Optional[datetime] = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: str
    created_by: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Chant Log Schemas
class ChantLogBase(BaseModel):
    group_id: str
    count: int
    method: str  # "tap"|"mala"|"manual"|"voice"

class ChantLogCreate(ChantLogBase):
    pass

class ChantLog(ChantLogBase):
    id: str
    user_id: str
    chanted_at: datetime
    chant_date: date

    class Config:
        from_attributes = True

class ChantAddResponse(BaseModel):
    today_total: int
    all_time_total: int

class TodayChantResponse(BaseModel):
    today_count: int
    yesterday_count: int

# Leaderboard/Summary Schemas
class DailySummary(BaseModel):
    user_id: str
    group_id: str
    chant_date: date
    total_count: int

    class Config:
        from_attributes = True

class GroupStatsResponse(BaseModel):
    total_chants: int
    member_count: int
    daily_total: int

class GlobalStatsResponse(BaseModel):
    total_chants: int
    global_target: int
    completion_percentage: float

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    is_new_user: bool = False
    user: Optional[User] = None

class TokenData(BaseModel):
    phone: Optional[str] = None

class OTPVerify(BaseModel):
    phone: str
    otp: str
    fcm_token: Optional[str] = None

class OTPSend(BaseModel):
    phone: str
