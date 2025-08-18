import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    bot_token: str = os.getenv("BOT_TOKEN", "")
    webapp_base_url: str = os.getenv("WEBAPP_BASE_URL", "")
    admin_username: str = os.getenv("ADMIN_USERNAME", "@poizmanager")

settings = Settings()
