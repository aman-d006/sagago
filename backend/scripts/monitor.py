# monitor.py
import time
import requests
from datetime import datetime

def monitor_turso():
    """Simple monitoring script"""
    while True:
        try:
            # Get stats from your API
            response = requests.get("https://your-app.com/stats")
            stats = response.json()
            
            print(f"\n[{datetime.now()}] Turso Stats:")
            print(f"Pool: {stats['pool']}")
            
            # Alert if near limits
            if stats.get('reads', 0) > 900_000_000:  # 90% of 1B
                print("⚠️ WARNING: Approaching read limit!")
            
            if stats.get('writes', 0) > 22_500_000:  # 90% of 25M
                print("⚠️ WARNING: Approaching write limit!")
            
            time.sleep(3600)  # Check every hour
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_turso()