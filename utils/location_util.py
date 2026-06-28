import os

import requests

from orm.location_orm import LocationOrm
location_orm_obj = LocationOrm()

POI_TYPE_CODE_DIC = {
    "餐饮服务": "050000",
    "中餐厅": "050100",
    "外国餐厅": "050200",
    "快餐厅": "050300",
    "休闲餐饮场所": "050400",
    "购物服务": "060000",
}

def reverse_address(longitude, latitude):
    reverse_geocode_url = "https://restapi.amap.com/v3/geocode/regeo"
    param = {
        "key": os.getenv("AMAP_API_KEY"),
        "location": f"{longitude},{latitude}",
        "output": "json"
    }
    response = requests.get(reverse_geocode_url, params=param)
    response.raise_for_status()
    response_json = response.json()
    if response_json["status"] != "1":
        raise RuntimeError(f"地址解析失败，错误信息：{response_json['info']}")
    return response_json["regeocode"]["formatted_address"]


def reverse_geocoding(poi_type_list=None):
    reverse_geocode_url = "https://restapi.amap.com/v3/geocode/regeo"
    location = location_orm_obj.select_last()
    if not location:
        raise ValueError("未查询到位置信息")
    param = {
        "key": os.getenv("AMAP_API_KEY"),
        "location": f"{location.longitude},{location.latitude}",
        "output": "json"
    }
    if poi_type_list:
        poi_code_list = []
        for poi_type in poi_type_list:
            if poi_type not in POI_TYPE_CODE_DIC:
                raise ValueError(f"不支持的地点类型：{poi_type}")
            poi_code_list.append(POI_TYPE_CODE_DIC[poi_type])
        poitype = "|".join(poi_code_list)
        param["poitype"] = poitype
        param["extensions"] = "all"
        param["radius"] = "1000"
    response = requests.get(reverse_geocode_url, params=param)
    response.raise_for_status()
    data = response.json()
    if data["status"] == "1":
        res = f"当前用户位置：{data['regeocode']['formatted_address']}"
        if poi_type_list:
            pois = data["regeocode"]["pois"]
            if pois:
                pois_parse_list = [f"地点名称：{poi['name']}|地址：{poi['address']}||电话：{poi.get('tel', '无')}|方向：{poi.get('direction', '无')}|距离：{poi.get('distance', '无')}" for poi in pois]
                res += f"，为您找到{len(pois)}个可能感兴趣的地点：\n{'\n'.join(pois_parse_list)}"
            else:
                res += "，附近没有找到您想查询的地点"
        return res
    else:
        raise RuntimeError(f"地址解析失败，错误信息：{data['info']}")

