from typing import List

from pydantic import BaseModel


class VoiceConfig(BaseModel):
    voice_enable: str
    voice_api_key: str
    voice_generation_type: str

class WeekdayRoughSchedule(BaseModel):
    morning: str
    afternoon: str
    evening: str

class WeekendRoughSchedule(BaseModel):
    saturday: str
    sunday: str

class Holiday(BaseModel):
    holiday_name: str
    arrange: str

class RoughSchedulePreferences(BaseModel):
    weekday: WeekdayRoughSchedule
    weekend: WeekendRoughSchedule

class RoughScheduleSpecialRule(BaseModel):
    holiday: List[Holiday]

class RoughSchedule(BaseModel):
    schedule_preferences: RoughSchedulePreferences
    special_rules: RoughScheduleSpecialRule
