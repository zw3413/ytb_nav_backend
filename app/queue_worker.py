import redis, json, time
from db import conn
import os
from dotenv import load_dotenv

load_dotenv()
r = redis.from_url(os.getenv("REDIS_URL"))

def process(video_url):
    # TODO: 接入你自己的 MCP Summary Pipeline
    return {
        "summary": "This is a test summary",
        "timestamps": [
            {"time": "00:00", "label": "Intro"},
            {"time": "02:34", "label": "Topic A"}
        ]
    }

while True:
    task_json = r.brpop("summary_queue", timeout=5)
    if not task_json:
        time.sleep(1)
        continue

    try:
        task = json.loads(task_json[1])
        video_id = task["video_id"]
        url = task["youtube_url"]

        cur = conn.cursor()
        cur.execute("UPDATE video_summary_tasks SET status='processing' WHERE video_id=%s", (video_id,))
        
        result = process(url)
        cur.execute("""
            UPDATE video_summary_tasks
            SET status='done', summary=%s, timestamps=%s
            WHERE video_id=%s
        """, (result["summary"], json.dumps(result["timestamps"]), video_id))

    except Exception as e:
        print("Error:", e)
        cur.execute("UPDATE video_summary_tasks SET status='error', error_message=%s WHERE video_id=%s", (str(e), video_id))
