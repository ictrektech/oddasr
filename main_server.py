
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

from odd_asr_app import init_instance_file, app
from odd_wss_server import init_instances_stream, start_wss_server
from log import logger

import odd_asr_config as config

if __name__ == '__main__':

    def start_wss_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_wss_server())
        finally:
            loop.close()

    # start websocket server
    if not config.odd_asr_cfg["disable_stream"]:
        wss_thread = threading.Thread(target=start_wss_in_thread)
        wss_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
        wss_thread.start()
        logger.info("WebSocket server started.")
    else:
        logger.info("WebSocket server disabled.")

    # Start Flask server with HTTPS support
    init_instance_file()
    logger.info(f"Starting server on {'https' if config.odd_asr_cfg['enable_https'] else 'http'}://{config.HOST}:{config.PORT}")
    if config.odd_asr_cfg["enable_https"]:
        ssl_context = (config.odd_asr_cfg["ssl_cert_path"], config.odd_asr_cfg["ssl_key_path"])
        app.run(host=config.HOST, port=config.PORT, ssl_context=ssl_context, debug=config.Debug)
    else:
        app.run(host=config.HOST, port=config.PORT, debug=config.Debug)

    # Start Flask server and listen for requests from any host
    # print(app.url_map)
