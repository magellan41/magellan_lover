import json
from pathlib import Path
import logging
import configparser

import os
from utils import setting

logger = logging.getLogger(__name__)

def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取配置文件 {file_path} 失败: {e}")

def resolve_llm_config():
    try:
        llm_config_json = None
        with open(setting.LLM_CONFIG_PATH, 'r', encoding='utf-8') as f:
            llm_config_json = json.load(f)
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