from fastapi.templating import Jinja2Templates
from datetime import datetime

templates = Jinja2Templates(directory="app/frontend/templates")

def humantime(ts):
    if not ts:
        return "—"
    return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")

def duration(seconds):
    if not seconds:
        return "—"
    seconds = int(seconds)
    h, m = divmod(seconds, 3600)
    m, s = divmod(m, 60)
    return f"{h:02}:{m:02}:{s:02}"

templates.env.filters["humantime"] = humantime
templates.env.filters["duration"] = duration
