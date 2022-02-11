import socket
import json
import yaml
import os
import time


# Press the green button in the gutter to run the script.
def doMsg(strJson):
    # jsonDic = json.loads(strJson)
    print(strJson)
    # print(jsonDic["protocol_id"])
    # print(jsonDic["front"]["area"][0])


def getAddress(source):
    fileNamePath = os.getcwd()
    yamlPath = os.path.join(fileNamePath, 'cfg.yaml')
    with open(yamlPath, 'r', encoding='utf-8') as f:
        cont = f.read()
        title = yaml.safe_load(cont)
        return title[source]['ip'], title[source]['port']


def main():
    data = {'protocol_id': 203, 'camera_id': 51, 'screenshot': 1}
    while 1:
        time.sleep(0.2)
        print(data)
        sender.sendto(json.dumps(data).encode(), ('127.0.0.1', 25540))  # 2秒后停止
        # sender.sendto(("Send Data:"+data.decode()).encode(), ('192.168.0.165', 13001))


if __name__ == '__main__':
    ip_ai, port_ai = getAddress('ai-interface')
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    main()
