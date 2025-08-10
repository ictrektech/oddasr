## Flask server binding IP & port
HOST = "127.0.0.1"
PORT = 12345
PORT = 7501
PORT = 8701

## WebSocket server binding IP & port
WS_HOST = "127.0.0.1"
WS_PORT = 8101

## working mode - Debug mode: True/False， Release mode: False/True
Debug = False

odd_asr_cfg = {
    ## load model and allocate memory on startup
    "preload_model": True,
    ## enable gpu
    "enable_gpu": False,
    ## disable stream mode ASR
    "disable_stream": False,
    ## concurrent threads, 0 auto detect CPU cores
    "concurrent_thread": 0,
    ## asr stream config
    "asr_stream_cfg": { 'max_instance': 1 },
    ## asr file config
    "asr_file_cfg": { 'max_instance':0 },
    ## HTTPS configuration
    "enable_https": False,
    "ssl_cert_path": "scripts/cert.pem",
    "ssl_key_path": "scripts/key.pem",
}

db_cfg = {
    "db_engine": "sqlite",
    "db_name": "oddasr.db",
    "db_user": "",
    "db_password": "",
    "db_host": "",
    "db_port": "",
}

## redis config
redis_cfg = {
    "redis_enabled": False,
    "redis_host": "127.0.0.1",
    "redis_port": 7379,
    "redis_password": "",
}

## log config
log_file = "oddasr.log"
log_path = "logs/"
log_level = 10 # 10-debug 20-info 30-warn 40-error 50-crit

## token authertication config
asr={'liveasr':'', 'appid':'oddasrtest', 'secret':'oddasrtest'}
Users = 'oddasr_users.json'
