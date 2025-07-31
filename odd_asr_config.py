## Flask server binding IP & port
HOST = "0.0.0.0"
PORT = 12345

## WebSocket server binding IP & port
WS_HOST = "0.0.0.0"
WS_PORT = 12346

## concurrent threads, 0 auto detect CPU cores
concurrent_thread = 0

## disable stream mode ASR
disable_stream = False

## working mode - Debug mode: True/False， Release mode: False/True
Debug = False

## enable gpu
enable_gpu = False

## asr stream config
asr_stream_cfg= { 'max_instance': 60 }
## asr file config
asr_file_cfg= { 'max_instance':2 }

## redis config
redis_enabled = False
redis_host = "127.0.0.1"
redis_port = 7379
redis_password = ""

## log config
log_file = "oddasr.log"
log_path = "logs/"
log_level = 10 # 10-debug 20-info 30-warn 40-error 50-crit

## token authertication config
asr={'asrserver':'/open', 'appid':'oddasrtest', 'secret':'oddasrtest'}
