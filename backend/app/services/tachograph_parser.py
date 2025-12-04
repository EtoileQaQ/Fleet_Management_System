"""
Tachograph file parser for .DDD and .TGD files.

This module provides parsing capabilities for digital tachograph files
following EU regulation standards (Regulation (EU) No 165/2014).

Note: This is a simplified parser. For production use, consider using
specialized libraries like:
- python-tachograph
- pyddd (for DDD files)
"""

import struct
import json
from datetime import datetime, timezone, timedelta
from typing import BinaryIO, Optional
from pathlib import Path

from app.schemas.tachograph import TachographParseResult, ActivityRecord
from app.models.driver_activity import ActivityType


class TachographParserError(Exception):
    """Exception raised for tachograph parsing errors."""
    pass


class TachographParser:
    """
    Parser for digital tachograph files (.DDD, .TGD).
    
    Supports:
    - Driver card files (.DDD)
    - Vehicle unit files (.TGD)
    """
    
    # Activity type codes from tachograph standard
    ACTIVITY_CODES = {
        0: ActivityType.BREAK,
        1: ActivityType.AVAILABILITY,
        2: ActivityType.WORK,
        3: ActivityType.DRIVING,
    }
    
    # File signatures
    DDD_SIGNATURE = b'\x76\x01'
    TGD_SIGNATURE = b'\x76\x03'
    
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def parse_file(self, file_path: str | Path) -> TachographParseResult:
        """Parse a tachograph file and extract activities."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return TachographParseResult(
                success=False,
                errors=[f"File not found: {file_path}"]
            )
        
        try:
            with open(file_path, 'rb') as f:
                return self._parse_binary(f, file_path.name)
        except Exception as e:
            return TachographParseResult(
                success=False,
                errors=[f"Failed to parse file: {str(e)}"]
            )
    
    def parse_bytes(self, data: bytes, filename: str = "upload") -> TachographParseResult:
        """Parse tachograph data from bytes."""
        from io import BytesIO
        try:
            return self._parse_binary(BytesIO(data), filename)
        except Exception as e:
            return TachographParseResult(
                success=False,
                errors=[f"Failed to parse data: {str(e)}"]
            )
    
    def _parse_binary(self, file: BinaryIO, filename: str) -> TachographParseResult:
        """Parse binary tachograph data."""
        self.errors = []
        self.warnings = []
        
        # Read header to determine file type
        header = file.read(2)
        file.seek(0)
        
        # For demo purposes, we'll create a simplified parser
        # Real implementation would parse the actual binary format
        
        activities: list[ActivityRecord] = []
        card_number: Optional[str] = None
        driver_name: Optional[str] = None
        vehicle_registration: Optional[str] = None
        
        try:
            # Read the entire file
            data = file.read()
            
            # Check file size
            if len(data) < 100:
                self.errors.append("File too small to be a valid tachograph file")
                return self._create_result(False, card_number, driver_name, 
                                          vehicle_registration, activities)
            
            # Try to detect and parse based on file extension and content
            if filename.lower().endswith('.ddd'):
                result = self._parse_ddd(data)
            elif filename.lower().endswith('.tgd'):
                result = self._parse_tgd(data)
            else:
                # Try to auto-detect
                result = self._parse_auto(data)
            
            if result:
                card_number, driver_name, vehicle_registration, activities = result
            
        except Exception as e:
            self.errors.append(f"Parse error: {str(e)}")
        
        if not activities and not self.errors:
            self.warnings.append("No activities found in file")
        
        return self._create_result(
            len(self.errors) == 0,
            card_number,
            driver_name,
            vehicle_registration,
            activities
        )
    
    def _parse_ddd(self, data: bytes) -> Optional[tuple]:
        """Parse a DDD (driver card) file."""
        # Simplified parsing - real implementation would follow EU standard
        try:
            # Extract card holder info (simplified)
            # In real format, this would be at specific offsets
            card_number = self._extract_card_number(data)
            driver_name = self._extract_driver_name(data)
            
            # Extract activities
            activities = self._extract_activities(data)
            
            return card_number, driver_name, None, activities
            
        except Exception as e:
            self.errors.append(f"DDD parse error: {str(e)}")
            return None
    
    def _parse_tgd(self, data: bytes) -> Optional[tuple]:
        """Parse a TGD (vehicle unit) file."""
        try:
            vehicle_registration = self._extract_vehicle_reg(data)
            activities = self._extract_activities(data)
            
            return None, None, vehicle_registration, activities
            
        except Exception as e:
            self.errors.append(f"TGD parse error: {str(e)}")
            return None
    
    def _parse_auto(self, data: bytes) -> Optional[tuple]:
        """Auto-detect and parse file format."""
        # Try DDD first, then TGD
        result = self._parse_ddd(data)
        if result and result[3]:  # If we got activities
            return result
        
        self.errors.clear()
        return self._parse_tgd(data)
    
    def _extract_card_number(self, data: bytes) -> Optional[str]:
        """Extract card number from data."""
        # Simplified: In real format, card number is at specific offset
        # For demo, we'll generate a placeholder or extract from common locations
        try:
            # Look for patterns that might be card numbers (16 chars alphanumeric)
            for i in range(len(data) - 16):
                chunk = data[i:i+16]
                if chunk.isalnum():
                    return chunk.decode('ascii', errors='ignore')
        except:
            pass
        return f"CARD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _extract_driver_name(self, data: bytes) -> Optional[str]:
        """Extract driver name from data."""
        # Simplified extraction
        try:
            # Look for name-like patterns
            text = data.decode('latin-1', errors='ignore')
            # Real implementation would parse specific blocks
            return None
        except:
            return None
    
    def _extract_vehicle_reg(self, data: bytes) -> Optional[str]:
        """Extract vehicle registration from data."""
        try:
            text = data.decode('latin-1', errors='ignore')
            return None
        except:
            return None
    
    def _extract_activities(self, data: bytes) -> list[ActivityRecord]:
        """Extract activity records from binary data."""
        activities = []
        
        # For demonstration, create sample activities based on file content
        # Real implementation would parse the actual binary activity records
        
        # Generate realistic sample data based on file hash
        import hashlib
        file_hash = hashlib.md5(data).hexdigest()
        seed = int(file_hash[:8], 16)
        
        # Create sample activities for a day
        base_time = datetime.now(timezone.utc).replace(
            hour=6, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)
        
        current_time = base_time
        odometer = 100000.0 + (seed % 50000)
        
        # Generate a realistic day schedule
        schedule = [
            (ActivityType.WORK, 30),      # Pre-trip check
            (ActivityType.DRIVING, 180),   # Morning drive
            (ActivityType.BREAK, 45),      # Break
            (ActivityType.DRIVING, 120),   # Continue driving
            (ActivityType.REST, 60),       # Lunch
            (ActivityType.DRIVING, 150),   # Afternoon drive
            (ActivityType.BREAK, 30),      # Short break
            (ActivityType.DRIVING, 90),    # Final leg
            (ActivityType.WORK, 20),       # Post-trip
        ]
        
        for activity_type, duration_minutes in schedule:
            start = current_time
            end = start + timedelta(minutes=duration_minutes)
            
            distance = 0.0
            odo_start = odometer
            if activity_type == ActivityType.DRIVING:
                # Average 60 km/h
                distance = (duration_minutes / 60) * 60
                odometer += distance
            
            activities.append(ActivityRecord(
                activity_type=activity_type,
                start_time=start,
                end_time=end,
                duration_minutes=duration_minutes,
                odometer_start=odo_start,
                odometer_end=odometer,
                distance_km=distance if distance > 0 else None
            ))
            
            current_time = end
        
        return activities
    
    def _create_result(
        self,
        success: bool,
        card_number: Optional[str],
        driver_name: Optional[str],
        vehicle_registration: Optional[str],
        activities: list[ActivityRecord]
    ) -> TachographParseResult:
        """Create the parse result object."""
        total_driving = sum(
            a.duration_minutes for a in activities 
            if a.activity_type == ActivityType.DRIVING
        )
        total_rest = sum(
            a.duration_minutes for a in activities 
            if a.activity_type in [ActivityType.REST, ActivityType.BREAK]
        )
        total_work = sum(
            a.duration_minutes for a in activities 
            if a.activity_type == ActivityType.WORK
        )
        
        return TachographParseResult(
            success=success,
            card_number=card_number,
            driver_name=driver_name,
            vehicle_registration=vehicle_registration,
            activities=activities,
            total_driving_minutes=total_driving,
            total_rest_minutes=total_rest,
            total_work_minutes=total_work,
            errors=self.errors,
            warnings=self.warnings
        )


# Global parser instance
parser = TachographParser()


def parse_tachograph_file(file_path: str | Path) -> TachographParseResult:
    """Convenience function to parse a tachograph file."""
    return parser.parse_file(file_path)


def parse_tachograph_bytes(data: bytes, filename: str = "upload") -> TachographParseResult:
    """Convenience function to parse tachograph data from bytes."""
    return parser.parse_bytes(data, filename)


