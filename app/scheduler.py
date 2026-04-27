from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from tg_bot.main import send_message_reminder

SYNC_DATABASE_URL = "postgresql://postgres:mysecretpassword@postgres:5432/habit_bot_tg"


jobstores = {
    'tg_reminder': SQLAlchemyJobStore(url=SYNC_DATABASE_URL)
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Europe/Moscow")


def add_reminder(habit_data, crud_result):
    time = habit_data.time.split(":")
    scheduler.add_job(send_message_reminder,
                      'cron',
                      hour=int(time[0]),
                      minute=int(time[1]),
                      jobstore='tg_reminder',
                      id=str(crud_result),
                      kwargs={
                          'user_id': habit_data.id_telegram,
                          'name': habit_data.name,
                          'habit_id': crud_result
                      },
                      )


def update_name_reminder(data_habit_edit_name):
    job = scheduler.get_job(job_id=str(data_habit_edit_name.id), jobstore='tg_reminder')
    current_kwargs = job.kwargs
    current_kwargs["name"] = data_habit_edit_name.name
    scheduler.modify_job(
        job_id=str(data_habit_edit_name.id),
        kwargs=current_kwargs,
    )


def update_time_reminder(data_habit_edit_time, time):
    scheduler.reschedule_job(
        job_id=str(data_habit_edit_time.id),
        trigger='cron',
        hour=int(time[0]),
        minute=int(time[1]),
        jobstore='tg_reminder',
    )


def delete_reminder(job_id):
    scheduler.remove_job(job_id=job_id, jobstore='tg_reminder')




