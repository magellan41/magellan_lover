import json
import os.path
import threading

from utils import setting

_env_lock = threading.Lock()
_env_path = os.path.join(setting.CONFIG_PATH, 'env.json')

_env_json = {}

def init_env():
    global _env_json
    with _env_lock:
        if os.path.exists(_env_path):
            with open(_env_path, 'r') as f:
                _env_json = json.load(f)

def read_env_var(var_name):
    global _env_json
    if var_name in _env_json:
        return _env_json.get(var_name)
    init_env()
    if var_name in _env_json:
        return _env_json.get(var_name)
    return "未找到该配置项"

def read_env_vars(var_names):
    global _env_json
    res = {}
    try:
        for var_name in var_names:
            res[var_name] = _env_json[var_name]
        return res
    except:
        init_env()
        res = {var_name: _env_json.get(var_name, "未找到该配置项") for var_name in var_names}
        return res

def write_env_var(var_name, value):
    with _env_lock:
        global _env_json
        _env_json[var_name] = value
        with open(_env_path, 'w', encoding='utf-8') as f:
            json.dump(_env_json, f, ensure_ascii=False, indent=4)

def write_env_vars(var_names, values):
    with _env_lock:
        global _env_json
        for var_name, value in zip(var_names, values):
            _env_json[var_name] = value
        with open(_env_path, 'w', encoding='utf-8') as f:
            json.dump(_env_json, f, ensure_ascii=False, indent=4)

