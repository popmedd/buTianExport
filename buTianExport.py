#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
# @Author  : Cr4y0n
# @Software: PyCharm
# @Time    : 2021/4/10
# @Github  : https://github.com/Cr4y0nXX

import os
import csv
import json
import time
import requests
from threading import Lock
from bs4 import BeautifulSoup
from argparse import ArgumentParser
from getChromeCookie import getCookiesFromChrome
from concurrent.futures import ThreadPoolExecutor

class BuTianExport:
    def __init__(self):
        self.banner()
        self.args = self.parseArgs()
        self.parseCookie()
        self.parseID()
        self.init()
        self.multiRun()
        self.start = time.time()

    def banner(self):
        logo = r"""
  _        _______ _             ______                       _   
 | |      |__   __(_)           |  ____|                     | |  
 | |__  _   _| |   _  __ _ _ __ | |__  __  ___ __   ___  _ __| |_ 
 | '_ \| | | | |  | |/ _` | '_ \|  __| \ \/ / '_ \ / _ \| '__| __|
 | |_) | |_| | |  | | (_| | | | | |____ >  <| |_) | (_) | |  | |_ 
 |_.__/ \__,_|_|  |_|\__,_|_| |_|______/_/\_\ .__/ \___/|_|   \__|
                                            | |                   
                                            |_|            Author: Cr4y0n
        """
        msg = """Get butian SRC vendor msg.\n
You need to login butian, and then you can use -c to specify Cookie or have the program automatically fetch Cookie from your Chrome.\n
If there's a big error in the result, please refresh the page or specify a new Cookie.\n\n"""
        print("\033[91m" + logo + "\033[0m")
        print(msg)

    def init(self):
        print("-" * 20)
        print("thread:", self.args.Thread)
        print("timeout:", self.args.timeout)
        print("delay:", self.args.delay)
        print("targetCount:", len(self.idList))
        print("cookie:", self.cookie)
        print("-" * 20 + "\n")

    def parseArgs(self):
        parser = ArgumentParser()
        parser.add_argument("-sid", "--startID", required=False, type=int, default=-1, help=f"Number of thread, default is auto extract from site")
        parser.add_argument("-eid", "--endID", required=False, type=int, default=-1, help=f"Number of thread, default is auto extract from site")
        parser.add_argument("-T", "--Thread", required=False, type=int, default=32, help=f"Number of thread, default is 32")
        parser.add_argument("-t", "--timeout", required=False, type=int, default=3,  help="Request timeout, default is 3 sec")
        parser.add_argument("-s", "--delay", required=False, type=int, default=0,  help="Delay between requests, default is 0 sec")
        parser.add_argument("-c", "--cookie", required=False, type=str, default=getCookiesFromChrome("butian.net"),  help="Cookie of the domain butian.net, default is auto extract from your chrome")
        return parser.parse_args()

    # 获取页面参数ID
    def getID(self):
        print("Collecting page ID, please waiting……")
        idList = []
        for pID in range(1, 11):
            data = {"s": 1, "p": {int(pID)}, "token": ""}
            reqURL = f"https://www.butian.net/Reward/pub"
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
                "Cookie": self.cookie,
                "Host": "www.butian.net",
                "Origin": "https://www.butian.net",
                "Referer": "https://www.butian.net/Reward/pub",
            }
            try:
                rep = requests.post(url=reqURL, headers=header, data=data, timeout=self.args.timeout)
                repJson = json.loads(rep.text)
                # 获取请求ID
                for i in range(len(repJson["data"]["list"])):
                    idList.append(repJson["data"]["list"][i]["company_id"])
            except:
                continue
        return idList

    # 获取name和domain
    def getNameAndDomain(self, id):
        try:
            reqURL = f"https://www.butian.net/Loo/submit?cid={id}"
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
                "Cookie": self.cookie,
                "Host": "www.butian.net",
                "Origin": "https://www.butian.net",
                "Referer": "https://www.butian.net/Reward/pub",
            }
            rep = requests.get(url=reqURL, headers=header, timeout=self.args.timeout)
            if rep.status_code == 200:
                soup = BeautifulSoup(rep.text, "html.parser")
                inputTag = soup.find_all("input", attrs={"class": "input-xlarge"})
                name = inputTag[0]["value"]
                domain = inputTag[1]["value"]
                if name and domain:
                    self.lock.acquire()
                    try:
                        self.resultList.append([name.strip(), domain.strip()])
                        print(f"\033[32m[+] {name.strip():<30}{domain.strip()}\033[0m")
                    finally:
                        self.lock.release()
            time.sleep(self.args.delay)
        except:
            time.sleep(self.args.delay)
            return

    # 解析ID
    def parseID(self):
        if self.args.startID == -1 or self.args.endID == -1:
            self.idList = self.getID()
        else:
            self.idList = [str(i) for i in range(int(self.args.startID), int(self.args.endID) + 1)]

    # 解析cookie
    def parseCookie(self):
        self.cookie = ""
        cookieList = self.args.cookie.split(";")
        for i in cookieList:
            i += "; "
            for j in ["PHPSESSID", "btuc_", "notice", "wzws_cid", "__q__"]:
                if j in i:
                    self.cookie += i

    # 多线程运行
    def multiRun(self):
        # self.parseID()
        self.resultList = []
        self.lock = Lock()
        executor = ThreadPoolExecutor(max_workers=self.args.Thread)
        executor.map(self.getNameAndDomain, self.idList)

    # 输出到文件
    def output(self):
        date = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        self.file = f"./output/export_{date}.csv"
        if not os.path.isdir(r"./output"):
            os.mkdir(r"./output")
        with open(self.file, "a", encoding="gbk", newline="") as f:
            csvWrite = csv.writer(f)
            csvWrite.writerow(["厂商","域名"])
            for result in self.resultList:
                csvWrite.writerow(result)

    def __del__(self):
        try:
            print("\n","-" * 20, "\nexportCount：\033[32m%d\033[0m" % (len(self.resultList)))
            self.end = time.time()
            print("Time Spent: %.2f" % (self.end - self.start))
            self.output()
            print(f"The result has been saved in {self.file}\n")
        except:
            pass

if __name__ == "__main__":
    BuTianExport()


