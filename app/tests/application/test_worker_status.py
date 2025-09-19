#!/usr/bin/env python3
"""
Simple test script to verify the worker status service works correctly.
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.infrastructure.db.sqlite import init_db
from app.infrastructure.repositories.calendar_repository import CalendarRepository
from app.application.worker_status_service import WorkerStatusService

async def test_worker_status_service():
    """Test the worker status service."""
    print("🧪 Testing WorkerStatusService...")
    
    # Initialize database
    await init_db()
    
    # Create service
    repository = CalendarRepository()
    service = WorkerStatusService(repository)
    
    # Test the service
    try:
        result = await service.get_worker_status_summary()
        print("✅ Service test successful!")
        print(f"📊 Total pending: {result.total_pending}")
        print(f"📅 Groups by date/hour: {len(result.pending_by_date_hour)}")
        
        for group in result.pending_by_date_hour[:3]:  # Show first 3 groups
            print(f"   - {group.date} {group.hour:02d}:00 - {group.count} prices ({'simple' if group.is_simple else 'complex'})")
        
        return True
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_worker_status_service())
    sys.exit(0 if success else 1)
