import hmac
import logging
from contextlib import asynccontextmanager
import uvicorn as uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
from starlette.responses import JSONResponse

from app.utils import create_token
from db.models import User
from .schemas import AddHabit, UserData, EditHabitName, GetHabits, GetHabitId, EditTime, HabitId
from .scheduler import scheduler, add_reminder, update_name_reminder, update_time_reminder, delete_reminder
from app import settings
from db import db, crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск планировщика
    scheduler.start()
    yield
    # Остановка при выключении сервера
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

auth_scheme = settings.auth_scheme
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ALGORITHM = settings.ALGORITHM
COUNT_COMPLETE_HABIT = settings.COUNT_COMPLETE_HABIT


async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(auth_scheme),
                           session: Session = Depends(db.get_async_session)):
    token = auth.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        user = await crud.get_user_obj(session=session, id_telegram=int(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found /start")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired /start")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials /start")


@app.post("/check_user")
async def check_user(user_data: UserData, session: Session = Depends(db.get_async_session)):
    logger.info("Check password endpoint")
    user = await crud.get_user_id(session=session, id_telegram=user_data.id_telegram)
    logger.info(user)

    if user is None:
        logger.info('User is not yet')
        user_data.password_hash = str(user_data.password)
        logger.info(user_data)
        await crud.add_user(session, user_data=user_data)
        token = create_token(user_id=user_data.id_telegram)
        return token
    else:
        logger.info("User is exists")
        hash_in_db_user = await crud.get_user_hash(session=session, id_telegram=user_data.id_telegram)
        input_hash = user_data.password
        result = hmac.compare_digest(str(input_hash), hash_in_db_user)
        token = create_token(user_id=user_data.id_telegram)
        if result is True:
            return token
        elif result is False:
            raise HTTPException(status_code=403, detail="Password is wrong")


@app.post("/check_auth")
async def check_auth(user: User = Depends(get_current_user),
                     session: Session = Depends(db.get_async_session)):
    user = await crud.get_user_id(session=session, id_telegram=user.id_telegram)
    return user


@app.post("/add_user")
async def add_user(user_data: UserData, session: Session = Depends(db.get_async_session)):
    logger.info(user_data)
    await crud.add_user(session, user_data=user_data)


@app.post("/add_habit")
async def add_habit(habit_data: AddHabit,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(db.get_async_session)):
    crud_result = await crud.add_habit(session, habit_data=habit_data)
    if crud_result:
        add_reminder(habit_data=habit_data,
                     crud_result=crud_result)


@app.post("/edit_habit/name")
async def edit_name_habit(data_habit_edit_name: EditHabitName,
                          user: User = Depends(get_current_user),
                          session: Session = Depends(db.get_async_session)):
    logger.info(data_habit_edit_name)
    edit_data = list()
    edit_data.append(data_habit_edit_name.id)
    edit_data.append(data_habit_edit_name.name)
    await crud.edit_habit_name(session, edit_data)
    update_name_reminder(data_habit_edit_name=data_habit_edit_name)


@app.post("/edit_habit/time")
async def update_time(data_habit_edit_time: EditTime,
                      user: User = Depends(get_current_user),
                      session: Session = Depends(db.get_async_session)):
    logger.info(data_habit_edit_time)
    logger.info("edit_time_habit")
    time = data_habit_edit_time.time.split(':')
    edit_data = list()
    edit_data.append(data_habit_edit_time.id)
    edit_data.append(data_habit_edit_time.time)
    await crud.edit_habit_time(session, edit_data)
    update_time_reminder(data_habit_edit_time=data_habit_edit_time,
                         time=time)


@app.post("/get_count")
async def get_count_for_user(count_data: HabitId,
                             user: User = Depends(get_current_user),
                             session: Session = Depends(db.get_async_session)):
    get_count = await crud.get_count(session, count_data.id_habit)
    return get_count


@app.post("/edit_habit/up_count")
async def up_count(count_data: HabitId,
                   session: Session = Depends(db.get_async_session)):
    logger.info("Up count func run")
    get_count = await crud.get_count(session, count_data.id_habit)
    if get_count == COUNT_COMPLETE_HABIT:
        habit_name = await crud.delete_habit(session, id_habit=count_data.id_habit)
        delete_reminder(job_id=str(count_data.id_habit))
        return JSONResponse(status_code=226, content={"habit_name": habit_name})
    logger.info(get_count)
    await crud.edit_habit_count(session, habit_id=count_data.id_habit)
    return False


@app.get("/get_habits")
async def add_habit(data_habit_add: GetHabits,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(db.get_async_session)):
    logger.info("Получаем список привычек")
    logger.info(data_habit_add)
    habit_data = await crud.get_habit_by_user(session=session,
                                              user_id=data_habit_add.user_id)
    logger.info(habit_data)
    return habit_data


@app.get("/get_name_habit")
async def get_habit_name(habit_get_name_data: HabitId,
                         user: User = Depends(get_current_user),
                         session: Session = Depends(db.get_async_session)):
    habit_name = await crud.get_name_habit(session=session,
                                           id_habit=habit_get_name_data.id_habit)
    logger.info(habit_name)
    return habit_name


@app.post("/get_habit/id")
async def add_habit(get_habit_id: GetHabitId,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(db.get_async_session)):
    logger.info("Получаем ID привычки")
    logger.info(get_habit_id)
    habit_id = await crud.get_habit_id(session=session,
                                       id_telegram=get_habit_id.id_telegram,
                                       name=get_habit_id.name)
    logger.info(habit_id)
    return habit_id


@app.delete("/get_habit/id")
async def delete_habit(delete_habit_id: HabitId,
                       user: User = Depends(get_current_user),
                       session: Session = Depends(db.get_async_session)):
    logger.info("Endpoint delete raw habit")
    logger.info(delete_habit_id)
    await crud.delete_habit(session, id_habit=delete_habit_id.id_habit)
    delete_reminder(job_id=str(delete_habit_id.id_habit))
    return True


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, workers=4)
