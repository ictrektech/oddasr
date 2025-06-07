import logging
from logging import handlers
import platform

if platform.system() != "Windows":
    path = "/var/log/odd_asr.log"
else:
    path = "./odd_asr.log"

def _logging():
    FORMAT = "%(asctime)s %(levelname)s %(filename)s:%(lineno)s (%(process)s-%(thread)s) - %(message)s "
    DATE = '%Y-%m-%d %H:%M:%S'

    log = logging.getLogger(path)
    th = handlers.TimedRotatingFileHandler(filename=path, when='MIDNIGHT', backupCount=10, encoding='utf-8')

    format = logging.Formatter(FORMAT, DATE)

    th.setFormatter(format)
    log.addHandler(th)

    # stdout = logging.StreamHandler()
    # stdout.setFormatter(format)
    # log.addHandler(stdout)

    # if app.debug:
    #     enableProtoPrint = False
    #     if enableProtoPrint:
    #         logging.basicConfig(level=logging.DEBUG,
    #                             format=FORMAT,
    #                             datefmt=DATE)
    #     else:
    #         ch = logging.StreamHandler()
    #         ch.setFormatter(format)
    #         log.addHandler(ch)

    log.setLevel(logging.INFO)
    return log


logger = _logging()



