import json
from pathlib import Path
import logging
import configparser

import os
from utils import setting
from utils.common_util import safe_json_loads

logger = logging.getLogger(__name__)


def resolve_llm_config():
    try:
        llm_config_json = None
        with open(setting.LLM_CONFIG_PATH, 'r', encoding='utf-8') as f:
            llm_config_json = safe_json_loads(f.read())
        if not llm_config_json:
            logger.error("LLM 配置文件为空")
            raise Exception("LLM 配置文件为空")
        return llm_config_json
    except Exception as e:
        logger.error(f"读取 LLM 配置文件失败: {e}")
        raise Exception("读取 LLM 配置文件失败")

def get_db_config():
    config = configparser.ConfigParser()
    config.read(setting.DB_CONFIG_PATH, encoding='utf-8')
    
    db_config = dict(config.items('database'))
    
    db_config['port'] = config.getint('database', 'port') 
    
    return db_config