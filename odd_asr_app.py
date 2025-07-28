# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr_app.py 
@info: 消息模版
"""

import werkzeug.utils
import os
from datetime import timedelta
import odd_asr_exceptions
import odd_asr_config as config
from flask import Flask, request, jsonify

from log import logger
from odd_asr import OddAsrFile, OddAsrParamsFile

odd_asr_params_file = OddAsrParamsFile()
odd_asr_file_set = set()

def init_instance_file():
    global odd_asr_file_set
    for i in range(config.asr_file_cfg["max_instance"]):
        odd_asr_file = OddAsrFile(odd_asr_params_file)
        odd_asr_file_set.add(odd_asr_file)

def find_free_odd_asr_file():
    '''
    find a free odd_asr_file
    :param :
    :return:
    '''
    global odd_asr_file_set
    for odd_asr_file in odd_asr_file_set:
        if not odd_asr_file.is_busy():
            return odd_asr_file
        
    return None

# odd_loop = EvLoop()

# register blueprints
def register_blueprints(new_app, path):
    for name in werkzeug.utils.find_modules(path):
        m = werkzeug.utils.import_string(name)
        new_app.register_blueprint(m.bp)
    new_app.errorhandler(odd_asr_exceptions.CodeException)(odd_asr_exceptions.handler)
    return new_app

app = Flask(__name__, static_url_path='')
register_blueprints(app, 'router')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

import router.asr_api

# for uwsgi start directly

# if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
#     logger.info('server has started!')
#     odd_loop.start()
#     odd_wssrv.start(config.ws_local_ip, config.ws_local_port)

# logger.info('starting event loop !')
# odd_loop.start()
# logger.info('event loop has started!')
# asyncio.run(odd_wssrv.start(config.ws_local_ip, config.ws_local_port))

