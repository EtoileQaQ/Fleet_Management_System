from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Driver(Base):
    """Driver model representing fleet drivers."""
    
    __tablename__ = "drivers"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    rfid_tag: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    card_number: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)  # Tachograph card
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    
    # Foreign key to current vehicle (nullable - driver might not be assigned)
    current_vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True
    )
    
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
    current_vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="current_driver",
        foreign_keys=[current_vehicle_id]
    )
    gps_positions: Mapped[list["GPSPosition"]] = relationship(
        "GPSPosition",
        back_populates="driver"
    )
    activities: Mapped[list["DriverActivity"]] = relationship(
        "DriverActivity",
        back_populates="driver",
        order_by="desc(DriverActivity.start_time)"
    )
    
    def __repr__(self) -> str:
        return f"<Driver(id={self.id}, name={self.name}, license={self.license_number})>"


# Import at the end to avoid circular imports
from app.models.vehicle import Vehicle
from app.models.gps_position import GPSPosition
from app.models.driver_activity import DriverActivity
