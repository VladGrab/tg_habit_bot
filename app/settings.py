import os

from dotenv import load_dotenv
from fastapi.security import HTTPBearer

from tg_bot.main import dotenv_path

auth_scheme = HTTPBearer()
load_dotenv(dotenv_path=dotenv_path)
SECRET_KEY = os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
ALGORITHM = os.environ.get("ALGORITHM")
COUNT_COMPLETE_HABIT = 20  # назначать с учетом в -1 от требуемого значения

