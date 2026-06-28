from pydantic import TypeAdapter

from orm.health_orm import SleepSessionORM, StepORM, HeartRateORM
from entity.health import LastDayHealthModel, SleepSessionModel, StepModel, HeartRateModel

step_orm_obj = StepORM()
heart_rate_orm_obj = HeartRateORM()
sleep_session_orm_obj = SleepSessionORM()



def select_last_day_health_data():
    sleep_sessions = sleep_session_orm_obj.select_last_day()
    SleepSessionListAdapter = TypeAdapter(list[SleepSessionModel])
    sleep_sessions_model_list = SleepSessionListAdapter.validate_python(sleep_sessions)

    steps = step_orm_obj.select_last_day()
    steps_model_list = [StepModel(steps=step.steps, synced_time=step.synced_time) for step in steps]
    heart_rates = heart_rate_orm_obj.select_last_day()
    heart_rates_model_list = [HeartRateModel(avg_bpm=heart_rate.avg_bpm, max_bpm=heart_rate.max_bpm, min_bpm=heart_rate.min_bpm, latest_bpm=heart_rate.latest_bpm, latest_time=heart_rate.synced_time,sample_count = heart_rate.sample_count) for heart_rate in heart_rates]
    res = LastDayHealthModel(
        sleep_sessions=sleep_sessions_model_list,
        steps=steps_model_list,
        heart_rates=heart_rates_model_list
    )

    return res.model_dump_json()
