import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, Index, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ActivityType(str, enum.Enum):
    """Types of driver activities from tachograph."""
    DRIVING = "DRIVING"
    REST = "REST"
    WORK = "WORK"
    AVAILABILITY = "AVAILABILITY"
    BREAK = "BREAK"
    UNKNOWN = "UNKNOWN"


class ActivitySource(str, enum.Enum):
    """Source of the activity data."""
    TACHOGRAPH = "TACHOGRAPH"
    MANUAL = "MANUAL"
    GPS_INFERRED = "GPS_INFERRED"


class DriverActivity(Base):
    """
    Driver activity records from tachograph files.
    Stores driving, rest, work, and availability periods.
    """
    
    __tablename__ = "driver_activities"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign keys
    driver_id: Mapped[int] = mapped_column(
        ForeignKey("drivers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Activity details
    activity_type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        nullable=False,
        index=True
    )
    source: Mapped[ActivitySource] = mapped_column(
        Enum(ActivitySource),
        default=ActivitySource.TACHOGRAPH,
        nullable=False
    )
    
    # Time range (always in UTC)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Odometer readings (km)
    odometer_start: Mapped[float | None] = mapped_column(Float)
    odometer_end: Mapped[float | None] = mapped_column(Float)
    distance_km: Mapped[float | None] = mapped_column(Float)
    
    # Source file info
    source_file: Mapped[str | None] = mapped_column(String(255))
    card_number: Mapped[str | None] = mapped_column(String(50), index=True)
    
    # Metadata
    raw_data: Mapped[str | None] = mapped_column(Text)  # JSON of original parsed data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()"
    )
    
    # Relationships
    driver: Mapped["Driver"] = relationship("Driver", back_populates="activities")
    vehicle: Mapped["Vehicle | None"] = relationship("Vehicle")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_activity_driver_time", "driver_id", "start_time", "end_time"),
        Index("idx_activity_time_range", "start_time", "end_time"),
        Index("idx_activity_card", "card_number", "start_time"),
    )
    
    def __repr__(self) -> str:
        return f"<DriverActivity(id={self.id}, driver={self.driver_id}, type={self.activity_type}, start={self.start_time})>"


# Import at end to avoid circular imports
from app.models.driver import Driver
from app.models.vehicle import Vehicle


