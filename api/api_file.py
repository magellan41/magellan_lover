import datetime
import os
import uuid

from fastapi import FastAPI, File, UploadFile, APIRouter, HTTPException

from utils import setting, env_util
from utils.env_util import write_env_var

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



