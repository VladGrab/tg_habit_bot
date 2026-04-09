from sqlalchemy import select, update, delete

from .models import User, Habit


async def get_user_id(session, id_telegram):
    res = await session.execute(
        select(User.id).where(User.id_telegram == id_telegram)
    )
    user = res.scalars().first()
    return user


async def get_user_obj(session, id_telegram):
    res = await session.execute(
        select(User).where(User.id_telegram == id_telegram)
    )
    user = res.scalars().first()
    return user


async def get_user_hash(session, id_telegram):
    res = await session.execute(
        select(User.password_hash).where(User.id_telegram == id_telegram)
    )
    hash = res.scalars().first()
    return hash


async def get_habit_id(session, id_telegram, name):
    user_id = await get_user_id(session, id_telegram)
    res = await session.execute(select(Habit.id).where(Habit.name == name and Habit.user_id == user_id))
    id_habit = res.scalars().first()
    return id_habit


async def select_habit_raw(session, name, user_id):
    res = await session.execute(
        select(Habit).where(Habit.name == name and Habit.user_id == user_id)
    )
    habit_raw = res.scalars().first()
    return habit_raw


async def add_user(session, user_data):
    new_user = User(username=user_data.username,
                    id_telegram=user_data.id_telegram,
                    password_hash=user_data.password_hash)
    session.add(new_user)
    await session.commit()
    return True


async def add_habit(session, habit_data):
    user_id = await get_user_id(session, habit_data.id_telegram)
    print(user_id)
    new_habit = Habit(name=habit_data.name,
                      user_id=user_id,
                      time=habit_data.time)
    session.add(new_habit)
    await session.commit()
    id_habit = new_habit.id
    return id_habit


async def get_habit_by_user(session, user_id):
    p_user_id = await get_user_id(session, user_id)
    query = select(Habit.name, Habit.time).where(Habit.user_id == p_user_id)
    # res = await session.execute(
    #     select(Habit.name, Habit.time).where(Habit.user_id == p_user_id)
    # )
    res = await session.execute(query)
    habit_raw = res.mappings().all()
    return habit_raw


async def edit_habit_name(session, edit_data):
    query = (
        update(Habit)
        .where(Habit.id == edit_data[0])
        .values(name=edit_data[1])
        .execution_options(synchronize_session="fetch")  # Обновляет объект в сессии
    )
    await session.execute(query)
    await session.commit()


async def edit_habit_time(session, edit_data):
    query = (
        update(Habit)
        .where(Habit.id == edit_data[0] and Habit.name == edit_data[1])
        .values(time=edit_data[2])
        .execution_options(synchronize_session="fetch")  # Обновляет объект в сессии
    )
    await session.execute(query)
    await session.commit()


async def get_count(session, id_habit):
    res = await session.execute(
        select(Habit.count_passed).where(Habit.id == id_habit)
    )
    result = res.scalars().first()
    return result


async def edit_habit_count(session, habit_id):
    query = (
        update(Habit)
        .where(Habit.id == habit_id)
        .values(count_passed=Habit.count_passed + 1)
        .execution_options(synchronize_session="fetch")  # Обновляет объект в сессии
    )
    await session.execute(query)
    await session.commit()


async def delete_habit(session, id_habit):
    await session.execute(delete(Habit).where(Habit.id == id_habit))
    await session.commit()

