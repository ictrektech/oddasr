import sys

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import odd_asr_config as config

sys.path.append('../')

if config.db_cfg["db_engine"] == "sqlite":
    e = create_engine("sqlite:///" + config.db_cfg["db_name"], pool_recycle=3600, pool_pre_ping=True)
elif config.db_cfg["db_engine"] == "mysql":
    e = create_engine(
        "mysql+pymysql://" + config.db_cfg["db_user"] + ":" + config.db_cfg["db_password"] + "@" + config.db_cfg["db_host"] + "/" + config.db_cfg["db_name"] + "?charset=utf8mb4",
        pool_recycle=3600, pool_pre_ping=True)  # , echo=True)
elif config.db_cfg["db_engine"] == "openGauss":
    e = create_engine(
        'opengauss+psycopg2://' + config.db_cfg["db_user"] + ":" + config.db_cfg["db_password"] + "@"
        + config.db_cfg["db_host"] + ':' + config.db_cfg["db_port"] + "/" + config.db_cfg["db_name"],
        pool_recycle=3600, pool_pre_ping=True)

Session = sessionmaker(bind=e)
Base = declarative_base()

def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def to_json(all_vendors):
    v = [ven.to_dict() for ven in all_vendors]
    return v
