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
    # res = LastDayHealthModel(
    #     sleep_sessions=sleep_sessions_model_list,
    #     steps=steps_model_list,
    #     heart_rates=heart_rates_model_list
    # )
    sleep_data_str = "【睡眠数据】\n"
    for sleep_session in sleep_sessions:
        sleep_data_str += f"本轮睡眠开启时间:{sleep_session.start_time}, 本轮睡眠结束时间:{sleep_session.end_time}\n"
        sleep_data_str += "\n\t".join([f"{stage.start_time}至{stage.end_time}处于{stage.stage}阶段" for stage in sleep_session.stages])
    step_data_str = "【步数数据】\n" + "\n".join([f"在{step.synced_time}时步数为{step.steps}步" for step in steps])
    heart_rate_data_str = "【心率数据】\n" + "\n".join([f"在{heart_rate.synced_time}时最大心率{heart_rate.max_bpm}pm, 最小心率{heart_rate.min_bpm}pm, 平均心率{heart_rate.avg_bpm}pm, 当时心率{heart_rate.latest_bpm}pm" for heart_rate in heart_rates])

    res = f"{sleep_data_str}\n{step_data_str}\n{heart_rate_data_str}"
    return res
