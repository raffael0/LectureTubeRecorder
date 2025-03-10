import os
import subprocess
import schedule
import time
import yaml
import logging
from datetime import datetime


# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Load environment variables
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yml")
STORAGE_DIR = os.getenv("STORAGE_DIR", "video-downloads")

# Initialize schedule_config globally
schedule_config = {"lectures": []}

def load_schedule_config(file_path=CONFIG_PATH):
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file) or {"lectures": []}
    except Exception as e:
        logging.error(f"Failed to load schedule configuration: {e}")
        return {"lectures": []}


def record_stream(lecture, hoersal_id, duration):
    url = f"https://live.video.tuwien.ac.at/lecturetube-live/{hoersal_id}/playlist.m3u8"
    headers = "Referer: https://tuwel.tuwien.ac.at/"
    lecture_dir = os.path.join(STORAGE_DIR, lecture)
    os.makedirs(lecture_dir, exist_ok=True)
    output_file = os.path.join(lecture_dir,
                               f"recording_{hoersal_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4")

    command = [
        "ffmpeg", "-protocol_whitelist", "https,tls,tcp", "-headers", f"Referer: {headers}",
        "-i", url, "-c", "copy", "-t", str(duration), output_file  # Duration from YAML
    ]

    try:
        print(f"Recording started for {hoersal_id} in {lecture}: {output_file}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            error_message = result.stderr.decode("utf-8")
            logging.error(f"Recording failed for {hoersal_id} in {lecture}: {error_message}")
        else:
            print(f"Recording finished for {hoersal_id} in {lecture}")
    except Exception as e:
        logging.error(f"Unexpected error during recording {hoersal_id} in {lecture}: {e}")


def update_schedule():
    global schedule_config
    schedule.clear()
    schedule_config = load_schedule_config()

    for lecture_entry in schedule_config.get("lectures", []):
        lecture_name = lecture_entry["lecture"]
        for entry in lecture_entry.get("rooms", []):
            day = entry["day"].lower()
            time_str = entry["time"]
            hoersal_id = entry["room_id"]
            duration = entry.get("duration", 3600)  # Default to 1 hour if not specified

            if hasattr(schedule.every(), day):
                getattr(schedule.every(), day).at(time_str).do(record_stream, lecture_name, hoersal_id, duration)
            else:
                logging.error(f"Invalid day in schedule: {day}")

    logging.info("Schedule reloaded.")


# Initial schedule load
update_schedule()

# Reload the schedule every 5 minutes
schedule.every(10).seconds.do(update_schedule)

logging.info("Scheduler running... Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(3)
