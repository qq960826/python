import random
import time
import requests
import threading
import re

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
from requests.adapters import HTTPAdapter

#This script is written By WZQ

requests.adapters.DEFAULT_RETRIES = 100

url = "http://192.168.100.117"

user_info = [{"user": "201601060222", "password": "111111"}]


class EnglishStudy:
    def __init__(self):
        session = requests.session()
        session.mount(url, HTTPAdapter(max_retries=100))
        session.keep_alive = False
        self.target_course = 1
        self.target_unit = 0
        self.courselist = []
        self.unitlist = []
        self.session = session

    def login(self, user, password):
        text = self.session.get(url + "/npels/").text
        soup = BeautifulSoup(text, 'html.parser')
        viewstate = soup.find_all('input', attrs={"id": "__VIEWSTATE"})[0].attrs["value"]

        self.user = user
        self.password = password

        form = {"tbName": self.user, "tbPwd": self.password, "__VIEWSTATE": viewstate, "btnLogin": "登 录"}
        text = self.session.post(url + "/npels/login.aspx", data=form).text
        # print(text)

    def loadclasslist(self):
        self.courselist = []
        text = self.session.get(url + "/NPELS/student/index.aspx").text
        soup = BeautifulSoup(text, 'html.parser')
        div = soup.find_all('div', attrs={"class": "class_mag_3"})[0]

        ul = div.find_all('ul')
        for i in range(len(ul)):
            location = ul[i].find("a").attrs["onclick"]
            location = location.replace("location.href=\'", "")
            location = location.replace("\'", "")
            param = parse_qs(location.replace("CourseIndex.aspx?", ""))
            # urlparse()
            # parse_qsl(urlparse(url).query)
            name = ul[i].find("li", attrs={"class": "class_mag_1_4"}).contents[0]
            temp = {"location": location, "name": name, "c": param["c"][0], "m": param["m"][0]}
            self.courselist.append(temp)
        #print(self.courselist)

    def loadunitlist(self):
        self.unitlist = []
        for i in range(len(self.courselist)):
            text = self.session.get(url + "/NPELS/student/" + self.courselist[i]["location"]).text
            soup = BeautifulSoup(text, 'html.parser')
            ul = soup.find_all('ul', attrs={"class": "class_3_2"})
            units = []
            course_param = self.courselist[i]["location"].replace("CourseIndex.aspx?", "")
            for j in range(len(ul)):
                temp = {}
                time = ul[j].find("div").contents[0]
                if (time == "开始下载"):
                    continue
                unit_name = ul[j].find("li", attrs={"class": "class_3_2_1"}).contents[0]
                unit_address = ul[j].find("a").attrs["href"]
                if ("ShowUnit" not in unit_address):
                    continue
                unit_address = unit_address.replace("javascript:ShowUnit(\'", "")
                unit_address = unit_address.replace("\');", "")
                unit_time = ul[j].find("div", attrs={"class": "tagText"}).contents[0]
                re_time = re.compile(r'([0-9]*?):([0-9][0-9])/([0-9]*?):([0-9][0-9])')
                unit_time_raw = re_time.findall(unit_time)
                temp["time_finished"] = int(unit_time_raw[0][0]) * 60 + int(unit_time_raw[0][1])
                temp["time_all"] = int(unit_time_raw[0][2]) * 60 + int(unit_time_raw[0][3])
                if (temp["time_finished"] > temp["time_all"]):
                    continue
                temp["name"] = unit_name
                temp["address"] = unit_address
                temp["time"] = time
                units.append(temp)
            self.unitlist.append(units)
        while True:
            flag = 0
            for i in range(len(self.unitlist)):
                if (len(self.unitlist[i])) == 0:
                    del self.unitlist[i]
                    del self.courselist[i]
                    flag = 1
                    break
            if flag == 0:
                break

    def heartbeat(self):
        if (len(self.unitlist[self.target_course]) == 0):
            return
        headers = {"X-Requested-With": "XMLHttpRequest", "Referer": url + "/NPELS/studentdefault.aspx"}
        updatestattime = self.session.get(
            url + "/NPELS/Student/LogTime.aspx?logType=updatestattime&nocache=" + str(random.random()),
            headers=headers).text
        gettoken = self.session.get(
            url + "/NPELS/Student/LogTime.aspx?logType=gettoken&nocache=" + str(random.random()), headers=headers).text
        pass

    def choosecourse(self, index):
        self.target_course = index

    def chooseunit(self, index):
        self.target_unit = index

    def start(self):
        headers = {"X-Requested-With": "XMLHttpRequest", "Referer": url + "/NPELS/studentdefault.aspx"}
        course_param = self.courselist[self.target_course]["location"].replace("CourseIndex.aspx?", "")
        url_course = url + "/NPELS/Student/CourseStudy.aspx?t=studyunit&" + course_param + "&u=" + \
                     self.unitlist[self.target_course][self.target_unit]["address"]
        text_course = self.session.get(url_course, headers=headers).text
        url_getcomment = url + "/NPELS/student/LogTime.aspx?logType=getcomment&classno=" + \
                         self.courselist[self.target_course]["c"] + "&material=" + self.courselist[self.target_course][
                             "m"] + "&unit=" + self.unitlist[self.target_course][self.target_unit][
                             "address"] + "&nocache=" + str(random.random())
        text_getcomment = self.session.get(url_getcomment, headers=headers).text
        url_checkneedauthorize = url + "/NPELS/student/LogTime.aspx?logType=checkneedauthorize&material=" + \
                                 self.courselist[self.target_course]["m"] + "&nocache=" + str(random.random())
        text_checkneedauthorize = self.session.get(url_checkneedauthorize, headers=headers).text
        url_getservertime = url + "/NPELS/Student/LogTime.aspx?logType=getservertime&nocache=" + str(random.random())
        text_getservertime = self.session.get(url_getservertime, headers=headers).text
        url_startnew = url + "/NPELS/Student/LogTime.aspx?logType=startnewstattime&stattype=1&material=" + \
                       self.courselist[self.target_course]["m"] + "&unit=" + \
                       self.unitlist[self.target_course][self.target_unit]["address"] + "&nocache=" + str(
            random.random()) + "&class=" + self.courselist[self.target_course]["c"] + "&nocache=" + str(random.random())
        text_startnew = self.session.get(url_startnew, headers=headers).text
        pass

    def switch(self):
        user_Session[i].loadunitlist()
        reminder = divmod(self.target_unit + 1, len(self.unitlist[self.target_course]))[0]
        # reminder=0

        self.target_course = (self.target_course + reminder) % len(self.courselist)
        self.target_unit = divmod((self.target_unit + 1), len(self.unitlist[self.target_course]))[1]

        if (len(self.unitlist[self.target_course]) == 0):
            return
        self.start()
        pass


user_Session = []
for i in range(len(user_info)):
    a = EnglishStudy()
    a.login(user_info[i]["user"], user_info[i]["password"])
    a.loadclasslist()
    a.loadunitlist()
    a.choosecourse(0)
    a.start()
    user_Session.append(a)


def autoswitch():
    while True:
        time.sleep(600)
        for i in range(len(user_info)):
            user_Session[i].switch()


thread_switch = threading.Thread(target=autoswitch)
thread_switch.start()

# autoswitch()
j = 0
while True:
    for i in range(len(user_info)):
        user_Session[i].heartbeat()
    time.sleep(10)
    # a.switch()
    j += 1
    print(j * 10)
