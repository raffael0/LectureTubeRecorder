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

#
# Initialize schedule_config globally
current_schedule = {}

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
        logging.info(f"Recording started for {hoersal_id} in {lecture}: {output_file}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            error_message = result.stderr.decode("utf-8")
            logging.error(f"Recording failed for {hoersal_id} in {lecture}: {error_message}")
        else:
            logging.info(f"Recording finished for {hoersal_id} in {lecture}")
    except Exception as e:
        logging.error(f"Unexpected error during recording {hoersal_id} in {lecture}: {e}")

def get_schedule_key(entry):
    return entry["day"].lower(), entry["time"], entry["room_id"], entry.get("duration", 3600)


def update_schedule():
    global current_schedule
    new_schedule = load_schedule_config()
    new_schedule_keys = {}

    changed = False

    for lecture_entry in new_schedule.get("lectures", []):
        lecture_name = lecture_entry["lecture"]
        for entry in lecture_entry.get("rooms", []):
            key = get_schedule_key(entry)

            if key not in current_schedule:
                day = entry["day"].lower()
                time_str = entry["time"]
                hoersal_id = entry["room_id"]
                duration = entry.get("duration", 3600)
                changed = True

                if hasattr(schedule.every(), day):
                    job = getattr(schedule.every(), day).at(time_str, "Europe/Vienna").do(record_stream, lecture_name, hoersal_id,
                                                                         duration)
                    current_schedule[key] = job
                    logging.info(f"Added new recording schedule: {key}")
                else:
                    logging.error(f"Invalid day in schedule: {day}")
            new_schedule_keys[key] = current_schedule.get(key)

    # Remove outdated schedules
    for key in list(current_schedule.keys()):
        if key not in new_schedule_keys:
            changed = True
            schedule.cancel_job(current_schedule[key])
            logging.info(f"Removed outdated recording schedule: {key}")
            del current_schedule[key]

    current_schedule = new_schedule_keys
    if changed:
        logging.info("Schedule updated.")

# Initial schedule load
update_schedule()

# Reload the schedule every 10 seconds
schedule.every(10).seconds.do(update_schedule)

logging.info("Scheduler running... Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(3)
