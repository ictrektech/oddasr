import werkzeug.utils
import os
from datetime import timedelta
import odd_asr_exceptions
import time
from flask import Flask, request, jsonify

from log import logger
from odd_asr import OddAsr, OddAsrParamsStream, OddAsrParamsFile

odd_asr_params_stream = OddAsrParamsStream()
odd_asr_params_file = OddAsrParamsFile()

odd_asr = OddAsr(odd_asr_params_file, odd_asr_params_stream)

# 注册蓝图
def register_blueprints(new_app, path):
    for name in werkzeug.utils.find_modules(path):
        m = werkzeug.utils.import_string(name)
        new_app.register_blueprint(m.bp)
    new_app.errorhandler(odd_asr_exceptions.CodeException)(odd_asr_exceptions.handler)
    return new_app

# loop = EvLoop()
# subsrv = SubscribeServer(loop , host = config.redis_host,port = config.redis_port , password = config.redis_password, disabled = False)
app = Flask(__name__, static_url_path='')
register_blueprints(app, 'router')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

import router.asr_api

# for uwsgi start directly

if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    logger.info('server has started!')
    # loop.start()
    # subsrv.start(config.ws_local_ip, config.ws_local_port)

# app.jinja_env.filters['datetime'] = format_datetime
