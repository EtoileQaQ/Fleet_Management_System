from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Float, Boolean, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.database import Base


class GPSPosition(Base):
    """
    GPS Position model for tracking vehicle locations.
    Designed for time-series data with partitioning support.
    """
    
    __tablename__ = "gps_positions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Foreign keys
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Timestamp (critical for time-series queries)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    # Location (PostGIS Point geometry - SRID 4326 for WGS84)
    location: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False
    )
    
    # Telemetry data
    speed: Mapped[float | None] = mapped_column(Float)  # km/h
    heading: Mapped[float | None] = mapped_column(Float)  # degrees (0-360)
    odometer: Mapped[float | None] = mapped_column(Float)  # km
    ignition_status: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="gps_positions")
    driver: Mapped["Driver | None"] = relationship("Driver", back_populates="gps_positions")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_gps_vehicle_timestamp", "vehicle_id", "timestamp"),
        Index("idx_gps_timestamp", "timestamp"),
        # Spatial index will be created automatically by GeoAlchemy2
    )
    
    def __repr__(self) -> str:
        return f"<GPSPosition(id={self.id}, vehicle_id={self.vehicle_id}, timestamp={self.timestamp})>"


# Import at the end to avoid circular imports
from app.models.vehicle import Vehicle
from app.models.driver import Driver



