import logging
from odd_asr_app import app
import os
from log import logger
import threading;

if __name__ == '__main__':
    # Start Flask server and listen for requests from any host
    print(app.url_map)
    app.run(host='0.0.0.0', port=12340, debug=False)