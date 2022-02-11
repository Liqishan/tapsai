import socket
import json
import os
import re
import _thread
import threading
from time import *
import yaml
from shapely.geometry import Polygon
import numpy as np
import cv2
import datetime


def t():
    t1 = datetime.datetime.now()
    ts1 = t1.strftime('%Y-%m-%d %H:%M:%S')
    return t1, ts1


def seconds(t1, t2):  # 秒
    sec = (t2 - t1).seconds
    # print("micros: ",micros)
    delta = sec
    return delta


def millis(t1, t2):  # 毫秒
    micros = (t2 - t1).microseconds
    # print("micros: ",micros)
    delta = micros / 1000
    return delta


def micros(t1, t2):  # 微秒
    delta = (t2 - t1).microseconds
    return delta


def Rect2Poly(box2points):
    """
    把两点矩形转化为polygon
    :param box2points: 左上角和右下角2点矩形
    :return: polygon
    """
    x01, y01, x02, y02 = box2points
    return [[x01, y01], [x01, y02], [x02, y02], [x02, y01]]


def Overlap_Area(data1, data2):
    """
    任意两个图形的相交面积的计算
    :param data1: 当前物体
    :param data2: 待比较的物体
    :return: 当前物体与待比较的物体的面积交集
    """
    poly1 = Polygon(data1).convex_hull  # Polygon：多边形对象
    poly2 = Polygon(data2).convex_hull
    # print(poly1)
    if not poly1.intersects(poly2):
        inter_area = 0  # 如果两四边形不相交
    else:
        inter_area = poly1.intersection(poly2).area  # 相交面积
    return inter_area


def Overlap_Area1(data1, data2, h, w):
    '''
    get the iou of 2 poly
    '''
    data1 = np.array(data1, np.int32)  ##the area of poly1 > poly2
    data2 = np.array(data2, np.int32)

    mask1 = np.zeros((h, w), np.uint8)
    mask2 = np.zeros((h, w), np.uint8)
    # cv2.imwrite("mask.jpg", mask)

    cv2.fillPoly(mask1, [data1], 1)
    data1_count = (mask1 == 1).sum()

    cv2.fillPoly(mask2, [data2], 1)
    mask = mask1 + mask2
    inter = (mask == 2).sum()

    if inter > 0:
        return inter
    else:
        return 0


def runtime(t1, t2):
    return t2 - t1


fencing = [[0.44, 0.16], [0.48, 0.15], [0.76, 1.0], [0.42, 1.0]]

rec = [[0.189323, 0.307870, 0.168229, 0.500926],
       [0.245573, 0.663426, 0.168229, 0.449074],
       [0.496094, 0.455093, 0.258854, 0.584259],
       [0.930469, 0.287963, 0.053646, 0.220370],
       [0.968490, 0.530093, 0.041146, 0.115741],
       [0.786458, 0.068519, 0.061458, 0.118519],
       [0.067187, 0.818981, 0.070833, 0.226852],
       [0.878646, 0.895833, 0.070833, 0.139815],
       [0.763802, 0.453704, 0.148438, 0.403704],
       [0.522135, 0.345370, 0.292187, 0.618519],
       [0.376823, 0.581019, 0.124479, 0.678704]]

if __name__ == '__main__':
    j = 0
    rt = 100
    begin_time = time()
    while j < rt:
        i = 0
        while i < len(rec):
            print(Overlap_Area(fencing, Rect2Poly(rec[i])))
            # print(Overlap_Area1(fencing, Rect2Poly(rec[i]), 600, 800))
            i += 1
        j +=1
    end_time = time()
    run_time = runtime(begin_time, end_time) / rt
    # micros(end_time,begin_time)
    print('Every %i times spend Run Time is %f:' % (len(rec), run_time) )
    # print('该循环程序运行时间：', millis(end_time, begin_time))
