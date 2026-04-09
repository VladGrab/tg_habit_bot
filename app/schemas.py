from typing import Optional, List

from pydantic import BaseModel, NaiveDatetime, Field, ConfigDict, model_validator, field_validator
from sqlalchemy.dialects.postgresql import JSON


class AddHabit(BaseModel):
    id_telegram: int
    name: str
    time: str


class GetHabit(BaseModel):
    id: int


class UserData(BaseModel):
    model_config = ConfigDict(extra='allow')
    username: str
    id_telegram: int
    password: str


class GetHabitId(BaseModel):
    id_telegram: int
    name: str


class EditHabitName(BaseModel):
    id: int
    name: str


class EditTime(BaseModel):
    id: int
    name: str
    time: str


class DeleteHab(BaseModel):
    id_habit: int


class CountData(BaseModel):
    user_id: int
    name: str


