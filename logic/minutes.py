from sqlalchemy import or_, desc, func

from log import logger
from model.db import Session
from model.meeting import CMeeting
from model.meeting import MEETING_OPEN_STATUS_INIT, MEETING_OPEN_STATUS_ENCODE, MEETING_OPEN_STATUS_FINISH, \
    MEETING_OPEN_STATUS_EXCEPTION
from model.meeting import MEETING_STATUS_APPLY, MEETING_STATUS_ENCODE, MEETING_STATUS_FINISH, MEETING_STATUS_MINUTES
from model.text import CText
from sqlalchemy import or_, desc, func

from log import logger
from model.db import Session
from model.meeting import CMeeting
from model.meeting import MEETING_OPEN_STATUS_INIT, MEETING_OPEN_STATUS_ENCODE, MEETING_OPEN_STATUS_FINISH, \
    MEETING_OPEN_STATUS_EXCEPTION
from model.meeting import MEETING_STATUS_APPLY, MEETING_STATUS_ENCODE, MEETING_STATUS_FINISH, MEETING_STATUS_MINUTES
from model.text import CText


# apply res suc.
class CStorageMinutes:

    @classmethod
    def applyMeetingRes(self, strSessionId: str, strMeetingE164: str, strMeetingAlias: str, strBeginTime: str,
                        bIsOpenMinutes: bool):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strSessionId).first()
        if meeting == None:
            meeting = CMeeting()
            meeting.session_id = strSessionId
            meeting.meeting_begin_time = strBeginTime
            meeting.meeting_alias = strMeetingAlias
            meeting.meeting_type = 2
            meeting.meeting_status = MEETING_STATUS_APPLY
            if bIsOpenMinutes:
                meeting.meeting_status = MEETING_STATUS_MINUTES
            session.add(meeting)
            session.commit()
            session.close()
        else:
            if bIsOpenMinutes and meeting.meeting_status == MEETING_STATUS_APPLY:
                meeting.meeting_status = MEETING_STATUS_MINUTES
                session.commit()
            session.close()

    @classmethod
    def openMeetingMinutes(self, strSessionId: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strSessionId).first()
        if meeting != None and meeting.meeting_status == MEETING_STATUS_APPLY:
            meeting.meeting_status = MEETING_STATUS_MINUTES
            session.commit()
        session.close()

    @classmethod
    def getAllMeetingsByKey(self, index, num, key=None):
        session = Session()
        count = 0
        qc = session.query(func.count(CMeeting.session_id))
        q = session.query(CMeeting)

        if key != None and key != "":
            qc = qc.filter(or_(CMeeting.meeting_alias.like('%' + key + '%'),
                               CMeeting.meeting_addr.like('%' + key + '%'),
                               CMeeting.meeting_participant.like('%' + key + '%'),
                               CMeeting.session_id == key))
            qc = qc.filter(CMeeting.meeting_status >= 0)
            q = q.filter(or_(CMeeting.meeting_alias.like('%' + key + '%'),
                             CMeeting.meeting_addr.like('%' + key + '%'),
                             CMeeting.meeting_participant.like('%' + key + '%'),
                             CMeeting.session_id == key))
            q = q.filter(CMeeting.meeting_status >= 0)

        q = q.order_by(desc(CMeeting.id))
        count = qc.scalar()
        list = q.limit(num).offset((index) * num).all()
        for meeting in list:
            if meeting.meeting_type == 1:
                split_strs = meeting.meeting_alias.split('/')
                meeting.meeting_alias = split_strs[-1]
                # 查找第一个_
                pos = meeting.meeting_alias.find('_')
                meeting.meeting_alias = meeting.meeting_alias[pos + 1:]
        session.close()
        return count, list

    @classmethod
    def addMeetingText(self, strMoid: str, strTermE164: str,
                       strTermAlias: str, nBg: int, nEd: int, strText: str, nFlag: int, nTime: int , nSign:int):
        session = Session()
        text = CText()
        text.session_id = strMoid
        text.text_term_e164 = strTermE164
        text.text_term_alias = strTermAlias
        text.text_bg_time = nBg
        text.text_ed_time = nEd
        text.text_content = strText
        text.text_time = nTime
        text.text_flag = nFlag
        text.text_sign = nSign
        session.add(text)
        session.commit()
        session.close()

    @classmethod
    def opMeetingText(self, strMoid: str,  strTermE164: str,
                       strTermAlias: str, nBg: int, nEd: int, strText: str,  nTime: int , nMixBg:int , nMixEd:int):
        session = Session()
        session.query(CText).filter(CText.session_id == strMoid,
                                              CText.text_bg_time >= nMixBg, 
                                              CText.text_sign == 1 ,
                                              CText.text_ed_time <= nMixEd).update({CText.text_sign:2})
        
        text = CText()
        text.session_id = strMoid
        text.text_term_e164 = strTermE164
        text.text_term_alias = strTermAlias
        text.text_bg_time = nBg
        text.text_ed_time = nEd
        text.text_content = strText
        text.text_time = nTime
        text.text_flag = 0
        text.text_sign = 3
        session.add(text)
        session.commit()   
        session.close()
    
    @classmethod
    def addMeetingTextVad(self , strMoid: str,  strTermE164: str,
                       strTermAlias: str, nBg: int, nEd: int, strText: str,  nTime: int , nTermTb:int , nTermTd:int , nSign:int):
        session = Session()
        text = CText()
        text.session_id = strMoid
        text.text_term_e164 = strTermE164
        text.text_term_alias = strTermAlias
        text.text_bg_time = nBg
        text.text_ed_time = nEd
        text.text_content = strText
        text.text_time = nTime
        text.text_flag = 0
        text.text_sign = nSign
        text.text_term_tb_time = nTermTb
        text.text_term_td_time = nTermTd
        session.add(text)
        session.commit()   
        session.close()               

    @classmethod
    def opMeetingFinish(self, strSessionId: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strSessionId).first()
        if meeting != None:
            meeting.meeting_op_status = 1
            session.commit()
        session.close()
   

    @classmethod
    def updateMeetingText(self, strId: str, strText: str):
        logger.info(f"strId:{strId},strText:{strText}")
        session = Session()
        meeting = session.query(CText).filter(CText.text_id == strId).first()
        if meeting != None:
            meeting.text_content = strText
            session.commit()
        session.close()

    @classmethod
    def updateMeetingEnd(self, strMoid: str, strEndTime: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strMoid).first()
        if meeting != None and meeting.meeting_status == MEETING_STATUS_MINUTES:
            meeting.meeting_status = MEETING_STATUS_ENCODE
            meeting.meeting_end_time = strEndTime
            session.commit()
        session.close()

    @classmethod
    def updateMeetingFinish(self, strMoid: str, strAudioResId: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strMoid).first()
        if meeting != None and meeting.meeting_status == MEETING_STATUS_ENCODE:
            meeting.meeting_status = MEETING_STATUS_FINISH
            meeting.meeting_audio_res_id = strAudioResId
            session.commit()
        session.close()

    @classmethod
    def getMeetingInfoById(self, meeting_id: int):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.id == meeting_id).first()

        return meeting

    @classmethod
    def getUnEncodeMeetingMoids(self):
        session = Session()
        moids = session.query(CMeeting.session_id).filter(CMeeting.meeting_status == MEETING_STATUS_ENCODE,
                                                            CMeeting.meeting_type == 2).all()
        session.close()
        return moids

    @classmethod
    def delMeetingInfoById(self, meeting_id: int):
        session = Session()
        session.query(CMeeting).filter(CMeeting.id.in_([meeting_id])).delete(synchronize_session=False)
        session.commit()
        session.close()

    @classmethod
    def getMeetingInfo(self, strMoid: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strMoid).first()
        count = session.query(func.count(CText.text_id)).filter(CText.session_id == strMoid).scalar()
        session.close()
        return meeting, count

    @classmethod
    def getMeetingText(self, strMoid: str, nPage: int, nNum: int , bOP:bool):
        session = Session()
        if bOP:
            qc = session.query(func.count(CText.text_id)).filter(CText.session_id == strMoid).filter(or_(CText.text_sign == 0 , 
            CText.text_sign == 1 , CText.text_sign == 3))
            q = session.query(CText).filter(CText.session_id == strMoid).filter(or_(CText.text_sign == 0 , 
            CText.text_sign == 1 , CText.text_sign == 3))
        else:
            qc = session.query(func.count(CText.text_id)).filter(CText.session_id == strMoid).filter(or_(CText.text_sign == 0 , 
            CText.text_sign == 1 , CText.text_sign == 2))
            q = session.query(CText).filter(CText.session_id == strMoid).filter(or_(CText.text_sign == 0 , 
            CText.text_sign == 1 , CText.text_sign == 2))
        q = q.order_by(CText.text_bg_time)
        count = qc.scalar()
        if nPage <= 0 or nNum <= 0:
            list = q.all()
        else:
            list = q.limit(nNum).offset((nPage - 1) * nNum).all()
        session.close()
        return list, count

    @classmethod
    def getMeetingAllText(self, strMoid: str, nPage: int, nNum: int, sign: int):
        session = Session()
        qc = session.query(func.count(CText.text_id)).filter(CText.session_id == strMoid)
        if sign != -1:
            q = session.query(CText).filter(CText.session_id == strMoid).filter(or_(CText.text_sign == sign))
        else:
            q = session.query(CText).filter(CText.session_id == strMoid)
        q = q.order_by(CText.text_bg_time)
        count = qc.scalar()
        if nPage <= 0 or nNum <= 0:
            list = q.all()
        else:
            list = q.limit(nNum).offset((nPage - 1) * nNum).all()
        session.close()
        return list, count

    @classmethod
    def addOpenMeeting(self, strSessionId: str, strMeetingName: str, strMeetingAddr: str
                       , strMeetingParticipant: str, strBeginTime: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strSessionId).first()
        if meeting != None:
            session.close()
            return False

        meeting = CMeeting()
        meeting.session_id = strSessionId
        meeting.meeting_participant = strMeetingParticipant
        meeting.meeting_begin_time = strBeginTime
        meeting.meeting_alias = strMeetingName
        meeting.meeting_addr = strMeetingAddr
        meeting.meeting_type = 0
        meeting.meeting_status = MEETING_OPEN_STATUS_INIT
        session.add(meeting)
        session.commit()
        session.close()
        return True

    @classmethod
    def updateOpenMeetingEnd(self, strSessionId: str, strEndTime: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strSessionId).first()
        if meeting == None:
            session.close()
            return False

        meeting.meeting_status = MEETING_OPEN_STATUS_ENCODE
        meeting.meeting_end_time = strEndTime
        session.commit()
        session.close()
        return True

    @classmethod
    def updateOpenMeetingFinish(self, strSessionId: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strSessionId).first()
        if meeting == None:
            session.close()
            return False

        meeting.meeting_status = MEETING_OPEN_STATUS_FINISH
        session.commit()
        session.close()

    @classmethod
    def addOpenFileMeeting(self, strUuid: str, strRank: str, strUniqueId: str, strFileName: str, strBeginTime: str):
        session = Session()
        strUuid = str(strUuid)
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strUuid).first()
        if meeting != None:
            session.close()
            return False

        meeting = CMeeting()
        meeting.session_id = strUuid
        # meeting.meeting_e164 = strRank
        meeting.meeting_begin_time = strBeginTime
        meeting.meeting_alias = strFileName
        meeting.meeting_participant = strUniqueId
        meeting.meeting_type = 1
        meeting.meeting_status = MEETING_OPEN_STATUS_INIT
        session.add(meeting)
        session.commit()
        session.close()
        return True

    @classmethod
    def updateOpenFileMeetingStart(self, strUuid: str, strAliTaskId: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strUuid).first()
        if meeting == None:
            session.close()
            return False

        meeting.meeting_addr = strAliTaskId
        meeting.meeting_status = MEETING_OPEN_STATUS_ENCODE
        session.commit()
        session.close()
        return True

    #
    # arrText:{'session_id':strUuid,'text_bg_time':,'text_ed_time':,'text_content':,}
    #
    @classmethod
    def updateOpenFileMeetingEnd(self, strUuid: str, strEndTime: str, arrTexts: list):
        
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strUuid).first()
        if meeting == None:
            session.close()
            return False
        meeting.meeting_status = MEETING_OPEN_STATUS_FINISH
        meeting.meeting_end_time = strEndTime
        if arrTexts != None and len(arrTexts) > 0:
            session.execute(CText.__table__.insert(), arrTexts)
        session.commit()
        session.close()
        return True

    @classmethod
    def updateOpenFileMeetingException(self, strUuid: str, strEndTime: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strUuid).first()
        if meeting is None:
            session.close()
            return False
        meeting.meeting_status = MEETING_OPEN_STATUS_EXCEPTION
        meeting.meeting_end_time = strEndTime

        session.execute(CText.__table__.insert(), [])
        session.commit()
        session.close()
        return True

    @classmethod
    def getOpenFileMeetingInfo(self, strUuid: str):
        meeting, count = self.getMeetingInfo(strUuid)
        if meeting != None:
            return {'uuid': meeting.session_id, 'aliTaskId': meeting.meeting_addr,
                    'uniqueId': meeting.meeting_participant, "status": meeting.meeting_status,
                    'priority': '',  # meeting.meeting_e164,
                    'fileName': meeting.meeting_alias, 'begin_time': meeting.meeting_begin_time,
                    "end_time": meeting.meeting_end_time}
        return None

    @classmethod
    # by rank
    def getOpenFileMeetingInfoByPriority(self):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.meeting_type == 1,
                                                 CMeeting.meeting_status == MEETING_OPEN_STATUS_INIT).order_by(
            CMeeting.session_id.desc()).first()
        session.close()
        if meeting != None:
            return {'uuid': meeting.session_id, 'aliTaskId': meeting.meeting_addr,
                    'uniqueId': meeting.meeting_participant, "status": meeting.meeting_status,
                    'priority': '', # meeting.meeting_e164,
                    'fileName': meeting.meeting_alias, 'begin_time': meeting.meeting_begin_time,
                    "end_time": meeting.meeting_end_time}
        return None

    @classmethod
    def getOpenFileMeetingInfoByEncoding(self):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.meeting_type == 1,
                                                 CMeeting.meeting_status == MEETING_OPEN_STATUS_ENCODE).order_by(
            CMeeting.session_id.desc()).first()
        session.close()
        if meeting != None:
            return {'uuid': meeting.session_id, 'aliTaskId': meeting.meeting_addr,
                    'uniqueId': meeting.meeting_participant, "status": meeting.meeting_status,
                    'priority': '', # meeting.meeting_e164,
                    'fileName': meeting.meeting_alias, 'begin_time': meeting.meeting_begin_time,
                    "end_time": meeting.meeting_end_time}
        return None

    @classmethod
    def updateOpenFileMeetingByRevert(self, strUuid: str):
        session = Session()
        meeting = session.query(CMeeting).filter(CMeeting.session_id == strUuid).first()
        if meeting == None:
            session.close()
            return False
        meeting.meeting_status = MEETING_OPEN_STATUS_INIT
        session.commit()
        return True

    @classmethod
    def deleteOpenFileMeeting(self, strUuid: str):
        session = Session()
        results = session.query(CMeeting).filter(CMeeting.session_id == strUuid).all()
        for result in results:
            session.delete(result)
            session.commit()
        return True

    @classmethod
    def getMeetingConf(self, meeting_id: int):
        meeting = CStorageMinutes.getMeetingInfoById(meeting_id)
        content = self.getMeetingText(meeting.session_id, 0, 0, False)
        return meeting, content
