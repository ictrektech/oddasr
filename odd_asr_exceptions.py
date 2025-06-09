# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: odd_asr_exceptions.py 
@info: 消息模版
"""

from flask import jsonify
import odd_asr_result

# 以下是c++的错误的PYTHON实现.

# Format: A.BBB.C.DDD

# A: TYPE [1,9]
EM_ERR_TYPE_C = "1"         #caller error
EM_ERR_TYPE_S = "2"         #callee error
EM_ERR_TYPE_T = "3"   

# BBB: MOD [000,999]
EM_ERR_MOD_LLM = "001"
EM_ERR_MOD_ASR = "002"
EM_ERR_MOD_TTS = "003"
EM_ERR_MOD_EMOTION = "004"
EM_ERR_MOD_MEMORY = "005"

# C.DDD: CODE [0000,9999]

g_mai_err_api = {}

def DEF_ERR(MOD,TYPE,CODE,DESC = ""):
    error_code = (int)(TYPE + MOD + CODE)
    g_mai_err_api[error_code] = DESC
    return error_code

def mai_err_name(error_code):
    ns = globals()
    for name in ns:
        if ns[name] == error_code:
            return name
    return ""

def mai_err_desc(error_code):
    if error_code in g_mai_err_api:
        return g_mai_err_api[error_code]
    return ""
  
#错误码定义如下:
## client errors
EM_ERR_ASR_ARGS_ERROR                             = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0001")
EM_ERR_ASR_SESSION_ID_EXIST                       = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0002")
EM_ERR_ASR_SESSION_ID_NOVALID                     = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0003")
EM_ERR_ASR_MINUTES_MOID_ERROR                     = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_C , "0004")
## server errors
EM_ERR_ASR_SERVER_ERROR                           = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0001", "timeout")
EM_ERR_ASR_WS_NONE                                = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0002", "reply timeout")
EM_ERR_ASR_SYNC_HOTWORDS_ERROR                    = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0003")
EM_ERR_ASR_METHOD_NOT_SUPPORT                     = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0004")
EM_ERR_ASR_MINUTES_STATUS_ERROR                   = DEF_ERR(EM_ERR_MOD_ASR, EM_ERR_TYPE_S , "0005")


class CodeException(Exception):

    def __init__(self, error_code, error_desc):
        super().__init__()
        self.error_code = error_code
        self.error_desc = error_desc

    def __str__(self):
        return "%d - %s" % (self.error_code, self.error_desc)

    def __unicode__(self):
        return u"%d - %s" % (self.error_code, self.error_desc)


class ResultException(CodeException):
    """异常返回"""
    def __init__(self, error_code=EM_ERR_ASR_ARGS_ERROR, error_desc=mai_err_name(EM_ERR_ASR_ARGS_ERROR)):
        super(ResultException, self).__init__(error_code, error_desc)


def handler(exc):
    return jsonify(odd_asr_result.from_exc(exc))
