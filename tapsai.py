"""
实现多线程方式接收电子围栏的坐标信号和目标检测到的人体信号
对两组信号中电子围栏多边形和人体目标矩形框进行比对是否有重叠，根据比对后的信号进行分析
把分析后的结果输出到AI接口
等待接收数据提取信号，拷贝视频图片到指定本地位置和网络位置
上面所有涉及到的IP和端口通过cfg.yaml文件配置
新增了日志功能
Author:Liqishan
Company:WingoPower
Date:2022-02-09
"""
import socket
import json
# import _thread
import threading
import time as Time
from shapely.geometry import Polygon
import yaml
import os
import re
from time import *
import datetime


def now():
    t1 = datetime.datetime.now()

    return t1


def seconds(t1, t2):  # 秒
    sec = (t2 - t1).seconds
    delta = sec
    return delta


def millis(t1, t2):  # 毫秒
    micros = (t2 - t1).microseconds
    delta = micros / 1000
    return delta


def micros(t1, t2):  # 微秒
    delta = (t2 - t1).microseconds
    return delta


class tapsai:
    def __init__(self):
        self.debug = False
        self.lasttime = time()
        self.send_ai_data = {'protocol_id': 201, 'tunnel_id': 1, 'camera_id': 0, 'risk_level': 0, 'person_num': 0}
        self.sendtimes = 0
        self.sendtimes_rear = 0
        self.log_file = open('./log/tapsai.log', 'a', encoding='utf8')
        self.debug_file = open('./log/debug.log', 'a', encoding='utf8')
        self.threadLock = threading.Lock()
        self.front_fencing = []
        self.rear_fencing = []
        self.front_ip = ''
        self.rear_ip = ''
        self.risk_level = 0
        self.socket_ai = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 初始化发送到AI的数据
        self.ip_ai, self.port_ai = self.getAddress('ai-interface')
        self.checkport = 13010
        self.checkport1 = 13011

    def write_log(self, log_str):
        """ 记录日志
            参数：
                log_str：日志
        """
        t = datetime.datetime.now()
        ts = t.strftime('%Y-%m-%d %H:%M:%S')
        format_log_str = "%s ---> %s \n " % (ts, log_str)
        self.log_file.write(format_log_str)

    def debug_log(self, log_str):
        """ 调试日志
        """
        if self.debug:
            t = datetime.datetime.now()
            ts = t.strftime('%Y-%m-%d %H:%M:%S:%f')
            format_log_str = "%s ---> %s \n " % (ts, log_str)
            self.debug_file.write(format_log_str)

    def deal_error(self, e):
        """ 处理错误异常
            参数：
                e：异常
        """
        log_str = '发生错误: %s' % e
        self.write_log(log_str)
        sys.exit()

    def run_time(self):
        return time() - self.lasttime

    def isIP(self, str):
        """
        判断字符串是否是IP
        :param str:传入的待判断字符串
        :return: 返回是否是IP
        """
        p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
        if p.match(str):
            return True
        else:
            return False

    def Rect2Poly(self, box2points):
        """
        把两点矩形转化为polygon
        :param box2points: 左上角和右下角2点矩形
        :return: polygon
        """

        assert len(box2points) == 4, 'Input value(box2points) has len ' + str(len(box2points))
        x01, y01, x02, y02 = box2points
        return [[x01, y01], [x01, y02], [x02, y02], [x02, y01]]

    def Overlap_Area(self, data1, data2):
        """
        任意两个图形的相交面积的计算
        :param data1: 当前物体
        :param data2: 待比较的物体
        :return: 当前物体与待比较的物体的面积交集
        """
        poly1 = Polygon(data1).convex_hull  # Polygon：多边形对象
        poly2 = Polygon(data2).convex_hull

        if not poly1.intersects(poly2):
            inter_area = 0  # 如果两四边形不相交
        else:
            inter_area = 1
            # inter_area = poly1.intersection(poly2).area  # 相交面积
        return inter_area

    def getAddress(self, source):
        """
        从yaml中读取配置数据
        :param source: 根标签
        :return: ip地址和端口
        """
        fileNamePath = os.getcwd()
        yamlPath = os.path.join(fileNamePath, 'cfg.yaml')
        with open(yamlPath, 'r', encoding='utf-8') as f:
            cont = f.read()
            title = yaml.safe_load(cont)
            return title[source]['ip'], title[source]['port']

    def extract_ip_port(self, source: str) -> list:
        """
        :param source: 'rtsp://admin:wingo123456@192.168.2.51:554/h264/ch1/main/av_stream'
        :return: ['192.168.2.51':'554']
        """
        return re.findall(r'[0-9]+(?:\.[0-9]+){3}:[0-9]+', source)[0].split(':')

    def Caculation(self, strJson):
        """
        接收人体检测和围栏数据
        计算围栏是否与人体图像是否重叠
        向AI接口发送风险等级
        :param strJson:传入的人体检测和围栏信息
        :return:无返回
        risk_level取值范围：0表示无人，1表示有人且处于安全区域，2表示有人且处于危险区域
        """

        jsonDic = json.loads(strJson)

        protocol_id = jsonDic["protocol_id"]
        detected = jsonDic["detected"]

        if protocol_id == 101 and self.front_fencing:  # 目标检测
            risk_level = 0
            num = jsonDic["objects"]["person"]["num"]
            persons_rect = jsonDic["objects"]["person"]["coords"]
            url = jsonDic["url"]

            ip_camera = self.extract_ip_port(url)[0]
            if detected == 1:
                for rect in persons_rect:
                    area = self.Overlap_Area(self.front_fencing, self.Rect2Poly(rect))
                    if area == 0:
                        risk_level = 1
                    elif area > 0:
                        risk_level = 2
                        self.sendtimes += 1
                        break
                if risk_level != 2:
                    self.sendtimes = 0
            else:
                risk_level = 0

            self.send_ai_data['risk_level'] = risk_level
            self.send_ai_data['person_num'] = num
            if self.isIP(ip_camera):
                self.send_ai_data['camera_id'] = int(ip_camera.split('.')[3])
            else:
                self.send_ai_data['camera_id'] = '0'

            self.socket_ai.sendto(json.dumps(self.send_ai_data).encode(), (self.ip_ai, self.port_ai))
            self.socket_ai.sendto(json.dumps(self.send_ai_data).encode(), (self.ip_ai, self.checkport))

            print('Detect:%d,Risk:%d' % (num, risk_level))


    def Caculation_rear(self, strJson):
        """
        接收人体检测和围栏数据
        计算围栏是否与人体图像是否重叠
        向AI接口发送风险等级
        :param strJson:传入的人体检测和围栏信息
        :return:无返回
        risk_level取值范围：0表示无人，1表示有人且处于安全区域，2表示有人且处于危险区域
        """
        jsonDic = json.loads(strJson)
        protocol_id = jsonDic["protocol_id"]
        detected = jsonDic["detected"]

        if protocol_id == 101 and self.rear_fencing:  # 目标检测
            risk_level = 0
            num = jsonDic["objects"]["person"]["num"]
            persons_rect = jsonDic["objects"]["person"]["coords"]
            url = jsonDic["url"]

            ip_camera = self.extract_ip_port(url)[0]


            if detected == 1:
                for rect in persons_rect:
                    assert len(rect) == 4, 'rect len not 4 error,is ' + str(len(rect)) + '.Msg is:' + str(jsonDic)
                    area = self.Overlap_Area(self.rear_fencing, self.Rect2Poly(rect))
                    if area == 0:
                        risk_level = 1
                    elif area > 0:
                        risk_level = 2
                        self.sendtimes_rear += 1
                        break
                if risk_level != 2:
                    self.sendtimes_rear = 0
            else:
                risk_level = 0

            self.send_ai_data['risk_level'] = risk_level
            self.send_ai_data['person_num'] = num
            if self.isIP(ip_camera):
                self.send_ai_data['camera_id'] = int(ip_camera.split('.')[3])
            else:
                self.send_ai_data['camera_id'] = '0'
            self.socket_ai.sendto(json.dumps(self.send_ai_data).encode(), (self.ip_ai, self.port_ai))
            self.socket_ai.sendto(json.dumps(self.send_ai_data).encode(), (self.ip_ai, 13010))
            self.socket_ai.sendto(json.dumps(self.send_ai_data).encode(), (self.ip_ai, 13011))


    def screen_requestfrommcu(self, threadname, delay):

        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        i = 1
        while True:
            data = {'protocol_id': 203, 'camera_id': 51, 'screenshot': i}
            skt.sendto(json.dumps(data).encode(), ('127.0.0.1', 25540))
            Time.sleep(delay)
            if i == 0:
                i += 1
            else:
                i -= 1

    def screen_waiting_success(self, threadname, delay):
        BUFSIZE = 1024
        skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        skt.bind((self.ip_ai, self.port_ai))
        while True:
            Time.sleep(delay)
            data = skt.recv(BUFSIZE).decode()
            print("Success:" + data)

    def receive_detection(self, threadname, delay):
        """
        接收电子围栏、目标检测和截图的信号线程
        :param threadname: 线程名称。与yaml标签同名
        :param delay:delay time
        :return: none
        """
        BUFSIZE = 1024
        ip, port = self.getAddress(threadname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((ip, port))
        while True:
            Time.sleep(delay)
            rawdata = s.recv(BUFSIZE)
            data = rawdata.decode()
            jsonDic = json.loads(data)
            # print(data)
            protocol_id = jsonDic["protocol_id"]
            if protocol_id == 101:  # 目标检测
                ip_camera = self.extract_ip_port(jsonDic["url"])[0]
                if ip_camera == self.front_ip:
                    self.lasttime = time()
                    self.Caculation(data)
                    debuginfo = "Caulation spending:" + str(self.run_time())
                    self.debug_log(str(debuginfo))
                elif ip_camera == self.rear_ip:
                    self.Caculation_rear(data)

            elif protocol_id == 203:  # 截图请求
                if jsonDic["screenshot"] == 1:
                    camera_id = jsonDic["camera_id"]
                    if camera_id == 51:
                        s.sendto(rawdata, ('127.0.0.1', 25599))  # 给detect程序发送截图命令
                    else:
                        s.sendto(rawdata, ('127.0.0.1', 25588))
                    Time.sleep(2)
                    jsonDic["screenshot"] = 0
                    s.sendto(json.dumps(jsonDic).encode(), ('127.0.0.1', 25599))  # 2秒后停止
                    s.sendto(json.dumps(jsonDic).encode(), ('127.0.0.1', 25588))

    def receive_fencing(self, threadname, delay):
        """
        接收电子围栏和目标检测的信号线程
        :param threadname: 线程名称。与yaml标签同名
        :param delay:delay time
        :return: none
        """
        BUFSIZE = 1024
        ip, port = self.getAddress(threadname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((ip, port))
        while True:
            Time.sleep(delay)
            data = s.recv(BUFSIZE)
            strJson = data.decode()
            # print(strJson)
            jsonDic = json.loads(strJson)

            protocol_id = jsonDic["protocol_id"]
            detected = jsonDic["detected"]
            if protocol_id == 102 and detected == 1:  # 电子围栏
                self.front_fencing = jsonDic["front"]["area"]
                self.rear_fencing = jsonDic["rear"]["area"]
                self.front_ip = jsonDic["front"]["ip"]
                self.rear_ip = jsonDic["rear"]["ip"]

    def ai_hearbeat(self, threadname, delay):
        hearbeat_data = {'protocol_id': 202, 'camera_id': 51, 'status': 1, 'modules':
            {'object_detection': 1, 'virtual_fencing': 1, 'calculation': 1}}
        while True:
            self.socket_ai.sendto(json.dumps(hearbeat_data).encode(), (self.ip_ai, self.port_ai))
            Time.sleep(delay)

    def debuging(self, threadname, delay):
        BUFSIZE = 1024
        ip, port = '0.0.0.0', 25900
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((ip, port))
        while True:
            Time.sleep(delay)
            data = s.recv(BUFSIZE)
            strJson = data.decode()
            if strJson == '1':
                ti = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                self.debug_file = open('./log/debug'+ ti + '.log', 'a', encoding='utf8')
                self.debug = True
            else:
                self.debug = False

def main():
    obj = tapsai()
    threads = []
    try:
        t1 = threading.Thread(target=obj.receive_detection, args=("wingo-detectcion", 0.001))
        threads.append(t1)
        t2 = threading.Thread(target=obj.receive_fencing, args=("virture-fencing", 2))
        threads.append(t2)
        t3 = threading.Thread(target=obj.ai_hearbeat, args=("ai_hearbeat", 0.5))
        threads.append(t3)
        t4 = threading.Thread(target=obj.debuging, args=("debuging", 0.5))
        threads.append(t4)
        for t in threads:
            t.setDaemon(True)
            t.start()
        print("aicacu run success!")
    except:
        print("Error: Can't start threads!")

    while 1:
        pass

if __name__ == '__main__':
    print("tapsai running...")
    main()
