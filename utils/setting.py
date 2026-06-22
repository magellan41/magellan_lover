import os

ROUT_PATH = ''
CONFIG_PATH = ''
LLM_CONFIG_PATH = ''
DB_CONFIG_PATH = ''
UPLOAD_PATH = ''
STATIC_PATH = ''
VOICE_PATH = ''
IMAGE_PATH = ''

def init(root_path):
    global ROUT_PATH
    global CONFIG_PATH
    global LLM_CONFIG_PATH
    global DB_CONFIG_PATH
    global UPLOAD_PATH
    global VOICE_PATH
    global IMAGE_PATH
    global STATIC_PATH

    ROUT_PATH = root_path
    CONFIG_PATH = os.path.join(root_path, 'config')
    os.makedirs(ROUT_PATH, exist_ok=True)
    LLM_CONFIG_PATH = os.path.join(CONFIG_PATH, 'llm_config.json')
    DB_CONFIG_PATH = os.path.join(CONFIG_PATH, 'db.ini')

    STATIC_PATH = os.path.join(root_path, "static")
    os.makedirs(STATIC_PATH, exist_ok=True)
    UPLOAD_PATH = os.path.join(STATIC_PATH, 'uploads')
    os.makedirs(UPLOAD_PATH, exist_ok=True)
    VOICE_PATH = os.path.join(STATIC_PATH, "voice")
    os.makedirs(VOICE_PATH, exist_ok=True)
    IMAGE_PATH = os.path.join(STATIC_PATH, "image")
    os.makedirs(IMAGE_PATH, exist_ok=True)


