from fastapi.templating import Jinja2Templates
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "frontend" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))