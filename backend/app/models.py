from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("user_id", "friend_user_id", name="uq_friendship_pair"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CollectionVisibility(Base):
    __tablename__ = "collection_visibility"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    default_visibility = Column(String(20), default="private", nullable=False)


class SharedCollection(Base):
    __tablename__ = "shared_collections"
    __table_args__ = (UniqueConstraint("owner_user_id", "viewer_user_id", name="uq_shared_collection"),)

    id = Column(Integer, primary_key=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    viewer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(String(20), default="view", nullable=False)


class Set(Base):
    __tablename__ = "sets"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    series = Column(String(120), nullable=True)
    release_date = Column(Date, nullable=True)
    total_cards = Column(Integer, nullable=True)
    symbol_url = Column(String(255), nullable=True)


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True)
    set_id = Column(Integer, ForeignKey("sets.id"), nullable=False, index=True)
    number = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    rarity = Column(String(80), nullable=True)
    supertype = Column(String(80), nullable=True)
    subtypes = Column(JSON, nullable=True)
    types = Column(JSON, nullable=True)
    hp = Column(String(20), nullable=True)
    artist = Column(String(120), nullable=True)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CardVariant(Base):
    __tablename__ = "card_variants"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    variant_type = Column(String(80), nullable=False)


class ExternalId(Base):
    __tablename__ = "external_ids"
    __table_args__ = (UniqueConstraint("entity_type", "entity_id", "source", name="uq_external_id"),)

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)
    external_id = Column(String(255), nullable=False)


class CardImage(Base):
    __tablename__ = "card_images"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    kind = Column(String(40), nullable=False)
    source_url = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)
    sha256 = Column(String(128), nullable=True)
    downloaded_at = Column(DateTime, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)


class UserPhoto(Base):
    __tablename__ = "user_photos"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)
    graded_item_id = Column(Integer, ForeignKey("graded_items.id"), nullable=True)
    local_path = Column(String(500), nullable=False)
    thumb_path = Column(String(500), nullable=False)
    caption = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StorageLocation(Base):
    __tablename__ = "storage_locations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(120), nullable=False)
    type = Column(String(80), nullable=True)
    details_json = Column(JSON, nullable=True)


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("card_variants.id"), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    condition = Column(String(20), default="NM", nullable=False)
    is_for_trade = Column(Boolean, default=False, nullable=False)
    is_wantlist = Column(Boolean, default=False, nullable=False)
    is_watched = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)
    purchase_price = Column(Float, nullable=True)
    purchase_date = Column(Date, nullable=True)
    vendor = Column(String(120), nullable=True)
    sell_price = Column(Float, nullable=True)
    sell_date = Column(Date, nullable=True)
    storage_location_id = Column(Integer, ForeignKey("storage_locations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GradedItem(Base):
    __tablename__ = "graded_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    grader = Column(String(20), nullable=False)
    grade = Column(String(20), nullable=False)
    cert_number = Column(String(80), nullable=True)
    notes = Column(Text, nullable=True)
    purchase_price = Column(Float, nullable=True)
    purchase_date = Column(Date, nullable=True)
    vendor = Column(String(120), nullable=True)
    sell_price = Column(Float, nullable=True)
    sell_date = Column(Date, nullable=True)
    storage_location_id = Column(Integer, ForeignKey("storage_locations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TagDetail(Base):
    __tablename__ = "tag_details"

    graded_item_id = Column(Integer, ForeignKey("graded_items.id"), primary_key=True)
    overall_grade = Column(String(20), nullable=True)
    subgrades_json = Column(JSON, nullable=True)
    dig_report_url = Column(String(500), nullable=True)
    extra_json = Column(JSON, nullable=True)


class PriceSource(Base):
    __tablename__ = "price_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    type = Column(String(80), nullable=False)
    config_json = Column(JSON, nullable=True)


class LatestPrice(Base):
    __tablename__ = "latest_prices"
    __table_args__ = (UniqueConstraint("entity_type", "entity_id", "source_id", name="uq_latest_price"),)

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey("price_sources.id"), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    market = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    mid = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(Integer, nullable=False)
    source_id = Column(Integer, ForeignKey("price_sources.id"), nullable=False)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    market = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    mid = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_value = Column(Float, nullable=False)
    raw_value = Column(Float, nullable=False)
    graded_value = Column(Float, nullable=False)


class PortfolioBreakdown(Base):
    __tablename__ = "portfolio_breakdowns"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
    breakdown_type = Column(String(40), nullable=False)
    key = Column(String(120), nullable=False)
    value = Column(Float, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(40), nullable=False)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(Integer, nullable=False)
    threshold = Column(Float, nullable=True)
    direction = Column(String(20), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True)
    job_name = Column(String(120), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running", nullable=False)
    stats_json = Column(JSON, nullable=True)
    error_text = Column(Text, nullable=True)
