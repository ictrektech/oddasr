# -*- coding: utf-8 -*-
""" 
@author: gaoyang 
@software: PyCharm 
@file: result.py 
@time: 2021/12/1 15:00
@info: 消息模版
"""


class Result:
    def __init__(self):
        self._result = {}

    def set_code(self, error_code):
        self._result['error_code'] = error_code

    def set_msg(self, error_desc):
        self._result['error_desc'] = error_desc

    def set_data(self, data):
        self._result['data'] = data

    @property
    def result(self):
        return self._result


def from_exc(exc):
    r = Result()
    r.set_code(exc.error_code)
    r.set_msg(exc.error_desc)
    return r.result


def from_data(data):
    r = Result()
    r.set_data(data)
    return r.result

