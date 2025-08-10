
from flask import Blueprint, render_template, request, session, redirect, send_from_directory, send_file

import odd_asr_config as config
from log import logger
from router.oddasr_session import session_required

bp = Blueprint('front', __name__, url_prefix='')
