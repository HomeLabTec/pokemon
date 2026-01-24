from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class FriendshipInvite(BaseModel):
    friend_email: EmailStr


class FriendshipAccept(BaseModel):
    friend_user_id: int


class SetOut(BaseModel):
    id: int
    code: str
    name: str
    series: Optional[str]
    release_date: Optional[date]
    total_cards: Optional[int]

    class Config:
        from_attributes = True


class CardOut(BaseModel):
    id: int
    set_id: int
    number: str
    name: str
    rarity: Optional[str]
    supertype: Optional[str]
    subtypes: Optional[List[str]]
    types: Optional[List[str]]
    hp: Optional[str]
    artist: Optional[str]

    class Config:
        from_attributes = True


class HoldingCreate(BaseModel):
    card_id: int
    variant_id: Optional[int] = None
    quantity: int = 1
    condition: str = "NM"
    is_for_trade: bool = False
    is_wantlist: bool = False
    is_watched: bool = False
    notes: Optional[str] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None
    vendor: Optional[str] = None
    sell_price: Optional[float] = None
    sell_date: Optional[date] = None
    storage_location_id: Optional[int] = None


class HoldingUpdate(BaseModel):
    quantity: Optional[int] = None
    condition: Optional[str] = None
    is_for_trade: Optional[bool] = None
    is_wantlist: Optional[bool] = None
    is_watched: Optional[bool] = None
    notes: Optional[str] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None
    vendor: Optional[str] = None
    sell_price: Optional[float] = None
    sell_date: Optional[date] = None
    storage_location_id: Optional[int] = None


class HoldingOut(BaseModel):
    id: int
    card_id: int
    variant_id: Optional[int]
    quantity: int
    condition: str
    is_for_trade: bool
    is_wantlist: bool
    is_watched: bool

    class Config:
        from_attributes = True


class GradedCreate(BaseModel):
    card_id: int
    grader: str
    grade: str
    cert_number: Optional[str] = None
    notes: Optional[str] = None
    purchase_price: Optional[float] = None
    purchase_date: Optional[date] = None
    vendor: Optional[str] = None
    sell_price: Optional[float] = None
    sell_date: Optional[date] = None
    storage_location_id: Optional[int] = None


class GradedOut(BaseModel):
    id: int
    card_id: int
    grader: str
    grade: str
    cert_number: Optional[str]

    class Config:
        from_attributes = True


class PhotoOut(BaseModel):
    id: int
    local_path: str
    thumb_path: str
    caption: Optional[str]

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    range: str
    data: list


class AdminJobRequest(BaseModel):
    mode: Optional[str] = None
    set_code: Optional[str] = None
    include_all: Optional[bool] = False
