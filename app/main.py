import os
from dotenv import load_dotenv
from tg_bot.main import dotenv_path
import hmac
import logging
from contextlib import asynccontextmanager
import datetime
import uvicorn as uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from db.models import User
from .schemas import AddHabit, UserData, EditHabitName, GetHabit, GetHabitId, DeleteHab, EditTime, CountData
from db import db, crud
from tg_bot.main import send_message_test


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск планировщика
    db.scheduler.start()
    yield
    # Остановка при выключении сервера
    db.scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)


auth_scheme = HTTPBearer()
load_dotenv(dotenv_path=dotenv_path)
SECRET_KEY = os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
ALGORITHM = os.environ.get("ALGORITHM")
COUNT_COMPLETE_HABIT = 20  # назначать с учетом в -1 от требуемого значения


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
    else:
        logger.info("User is exists")
        hash_p_user = await crud.get_user_hash(session=session, id_telegram=user_data.id_telegram)
        input_hash = user_data.password
        result = hmac.compare_digest(str(input_hash), hash_p_user)
        payload = {
            "sub": str(user_data.id_telegram),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
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
    logger.info(habit_data)
    print(habit_data)
    time_list = habit_data.time.split(":")
    logger.info(time_list)
    logger.info(session)
    crud_result = await crud.add_habit(session, habit_data=habit_data)
    logger.info(crud_result)
    if crud_result:
        db.scheduler.add_job(send_message_test,
                          'cron',
                          hour=int(time_list[0]),
                          minute=int(time_list[1]),
                          jobstore='tg_reminder',
                          id=str(crud_result),
                          kwargs={
                              'user_id': habit_data.id_telegram,
                              'name': habit_data.name
                          },
                          )


async def test_add_reminder():
    logger.info("Успешно выполнен тест")
    return "True"


@app.post("/edit_habit/name")
async def edit_name_habit(hd_edit_name: EditHabitName,
                          user: User = Depends(get_current_user),
                          session: Session = Depends(db.get_async_session)):
    logger.info(hd_edit_name)
    logger.info("edit_name_habit")
    edit_data = list()
    edit_data.append(hd_edit_name.id)
    edit_data.append(hd_edit_name.name)
    await crud.edit_habit_name(session, edit_data)
    job = db.scheduler.get_job(job_id=str(hd_edit_name.id), jobstore='tg_reminder')
    current_kwargs = job.kwargs
    current_kwargs["name"] = hd_edit_name.name
    db.scheduler.modify_job(
                         job_id=str(hd_edit_name.id),
                         kwargs=current_kwargs,
                         )


@app.post("/edit_habit/time")
async def update_time(hd_edit_time: EditTime,
                      user: User = Depends(get_current_user),
                      session: Session = Depends(db.get_async_session)):
    logger.info(hd_edit_time)
    logger.info("edit_time_habit")
    time_list = hd_edit_time.time.split(':')
    edit_data = list()
    edit_data.append(hd_edit_time.id)
    edit_data.append(hd_edit_time.name)
    edit_data.append(hd_edit_time.time)
    await crud.edit_habit_time(session, edit_data)
    db.scheduler.reschedule_job(
                                job_id=str(hd_edit_time.id),
                                trigger='cron',
                                hour=int(time_list[0]),
                                minute=int(time_list[1]),
                                jobstore='tg_reminder',
                                )


@app.post("/get_count")
async def get_count_for_user(count_data: CountData,
                             user: User = Depends(get_current_user),
                             session: Session = Depends(db.get_async_session)):
    id_habit = await crud.get_habit_id(session,
                                       id_telegram=count_data.user_id,
                                       name=count_data.name)
    get_count = await crud.get_count(session, id_habit)
    return get_count


@app.post("/edit_habit/up_count")
async def up_count(count_data: CountData,
                   session: Session = Depends(db.get_async_session)):
    logger.info("Up count func run")
    id_habit = await crud.get_habit_id(session,
                                       id_telegram=count_data.user_id,
                                       name=count_data.name)
    get_count = await crud.get_count(session, id_habit)
    if get_count == COUNT_COMPLETE_HABIT:
        await crud.delete_habit(session, id_habit=id_habit)
        db.scheduler.remove_job(job_id=str(id_habit))
        return True
    logger.info(get_count)
    await crud.edit_habit_count(session, habit_id=id_habit)
    return False


@app.get("/get_habit")
async def add_habit(get_hab_dt: GetHabit,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(db.get_async_session)):
    logger.info("Получаем список привычек")
    logger.info(get_hab_dt)
    had_data = await crud.get_habit_by_user(session=session, user_id=get_hab_dt.id)
    logger.info(had_data)
    return had_data


@app.post("/get_habit/id")
async def add_habit(get_hab_id: GetHabitId,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(db.get_async_session)):
    logger.info("Получаем ID привычки")
    logger.info(get_hab_id)
    had_id = await crud.get_habit_id(session=session, id_telegram=get_hab_id.id_telegram, name=get_hab_id.name)
    logger.info(had_id)
    return had_id


@app.delete("/get_habit/id")
async def delete_habit(delete_hab_id: DeleteHab,
                       user: User = Depends(get_current_user),
                       session: Session = Depends(db.get_async_session)):
    logger.info("Endpoint delete raw habit")
    logger.info(delete_hab_id)
    await crud.delete_habit(session, id_habit=delete_hab_id.id_habit)
    db.scheduler.remove_job(job_id=str(delete_hab_id.id_habit), jobstore='tg_reminder')
    return True


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.1.1.1", port=8000, workers=4)
