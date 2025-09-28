# -*- coding: utf-8 -*-
""" 
@author: catherine@oddmeta.com 
@software: PyCharm 
@file: sensitivewords.py 
@time: 2021/12/1 16:25 
@info: 敏感词相关处理逻辑
"""
from json import dumps

from log import logger
from model import db
from model import sensitiveword as sw

class SensitiveWordManage(object):

    @classmethod
    def set_sensitive_word(cls, unique_id, sensitive_word):
        db_session = db.Session()

        sensitive_word_m = db_session.query(sw.CSensitiveWord).filter(sw.CSensitiveWord.unique_id == unique_id).first()
        if sensitive_word_m:
            sensitive_word_m.sensitive_word = dumps(sensitive_word, ensure_ascii=False)
        else:        
            sensitive_word_m = sw.CSensitiveWord(
                unique_id=unique_id,
                sensitive_word=dumps(sensitive_word, ensure_ascii=False)
            )
        db_session.merge(sensitive_word_m)
        db_session.commit()
        data = db.to_dict(sensitive_word_m)
        logger.info(f"set_sensitive_word:{data}")
        db_session.close()
        return data

    @classmethod
    def get_sensitive_word(cls, unique_id):
        logger.info(f"get_sensitive_word{unique_id}")
        db_session = db.Session()
        sensitive_word_m = db_session.query(sw.CSensitiveWord).filter(sw.CSensitiveWord.unique_id == unique_id).first()
        if not sensitive_word_m:
            db_session.close()
            return None
        data = db.to_dict(sensitive_word_m)
        db_session.close()
        return data

    @classmethod
    def del_sensitive_word(cls, unique_id):
        db_session = db.Session()
        sensitive_word_m = db_session.query(sw.CSensitiveWord).filter(sw.CSensitiveWord.unique_id == unique_id).first()
        if not sensitive_word_m:
            return
        db_session.delete(sensitive_word_m)
        db_session.commit()
        db_session.close()
        return {}

