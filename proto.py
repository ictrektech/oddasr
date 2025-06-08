# -*- coding: utf-8 -*-
""" 
@author: catherine wei
@contact: EMAIL@contact: catherine@oddmeta.com
@software: PyCharm 
@file: result.py 
@time: 2025/6/9 15:00
@info: 消息模版
"""

# websocket common reponse struct.
class TCMDCommonRes:
    msg_type=""
    msg_id=""
    error_code = 0
    error_desc=""

    def __init__(self , msg_id, msg_type) -> None:
        self.msg_id = msg_id
        self.msg_type = msg_type

class TCMDApplyAsrRes:
    msg_type="MSG_APPLY_ASR_RES"
    msg_id=""
    error_code = 0
    error_desc=""
    session_id=""

    def __init__(self , msg_id) -> None:
        self.msg_id = msg_id


class TASRRecogTextParam:
    text=""
    bg=0
    ed=0
    fin=0

    def __init__(self) -> None:
        pass

def obj_to_dict(self):
    return dict((name, getattr(self, name)) for name in dir(self) if not name.startswith('__'))


