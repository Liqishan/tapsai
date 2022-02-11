import socket
import json
import yaml
import os
import time
import datetime


def t():
    t1 = datetime.datetime.now()
    ts1 = t1.strftime('%Y-%m-%d %H:%M:%S')
    return t1, ts1


def millis(t1, t2):  # 毫秒
    micros = (t2 - t1).microseconds
    # print("micros: ",micros)
    delta = micros / 1000
    return delta


def micros(t1, t2):  # 微秒
    delta = (t2 - t1).microseconds
    return delta


# Press the green button in the gutter to run the script.
lasttime, _ = t()


def doMsg(strJson):
    global lasttime, _
    jsonDic = json.loads(strJson)
    # print(strJson)
    if jsonDic["protocol_id"] == 201:
        print("Date:%s,CameraID:%s,Risk:%s,Person num:%s,TTS(ms):%i" %
              (_,
               jsonDic['camera_id'],
               jsonDic['risk_level'],
               jsonDic['person_num'],
               millis(lasttime, datetime.datetime.now())
               ))
        lasttime, _ = t()

        # print(strJson)
    # print(jsonDic["front"]["area"][0])


def getAddress(source):
    fileNamePath = os.getcwd()
    yamlPath = os.path.join(fileNamePath, 'cfg.yaml')
    with open(yamlPath, 'r', encoding='utf-8') as f:
        cont = f.read()
        title = yaml.safe_load(cont)
        return title[source]['ip'], title[source]['port']


def main():
    while 1:
        # time.sleep(1)
        data, fromAddress = receiver.recvfrom(1024)  # 一次接收1024字节
        doMsg(data.decode())
        # print(data.decode()+" IP:"+fromAddress[0]+":"+str(fromAddress[1]))


if __name__ == '__main__':
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.bind(("0.0.0.0", 13010))
    print("Wainting...")
    main()
