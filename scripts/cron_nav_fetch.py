"""
scripts/cron_nav_fetch.py - Bonus Challenge B1: Auto-fetch NAV every weekday at 8 PM
"""
import sys
import time
import datetime
from pathlib import Path
from live_nav_fetch import main as fetch_main

def is_weekday():
    return datetime.datetime.now().weekday() < 5

def run_scheduled_job():
    print(f"[{datetime.datetime.now()}] Cron Job Triggered - Auto Fetching Live NAVs...")
    if is_weekday():
        fetch_main()
        print(f"[{datetime.datetime.now()}] Weekday NAV Ingestion Completed Successfully.")
    else:
        print(f"[{datetime.datetime.now()}] Weekend detected. Skipping NAV fetch.")

if __name__ == "__main__":
    print("=== BLUESTOCK WEEKDAY 8 PM NAV AUTO-FETCH CRON WORKER ===")
    print("To install as a permanent Windows Task Scheduler job, run this command in Administrator CMD/PowerShell:")
    print('schtasks /create /tn "Bluestock_NAV_Cron_8PM" /tr "C:\\Users\\kayri\\anaconda3\\python.exe \'C:\\Users\\kayri\\OneDrive - IIT BHU\\Documents\\Mutual Funds Analytics\\scripts\\cron_nav_fetch.py\'" /sc weekly /d MON,TUE,WED,THU,FRI /st 20:00 /f')
    
    if "--daemon" in sys.argv:
        print("\nStarting continuous daemon scheduler loop (checks daily at 20:00)...")
        while True:
            now = datetime.datetime.now()
            if now.hour == 20 and now.minute == 0:
                run_scheduled_job()
                time.sleep(65)
            time.sleep(10)
    else:
        print("\nRunning single-shot execution for verification...")
        run_scheduled_job()
