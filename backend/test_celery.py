"""Simple script to test Celery connection and task execution."""

import sys
import time
from app.tasks.celery_app import celery_app
from app.tasks.job_monitor import test_task

def main():
    print("=" * 80)
    print("Testing Celery connection...")
    print("=" * 80)
    
    # Check if Celery app is configured
    print(f"\n1. Celery app name: {celery_app.main}")
    print(f"2. Broker URL: {celery_app.conf.broker_url}")
    print(f"3. Backend URL: {celery_app.conf.result_backend}")
    
    # Try to ping the broker
    try:
        print("\n4. Attempting to ping Redis broker...")
        result = celery_app.control.inspect().active()
        if result is None:
            print("   ⚠️  No workers are currently running.")
            print("   To start a worker, run in another terminal:")
            print("   cd backend && celery -A app.tasks.celery_app worker --loglevel=info")
            print("\n   Skipping task execution test.")
            return
        else:
            print(f"   ✓ Connected! Active workers: {list(result.keys())}")
    except Exception as e:
        print(f"   ✗ Failed to connect to Redis: {e}")
        print("\n   Make sure Redis is running:")
        print("   docker-compose up redis")
        sys.exit(1)
    
    # Try to execute the test task
    try:
        print("\n5. Executing test_task...")
        async_result = test_task.delay()
        print(f"   Task ID: {async_result.id}")
        print("   Waiting for result (max 10s)...")
        
        result = async_result.get(timeout=10)
        print(f"   ✓ Task completed successfully!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ✗ Task execution failed: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✓ Celery is working correctly!")
    print("=" * 80)

if __name__ == "__main__":
    main()
