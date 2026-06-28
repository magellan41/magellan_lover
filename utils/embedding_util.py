import os
import time
from http import HTTPStatus
from typing import Dict, List, Any

import dashscope
from chromadb import EmbeddingFunction, Embeddings

from utils import agent_util, common_util, env_util

import logging
logger = logging.getLogger(__name__)


class AliyunFusionEmbedding(EmbeddingFunction):
    def __init__(self, api_key: str | None = None, model: str = "qwen3-vl-embedding", dimension: int = 1024):
        dashscope.api_key = common_util.get_true_value_in_env(env_util.read_env_var("embedding_api_key"))
        self.model = model
        self.dimension = dimension
        self.max_retries = 3

    def _call_with_retry(self, input_data):
        for attempt in range(self.max_retries):
            try:
                resp = dashscope.MultiModalEmbedding.call(
                    model=self.model,
                    input=input_data,
                    enable_fusion=True,
                    dimension=self.dimension
                )
                if resp.status_code == HTTPStatus.OK:
                    return resp.output['embeddings'][0]['embedding']
                else:
                    logger.warning(f"API 调用失败 (attempt {attempt + 1}): {resp.message}")
                    if attempt == self.max_retries:
                        raise ValueError(f"API 调用最终失败: {resp.message}")
                    time.sleep(1 * (attempt + 1))  # 退避等待
            except Exception as e:
                logger.warning(f"请求异常 (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries:
                    raise
                time.sleep(1 * (attempt + 1))

    def __call__(self, input: list[list[Dict[str, str]]]) -> Embeddings:
        embeddings = []
        for item in input:
            try:
                embedding = self._call_with_retry(item)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"处理 {item} 失败: {e}")
                raise RuntimeError(f"处理 {item} 时出错: {e}") from e
        return embeddings

_embed_fn = AliyunFusionEmbedding()

import chromadb
from utils import setting

_client = chromadb.PersistentClient(path=os.path.join(setting.CONFIG_PATH, "meme_db"), settings=chromadb.Settings(anonymized_telemetry=False))
_memes_collection_name = "memes"
_memes_collection = _client.get_or_create_collection(
    name=_memes_collection_name,
    embedding_function=_embed_fn,   # 首次创建时使用，已存在时此参数被忽略
    metadata={"hnsw:space": "cosine"}
)

def save_meme_to_db(image_id: int, image_path: str):
    item_to_base64 = common_util.base64_encode(image_path)
    logger.debug(f"转换为 base64: {item_to_base64}")
    image_description = agent_util.agents["memes"].chat(item_to_base64, "system")
    logger.debug(f"图片描述: {image_description}")
    input_data = [
        {'image': item_to_base64},
        {'text': image_description}
    ]
    embedding_vector = _embed_fn([input_data])[0]
    _memes_collection.add(
        ids=[str(image_id)],
        embeddings=[embedding_vector],  # 手动传入向量
        documents=[image_description],  # 只存文本，用于展示或后续处理
        metadatas=[{
            "image_id": image_id,
            "description": image_description
        }]
    )

def query_memes_by_text(query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
    try:
        input_data = [{'text': query_text}]
        query_embedding = _embed_fn([input_data])[0]
        results = _memes_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents"]  # 只需要描述，id 默认返回
        )
        top_results = []
        if results['ids'] and results['ids'][0]:
            for idx, doc_id in enumerate(results['ids'][0]):
                top_results.append({
                    "id": int(doc_id),  # 存的时候是 str，转回 int
                    "description": results['documents'][0][idx] if results['documents'] else ""
                })
        return top_results
    except Exception as e:
        logger.error(f"查询向量库失败: {e}")
        raise RuntimeError(f"查询向量库失败: {e}") from e
