
# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_wss_server.py 
@info: 消息模版
"""

from odd_asr_app import app
from log import logger
import threading;
import odd_asr_config as config
import asyncio

from odd_wss_server import start_wss_server

if __name__ == '__main__':

    def start_wss_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_wss_server())
        finally:
            loop.close()

    # start websocket server
    wss_thread = threading.Thread(target=start_wss_in_thread)
    wss_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
    wss_thread.start()
    logger.info("WebSocket server started.")

    # Start Flask server and listen for requests from any host
    # print(app.url_map)
    app.run(host=config.HOST, port=config.PORT, debug=config.Debug)
