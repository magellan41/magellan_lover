import json
import os.path
import threading

from utils import setting

env_lock = threading.Lock()
env_path = os.path.join(setting.CONFIG_PATH, 'env.json')

def read_env_var(var_name):
    env_json = {}
    if not os.path.exists(env_path):
        return None
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            env_json = json.load(f)
    except (json.JSONDecodeError, ValueError):
        pass
    env_var = env_json.get(var_name)
    return env_var

def read_env_vars(var_names):
    env_json = {}
    if not os.path.exists(env_path):
        return None
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            env_json = json.load(f)
    except (json.JSONDecodeError, ValueError):
        pass
    env_vars = {var_name: env_json.get(var_name, "未找到该配置项") for var_name in var_names}
    return env_vars

def write_env_var(var_name, value):
    with env_lock:
        env_json = {}
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_json = json.load(f)
            except (json.JSONDecodeError, ValueError):
                pass
        env_json[var_name] = value
        with open(env_path, 'w', encoding='utf-8') as f:
            json.dump(env_json, f, ensure_ascii=False, indent=4)

def write_env_vars(var_names, values):
    with env_lock:
        env_json = {}
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_json = json.load(f)
            except (json.JSONDecodeError, ValueError):
                pass
        for var_name, value in zip(var_names, values):
            env_json[var_name] = value
        with open(env_path, 'w', encoding='utf-8') as f:
            json.dump(env_json, f, ensure_ascii=False, indent=4)

