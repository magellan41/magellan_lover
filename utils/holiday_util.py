import datetime
import json
import os

import requests

from utils import setting



def _get_day_type(date_param:datetime.date):
    """
    获取日期的类型，包括工作日、节假日、工作日、类型
    :param date_param: 日期对象
    :return: 日期类型，包括weekday、weekend、public_holiday、transfer_workday，节假日名称/非节假日
    """
    year = date_param.year
    holiday_dir = os.path.join(setting.STATIC_PATH, "holiday")
    os.makedirs(holiday_dir, exist_ok=True)
    file_path = os.path.join(holiday_dir, f"{year}.json")
    holiday_api_url = f"https://unpkg.com/holiday-calendar/data/CN/{year}.json"
    if not os.path.exists(file_path):
        response = requests.get(holiday_api_url, timeout=10)
        response.raise_for_status()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)

    day_type = ""
    day_name = "非节假日"
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        dates = data.get('dates')
        for date in dates:
            # print(date)
            if date.get('date') == date_param:
                day_type = date.get('type')
                day_name = date.get('name_cn')
                break
    if day_type == "":
        # 判断是否是工作日
        is_work_day = date_param.weekday() < 5
        day_type = "weekday" if is_work_day else "weekend"
    day_type_map = {
        "weekday": "工作日",
        "weekend": "周末",
        "public_holiday": "节假日",
        "transfer_workday": "调休工作日"
    }
    return day_type_map.get(day_type, day_type), day_name


def _is_workday(date_param:datetime.date):
    """
    判断日期是否是工作日
    :param date_param: 日期对象
    :return: True 工作日，False 假期，日期类型，节假日名称/非节假日
    """
    day_type, day_name = _get_day_type(date_param)
    year = date_param.year
    if date_param == datetime.date(year, 2, 14):
        day_name = "情人节"
    elif date_param == datetime.date(year, 10, 31):
        day_name = "万圣节前夕"
    elif date_param == datetime.date(year, 12, 24):
        day_name="平安夜"
    elif date_param == datetime.date(year, 12, 25):
        day_name="圣诞节"
    return day_type in ["工作日", "调休工作日"], day_type, day_name

_update_day = datetime.date(2024, 1, 1)
_day_type = ""
_workday_flag = False
_day_name = ""

def today_status():
    """
    获取当前日期的类型，包括工作日、节假日、工作日、类型
    :return: True 工作日，False 假期，日期类型，节假日名称/非节假日，日期字符串
    """
    global _update_day, _workday_flag, _day_type, _day_name
    if _update_day != datetime.date.today():
        _workday_flag, _day_type, _day_name = _is_workday(datetime.date.today())
        _update_day = datetime.date.today()
    return _workday_flag, _day_type, _day_name, _update_day.strftime("%Y-%m-%d")
