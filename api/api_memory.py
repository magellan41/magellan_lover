from fastapi import APIRouter, Body

from entity.Memory import MidTermMemoryDto, LongTermMemoryDto
from orm.long_term_memory_orm import LongTermMemoryOrm
from orm.mid_term_memroy_orm import MidTermMemoryOrm

import logging

from utils.agent_util import init_agents

logger = logging.getLogger(__name__)


mid_term_memory_orm_obj = MidTermMemoryOrm()
long_term_memory_orm_obj = LongTermMemoryOrm()

router = APIRouter(tags=["记忆接口"])

@router.get("/api/memory/mid/list", summary="获取中期记忆数据", description="获取所有存活的中期记忆数据")
async def list_mid_term_memory() -> list[MidTermMemoryDto]:
    mid_term_memory_list = mid_term_memory_orm_obj.select_all()
    mid_term_memory_dto_list = [MidTermMemoryDto(
        id=mid_term_memory.id,
        content=mid_term_memory.content,
        create_time=mid_term_memory.create_time,
        status=mid_term_memory.status,
        alive_turn=mid_term_memory.alive_turn
    ) for mid_term_memory in mid_term_memory_list]
    return mid_term_memory_dto_list

@router.delete("/api/memory/mid/delete", summary="批量删除中期记忆", description="批量删除中期记忆ID为mid_term_memory_id的记录")
async def delete_mid_term_memory(mid_term_memory_id_list: list[int] = Body(..., description="中期记忆ID列表")):
    mid_term_memory_orm_obj.delete_all(mid_term_memory_id_list)
    init_agents()
    return {"message": "中期记忆删除成功"}



@router.get("/api/memory/long/list", summary="获取长期记忆数据", description="获取所有存活的长期记忆数据")
async def list_long_term_memory() -> list[LongTermMemoryDto]:
    long_term_memory_list = long_term_memory_orm_obj.select_all()
    long_term_memory_dto_list = [LongTermMemoryDto(
        id=long_term_memory.id,
        content=long_term_memory.content,
        create_time=long_term_memory.create_time,
        status=long_term_memory.status
    ) for long_term_memory in long_term_memory_list]
    return long_term_memory_dto_list

@router.delete("/api/memory/long/delete", summary="批量删除长期记忆", description="批量删除长期记忆ID为long_term_memory_id的记录")
async def delete_long_term_memory(long_term_memory_id_list: list[int] = Body(..., description="长期记忆ID列表")):
    long_term_memory_orm_obj.delete_all(long_term_memory_id_list)
    init_agents()
    return {"message": "长期记忆删除成功"}


