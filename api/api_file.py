import datetime
import os
import uuid
from typing import Any

from fastapi import FastAPI, File, UploadFile, APIRouter, HTTPException, BackgroundTasks, Query

from utils import setting, env_util, common_util, embedding_util
from utils.env_util import write_env_var

import logging
logger = logging.getLogger(__name__)


router = APIRouter(tags=["文件接口"])


async def save_file_to_disk(file: UploadFile, file_parent_path: str = "uploads", allowed_extensions: set = None, save_name: str = None):
    """底层通用的文件保存逻辑"""
    # 后缀名
    file_extension = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'bin'
    if allowed_extensions is not None and file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"文件扩展名 {file_extension} 不被允许")

    # 使用 UUID 生成唯一文件名，并拼接后缀名

    if save_name is None:
        new_filename = f"{uuid.uuid4()}.{file_extension}"
    else:
        new_filename = f"{save_name}.{file_extension}"
    file_path = os.path.join(file_parent_path, new_filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return new_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
ALLOWED_OWNER = {"user", "agent"}
@router.post("/api/file/uploads/avatar/{owner}", summary="上传头像", description="上传用户头像或智能体头像,owner 可以是 user 或 agent, 头像格式只能是 png, jpg, jpeg, gif")
async def upload_file(owner: str, file: UploadFile = File(...)):
    if owner not in ALLOWED_OWNER:
        raise HTTPException(status_code=400, detail=f"owner {owner} 不被允许，只能是 user 或 assistant")
    file_parent_path = os.path.join(setting.UPLOAD_PATH, "avatar")
    os.makedirs(file_parent_path, exist_ok=True)
    new_filename = await save_file_to_disk(file, file_parent_path, allowed_extensions=ALLOWED_EXTENSIONS)
    url = f'/static/uploads/avatar/{new_filename}'
    write_env_var(f"avatar_{owner}", url)
    return {
        "original_filename": file.filename,
        "saved_filename": new_filename,
        "url": url
    }

@router.post("/api/file/uploads/common", summary="上传通用文件", description="上传通用文件, 例如图片, 文档等")
async def upload_file(file: UploadFile = File(...)):
    file_parent_path = os.path.join(setting.UPLOAD_PATH, "common", datetime.datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(file_parent_path, exist_ok=True)
    new_filename = await save_file_to_disk(file, file_parent_path)
    url = f'/static/uploads/common/{datetime.datetime.now().strftime("%Y-%m-%d")}/{new_filename}'
    return {
        "original_filename": file.filename,
        "saved_filename": new_filename,
        "url": url
    }

@router.post("/api/file/uploads/character_image", summary="上传角色图片", description="上传角色图片,用于生成角色自拍")
async def upload_character_image_file(file: UploadFile = File(...)):
    file_extension = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'bin'
    file_parent_path = os.path.join(setting.UPLOAD_PATH, "character_image")
    os.makedirs(file_parent_path, exist_ok=True)
    new_filename = await save_file_to_disk(file, file_parent_path, allowed_extensions=ALLOWED_EXTENSIONS, save_name="character_image")
    url = f'/static/uploads/character_image/character_image.{file_extension.lower()}'
    env_util.write_env_vars(["character_image_path", "character_image_url"], [os.path.join(file_parent_path, new_filename), url])
    return {
        "original_filename": file.filename,
        "saved_filename": new_filename,
        "url": url
    }

import asyncio
from orm.memes_orm import MemesOrm
memes_orm_obj = MemesOrm()

def sync_meme_to_vector_db(file_info_list: list[dict[str, Any]]):
    for file_info in file_info_list:
        id = file_info["id"]
        file_path = file_info["file_path"]
        try:
            embedding_util.save_meme_to_db(id, file_path)
            logger.info(f"表情包 {file_info['name']} 成功保存到向量数据库")
            memes_orm_obj.mark_save_in_vector([id])
        except Exception as e:
            logger.error(f"表情包 {file_info['name']} 失败: {e}")
            memes_orm_obj.mark_fail_save_in_vector([id])



@router.post("/api/file/uploads/memes", summary="上传表情包", description="上传表情包,用于虚拟角色回复")
async def upload_memes_file(files: list[UploadFile] = File(..., max_length=9, description="一次最多上传9张图片"),
                            background_tasks: BackgroundTasks = None,):
    file_parent_path = os.path.join(setting.UPLOAD_PATH, "memes")
    os.makedirs(file_parent_path, exist_ok=True)
    urls = []
    success_names = []
    file_info_list = []
    for file in files:
        content = await file.read()
        md5_val = common_util.get_md5_val(content)

        existing_meme = memes_orm_obj.select_by_md5_val(md5_val)
        if existing_meme is not None:
            urls.append(existing_meme.url)
            success_names.append(existing_meme.url)
            continue
        try:
            await file.seek(0)
            new_filename = await save_file_to_disk(file, file_parent_path, allowed_extensions=ALLOWED_EXTENSIONS)
            url = f'/static/uploads/memes/{new_filename}'
            file_path = os.path.join(file_parent_path, new_filename)
            id = memes_orm_obj.insert(file_path, url, md5_val)
            file_info_list.append({"id": id, "file_path": file_path, "name": file.filename})
            success_names.append(file.filename)
        except Exception as e:
            logger.error(f"上传表情包 {file.filename} 失败: {e}")

    if file_info_list:
        async def run_sync_task():
            await asyncio.to_thread(sync_meme_to_vector_db, file_info_list)

        background_tasks.add_task(run_sync_task)

    return {
        "status": "received",
        "total_count": len(files),
        "success_count": len(success_names),
        "success_names": success_names
    }

@router.get("/api/file/query/memes", summary="查询表情包", description="【文搜图】根据文本查询表情包")
async def query_memes_query(query_text: str = Query(..., description="查询文本")):
    results = embedding_util.query_memes_by_text(query_text)
    logger.debug(str(results))
    return results


