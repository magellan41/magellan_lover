import logging

from starlette.responses import JSONResponse

from entity.location import LocationModel, LocationPoiQueryModel
from utils import location_util

logger = logging.getLogger(__name__)

from fastapi import APIRouter
router = APIRouter(tags=["地理位置数据接口"])

from orm.location_orm import LocationOrm
location_orm_obj = LocationOrm()

@router.post("/api/location/load", summary="上传地理位置数据", description="上传地理位置数据")
async def load_location(data: LocationModel):
    res = location_util.reverse_geocoding(data.longitude, data.latitude)
    address = res.split("：")[1]
    logger.debug(f"location load: {data}, address: {address}")
    location_orm_obj.insert(data, address)
    return JSONResponse(content={"message": res})


@router.post("/api/location/query", summary="查询地理位置数据", description="查询地理位置数据")
async def query_location(data: LocationPoiQueryModel):
    res = location_util.reverse_geocoding(data.longitude, data.latitude, data.poi_type_list)
    address = res.split("：")[1]
    logger.debug(f"location query: {data}, address: {address}")
    return JSONResponse(content={"message": res})

