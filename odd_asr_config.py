HOST = "0.0.0.0"
PORT = 12345

WS_HOST = "0.0.0.0" # "127.0.0.1"
WS_PORT = 12346

concurrent_thread = 8
disable_stream = False

Debug = False

enable_gpu = False

asr_stream_cfg= { 'max_instance': 2 }
asr_file_cfg= { 'max_instance':2 }

redis_enabled = False
redis_host = "127.0.0.1"
redis_port = 7379
redis_password = ""

log_file = "oddasr.log"
log_path = "logs/"
log_level = 10 # 10-debug 20-info 30-warn 40-error 50-crit

asr={'asrserver':'/open', 'appid':'oddasrtest', 'secret':'oddasrtest'}
