import os
import json
import subprocess
import datetime
import platform
import asyncio
import random
import websockets as ws
import odd_asr_config as config

def getAuth():
    if platform.system() != "Windows":
        str = os.popen('/opt/catherine/oddasr/script/auth_info.sh').read()
    else:
        str = '127.0.0.1,2039-6-26,已授权,12,2039-6-26,已授权,已授权,0'
    l = str.split(',')
    return {'ip':l[0],'date':l[1],'desc':l[2],
    'audio_num':l[3],'audio_date':l[4],'audio_status':l[5],
    'audio_desc':l[6],'audio_offline_num':l[7]};

#导入设备授权
def import_jdl_auth():
    if platform.system() != "Windows":
        file_path = config.auth_cert_path
        auth_path = "/opt/catherine/oddasr/license/"
        auth_file = file_path + "license.lic"
        res=os.system("mv %s %s"%(auth_file,auth_path))
    else:
        res = 1
        print("do nothing")
    
    if res == 0:
        return {'code': 0, 'description': '导入成功'}
    
    else:
        return {'code': -1, 'description': '导入失败'}

#导出设备凭证
def export_jdl_auth_cert():
    if platform.system() != "Windows":
        res=os.system("/opt/catherine/oddasr/script/autoAuth.sh get_cert")
        filename = os.popen("ls /opt/catherine/oddasr/auth-relate | grep AuthRequestFile").read()
    else:
        res=0
        filename = ""
    if res !=0 or filename == '':
        print('get jdl auth failed')
        return {"code":-1, "filename":filename, "description":"导出失败"}
    return {"code":0, "filename":filename, "description":"导出成功"}


#for msg_id
def random_str(n):  
    keylist = [random.choice("0123456789") for i in range(n)]
    return ("".join(keylist))

#读取信息
def read_file_to_json(path):
    f=open(path,'rb')
    file_json=json.load(f)
    auth_code=file_json['authCode']
    driver='aliyun'
    msg_id = random_str(8) + "-" + random_str(4) + "-" + random_str(4) + random_str(4) + "-" + random_str(12)
    msg_type='MSG_KISTOJDL_PUT_ASR_LICENSE_REQ'
    addr=config.jdl_address
    msg={'data':auth_code,'driver_name':driver,'msg_id':msg_id,'msg_type':msg_type,'ws_addr':addr}
    data=json.dumps(msg)
    f.close()
    return data

#导入asr授权
def import_asr_auth(path):
    if platform.system() != "Windows":
        data=read_file_to_json(path)
        url=config.jdl_address
        loop=asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data_res=asyncio.get_event_loop().run_until_complete(send_data_to_jdl(url,data))
        
        data_res_json=json.loads(data_res)

        status_code=data_res_json["status_code"]
    else:
        status_code="10001"

    if status_code=="10000":
        return {'code': 0, 'description': '导入成功'}
    else:
        return {'code': -1, 'description': '导入失败'}


#导出asr凭证： excute by local
def export_asr_auth_cert2():
    if platform.system() != "Windows":
        res=os.system("/opt/catherine/oddasr/script/autoAuth.sh get_asr_cert")
        filename = os.popen("ls /opt/catherine/oddasr/auth-relate | grep AuthRequestFile_").read()
    else:
        res=0
        filename = ""
    if res !=0 or filename == '':
        print('get jdl auth failed')
        return {"code":-1, "filename":filename, "description":"导出失败"}
    return {"code":0, "filename":filename, "description":"导出成功"}

#导出asr凭证： excute thru JDL server


def export_asr_auth_cert():
    if platform.system() != "Windows":
        msg_id = random_str(8) + "-" + random_str(4) + "-" + random_str(4) + random_str(4) + "-" + random_str(12)
        url = config.jdl_address
        msg = {"driver_name" : "aliyun","msg_id" : msg_id,"msg_type" : "MSG_GET_ASR_LICENSE_MACHINE_CODE_REQ","ws_addr" : url}
        data = json.dumps(msg)

        loop=asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data_res=asyncio.get_event_loop().run_until_complete(send_data_to_jdl(url,data))

        data_res_json=json.loads(data_res)

        time=data_res_json["datetime"]
        dongle_id=data_res_json["dongle_id"]
        machineCode=data_res_json["data"]
        mac=data_res_json["min_mac"]
        licenceNum=0

        #todo soft auth get reset_code
        resetCode = ""
        status_code = data_res_json["status_code"]

        #str型的时间转换成格式化的datetime.datetime型
        curtime = datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S') 

        file_name = mac+"-ALIRF-"+curtime+".txt"
        file_path = config.auth_cert_path
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        filename=file_path+file_name
        content={"datetime":time,"dongle_id":dongle_id,"machineCode":machineCode,"mac":mac,"licenceNum":licenceNum,"resetCode":resetCode}
        f=open(filename,"w")
        json.dump(content,f)
        f.close()
    else:
        file_name=""
        status_code="10001"

    if status_code=="10000":
        return {"code": 0, "description": "导出成功","filename":file_name}
    else:
        return {"code": -1, "description": "导出失败","filename":file_name}


async def send_data_to_jdl(url,data):
    async with ws.connect(url) as websocket:
        await websocket.send(data)
        data_res=await websocket.recv()
    return data_res
    