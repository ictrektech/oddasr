import logging
from odd_asr_app import app
import os
from log import logger
import threading;
import odd_asr_config as config
from logic.odd_asr_ws_server import OddAsrWsServer
import asyncio

odd_wssrv = OddAsrWsServer(None , host = config.redis_host,port = config.redis_port , password = config.redis_password, disabled = False)

def run_ws_server():
    asyncio.run(odd_wssrv.start(config.ws_local_ip, config.ws_local_port))

if __name__ == '__main__':

    # 启动 WebSocket 服务器线程
    ws_thread = threading.Thread(target=run_ws_server)
    ws_thread.daemon = True
    ws_thread.start()

    # Start Flask server and listen for requests from any host
    print(app.url_map)

    app.run(host=config.HOST, port=config.PORT, debug=config.Debug)