import socket
import json
import yaml
import os
import time
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', default=1, type=int, help='wrint debug log')
    parser.add_argument('--ip', default='127.0.0.1', type=str, help='目标IP')
    opt = parser.parse_args()
    print(opt)
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    i = 0
    while i < 1:
        time.sleep(0.2)
        sender.sendto(json.dumps(opt.debug).encode(), (opt.ip, 25900))
        i += 1

