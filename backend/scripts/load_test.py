#!/usr/bin/env python3
"""
Load test script for telematics GPS endpoint.

Simulates 100 trucks sending GPS data every minute.

Usage:
    python scripts/load_test.py --trucks 100 --duration 60 --interval 60
"""

import asyncio
import argparse
import random
import time
from datetime import datetime, timezone
from dataclasses import dataclass
import httpx


@dataclass
class SimulatedTruck:
    """Simulated truck with GPS tracking."""
    vehicle_id: int
    lat: float
    lon: float
    speed: float
    heading: float
    odometer: float
    
    def update_position(self):
        """Simulate movement."""
        # Random speed 0-90 km/h
        self.speed = random.uniform(0, 90)
        
        # Update heading occasionally
        if random.random() < 0.1:
            self.heading = (self.heading + random.uniform(-30, 30)) % 360
        
        # Move based on speed and heading (simplified)
        if self.speed > 0:
            # Convert speed to degrees per second (very simplified)
            distance_deg = (self.speed / 3600) * 0.01
            import math
            self.lat += distance_deg * math.cos(math.radians(self.heading))
            self.lon += distance_deg * math.sin(math.radians(self.heading))
            
            # Update odometer
            self.odometer += self.speed / 3600  # km per second
        
        # Keep within bounds
        self.lat = max(-90, min(90, self.lat))
        self.lon = max(-180, min(180, self.lon))


class LoadTester:
    """Load tester for telematics endpoint."""
    
    def __init__(
        self,
        base_url: str,
        num_trucks: int,
        duration_seconds: int,
        interval_seconds: int
    ):
        self.base_url = base_url.rstrip('/')
        self.num_trucks = num_trucks
        self.duration = duration_seconds
        self.interval = interval_seconds
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_latency = 0.0
        self.max_latency = 0.0
        self.min_latency = float('inf')
        
        # Initialize trucks
        self.trucks: list[SimulatedTruck] = []
        self._init_trucks()
    
    def _init_trucks(self):
        """Initialize simulated trucks."""
        # Start positions spread around Europe
        base_lat, base_lon = 48.8566, 2.3522  # Paris
        
        for i in range(self.num_trucks):
            self.trucks.append(SimulatedTruck(
                vehicle_id=i + 1,  # Assuming vehicle IDs 1 to num_trucks
                lat=base_lat + random.uniform(-5, 5),
                lon=base_lon + random.uniform(-10, 10),
                speed=random.uniform(0, 80),
                heading=random.uniform(0, 360),
                odometer=random.uniform(10000, 500000)
            ))
    
    async def send_position(self, client: httpx.AsyncClient, truck: SimulatedTruck):
        """Send a single position update."""
        payload = {
            "vehicle_id": truck.vehicle_id,
            "lat": truck.lat,
            "lon": truck.lon,
            "speed": truck.speed,
            "heading": truck.heading,
            "odometer": truck.odometer,
            "ignition": truck.speed > 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        start_time = time.time()
        try:
            response = await client.post(
                f"{self.base_url}/api/v1/telematics/ping",
                json=payload,
                timeout=10.0
            )
            latency = time.time() - start_time
            
            self.total_requests += 1
            self.total_latency += latency
            self.max_latency = max(self.max_latency, latency)
            self.min_latency = min(self.min_latency, latency)
            
            if response.status_code == 200:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
        except Exception as e:
            self.total_requests += 1
            self.failed_requests += 1
            print(f"Error sending position for truck {truck.vehicle_id}: {e}")
    
    async def run_batch(self, client: httpx.AsyncClient):
        """Send positions for all trucks concurrently."""
        # Update all truck positions
        for truck in self.trucks:
            truck.update_position()
        
        # Send all positions concurrently
        tasks = [self.send_position(client, truck) for truck in self.trucks]
        await asyncio.gather(*tasks)
    
    async def run(self):
        """Run the load test."""
        print(f"Starting load test:")
        print(f"  - Trucks: {self.num_trucks}")
        print(f"  - Duration: {self.duration} seconds")
        print(f"  - Interval: {self.interval} seconds")
        print(f"  - Target URL: {self.base_url}")
        print()
        
        start_time = time.time()
        batch_count = 0
        
        async with httpx.AsyncClient() as client:
            while time.time() - start_time < self.duration:
                batch_start = time.time()
                
                await self.run_batch(client)
                batch_count += 1
                
                # Print progress
                elapsed = time.time() - start_time
                avg_latency = self.total_latency / max(1, self.successful_requests)
                print(
                    f"Batch {batch_count}: "
                    f"{self.successful_requests}/{self.total_requests} successful, "
                    f"avg latency: {avg_latency*1000:.1f}ms, "
                    f"elapsed: {elapsed:.0f}s"
                )
                
                # Wait for next interval
                batch_duration = time.time() - batch_start
                sleep_time = max(0, self.interval - batch_duration)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
        
        # Print final statistics
        self._print_stats()
    
    def _print_stats(self):
        """Print final statistics."""
        print()
        print("=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Total Requests:      {self.total_requests}")
        print(f"Successful:          {self.successful_requests}")
        print(f"Failed:              {self.failed_requests}")
        print(f"Success Rate:        {100 * self.successful_requests / max(1, self.total_requests):.1f}%")
        print()
        
        if self.successful_requests > 0:
            avg_latency = self.total_latency / self.successful_requests
            print(f"Avg Latency:         {avg_latency * 1000:.1f} ms")
            print(f"Min Latency:         {self.min_latency * 1000:.1f} ms")
            print(f"Max Latency:         {self.max_latency * 1000:.1f} ms")
        
        print()
        print(f"Throughput:          {self.total_requests / self.duration:.1f} req/s")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Load test for telematics endpoint")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API"
    )
    parser.add_argument(
        "--trucks",
        type=int,
        default=100,
        help="Number of simulated trucks"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval between batches in seconds"
    )
    
    args = parser.parse_args()
    
    tester = LoadTester(
        base_url=args.url,
        num_trucks=args.trucks,
        duration_seconds=args.duration,
        interval_seconds=args.interval
    )
    
    asyncio.run(tester.run())


if __name__ == "__main__":
    main()


