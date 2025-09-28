from email.policy import default
from sqlalchemy import Column, Integer, String
from model.db import Base


MEETING_STATUS_APPLY = -1
MEETING_STATUS_MINUTES = 0
MEETING_STATUS_ENCODE = 1
MEETING_STATUS_FINISH = 2
MEETING_STATUS_ERROR = 3


MEETING_OPEN_STATUS_INIT = 0
MEETING_OPEN_STATUS_ENCODE = 1
MEETING_OPEN_STATUS_FINISH = 2
MEETING_OPEN_STATUS_EXCEPTION = 3

class CMeeting(Base):
    __tablename__ = 'oddasr_meeting'

    id = Column(Integer, primary_key=True)     
    session_id = Column(String(1024) ,unique=True)        # open->session_id uuid
    # meeting_e164 = Column(String(32))                       # priority
    meeting_type = Column(Integer)                          # 0 open-live 1 open-file 2 meeting
    meeting_alias = Column(String(1024))                    # filename
    meeting_addr = Column(String(1024))                     # alitaskId
    meeting_begin_time = Column(String(32))
    meeting_end_time = Column(String(32))
    meeting_participant = Column(String(1024))              # split by ',' , length > 1024?  uniqueid
    meeting_audio_res_id = Column(String(1024),default='')  
    meeting_status = Column(Integer)                        # -1 apply 0 ing 1 encode 2 finish 3 error
    meeting_op_status = Column(Integer , default=0)         # 0 , 1 for meeting.

    def __repr__(self):
        return ("<CMeeting(id:%d)>") % (self.id)


    