
# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: main_server.py 
@info: 消息模版
"""
import argparse
import threading;
import asyncio

from odd_asr_app import app, init_stream_instance, init_file_instance
from log import logger
from odd_wss_server import start_wss_server

import odd_asr_config as config

if __name__ == '__main__':

    # parser = argparse.ArgumentParser(description='Control whether to enable streaming ASR')
    # parser.add_argument('--disable_stream', action='store_true', help='Disable streaming ASR')
    # args = parser.parse_args()

    def start_wss_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_wss_server())
        finally:
            loop.close()

    # start websocket server
    # if not args.disable_stream:
    if not config.disable_stream:
        init_stream_instance()
        wss_thread = threading.Thread(target=start_wss_in_thread)
        wss_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
        wss_thread.start()
        logger.info("WebSocket server started.")
    else:
        logger.info("WebSocket server disabled.")

    init_file_instance()
    # Start Flask server and listen for requests from any host
    # print(app.url_map)
    app.run(host=config.HOST, port=config.PORT, debug=config.Debug)
