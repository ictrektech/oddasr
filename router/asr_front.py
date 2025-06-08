import time
import wave

from flask import Blueprint, render_template, request, session, send_file
from mutagen.mp3 import MP3

import odd_asr_config as config
from log import logger

bp = Blueprint('front_asr', __name__, url_prefix='')

@bp.route('/asr_live.html')
def asr_live():
    return render_template('asr_live.html', servercfg=config.asr, username=session["user"])

@bp.route('/asr_file.html')
def asr_file():
    return render_template('asr_file.html', servercfg=config.asr)