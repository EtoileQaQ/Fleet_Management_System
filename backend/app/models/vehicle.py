import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.database import Base


class VehicleStatus(str, enum.Enum):
    """Vehicle status enumeration."""
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class Vehicle(Base):
    """Vehicle model representing fleet vehicles."""
    
    __tablename__ = "vehicles"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    registration_plate: Mapped[str] = mapped_column(
        String(20), 
        unique=True, 
        nullable=False, 
        index=True
    )
    vin: Mapped[str] = mapped_column(String(17), unique=True, nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus), 
        default=VehicleStatus.ACTIVE, 
        nullable=False
    )
    
    # Real-time tracking fields
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    current_position: Mapped[Geometry | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True
    )
    current_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_odometer: Mapped[float | None] = mapped_column(Float, nullable=True)  # km
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    current_driver: Mapped["Driver | None"] = relationship(
        "Driver",
        back_populates="current_vehicle",
        foreign_keys="Driver.current_vehicle_id",
        uselist=False
    )
    gps_positions: Mapped[list["GPSPosition"]] = relationship(
        "GPSPosition",
        back_populates="vehicle"
    )
    
    @property
    def is_online(self) -> bool:
        """Check if vehicle is online (last seen within 5 minutes)."""
        if self.last_seen is None:
            return False
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        return (now - self.last_seen) < timedelta(minutes=5)
    
    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, plate={self.registration_plate}, status={self.status})>"


# Import at the end to avoid circular imports
from app.models.driver import Driver
from app.models.gps_position import GPSPosition
