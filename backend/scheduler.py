import time
from apscheduler.schedulers.background import BackgroundScheduler
from agents import mail_ingest, signal_agent

def job_ingest():
    try:
        print("Running mail_ingest...")
        mail_ingest.run_once()
    except Exception as e:
        print("mail_ingest error:", e)

def job_signals():
    try:
        print("Running signal_agent...")
        signal_agent.generate_signals()
    except Exception as e:
        print("signal_agent error:", e)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_ingest, "interval", minutes=15)
    scheduler.add_job(job_signals, "interval", minutes=30)
    scheduler.start()
    print("Scheduler started. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(5)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

