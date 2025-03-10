Here's your README file:  

---

# **LectureTube Recorder**  

## **Overview**  
LectureTube Recorder is a Python-based scheduling tool that records lecture streams from **TU Wien's LectureTube** service. It allows configuring multiple lectures with different rooms and time schedules, saving recordings to a structured folder system.

## **Features**  
- Automatically records scheduled streams based on a YAML config.  
- Stores recordings in lecture-specific directories.  
- Logs errors and recording progress.  
- Supports dynamic config reloading.  
- Runs efficiently inside a **Docker container**.  

---

## **Configuration**  

Create a **YAML config file** (default: `./config.yml`) with the following format:

```yaml
lectures:
  - lecture: "Introduction to AI"
    rooms:
      - room_id: "cdeg13-ei-7-hoersaal"
        day: "tuesday"
        time: "10:00"
        duration: 3600  # Duration in seconds
      - room_id: "cdeg14-ei-8-hoersaal"
        day: "friday"
        time: "14:30"
        duration: 7200
  - lecture: "Advanced Robotics"
    rooms:
      - room_id: "robotics-101"
        day: "monday"
        time: "09:00"
        duration: 5400
```

### **Explanation:**  

- `lecture`: Name of the lecture (creates a folder inside `STORAGE_DIR`).  
- `rooms`: List of Hörsäle (lecture halls) for recording.  
- `room_id`: The part of the URL between `lecturetube-live/` and `/playlist.m3u8`. You can find it in the `AllgemeineLink` on [hs-streamer](hs-streamer.fsbau.at)
- `day`: The weekday (e.g., `monday, tuesday, etc.`).  
- `time`: The recording start time (`HH:MM` format).  
- `duration`: Recording duration in seconds.  

---

## **Docker Setup**  

### **Docker Compose**  

Create a `docker-compose.yml` file:  

```yaml
version: "3.8"

services:
  lecturetube-recorder:
    build: .
    container_name: lecturetube-recorder
    restart: always
    volumes:
        - type: bind
          source: ./config.yml
          target: /app/config.yml
          read_only: true
        - ./video-downloads:/app/video-downloads  

```

## **Development**
This project uses `uv` for package management. You can run the cloned project via `uv run main.py` on your machine.

## **Logging & Debugging**  

- **Logs are printed to the console** and capture errors if an `ffmpeg` command fails.  

---

