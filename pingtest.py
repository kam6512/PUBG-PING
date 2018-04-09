import subprocess
import re

import uuid
import requests
import time

from rx import Observable

import tkinter as tk
root = tk.Tk()


class AWS:
    def check(self):
        link = "http://dynamodb.ap-northeast-2.amazonaws.com/ping?x="

        return Observable.interval(2000)\
            .map(lambda i: uuid.uuid4().hex)\
            .map(lambda hash: link+hash)\
            .map(lambda req_link: requests.get(req_link))\
            .on_error_resume_next(lambda e: Observable.just(e))\
            .map(lambda res: res.elapsed.total_seconds())\
            .map(lambda elapsed: int(round(elapsed, 3)*1000))


class IP_Manager:

    def runShell(self, cmd, observer):
        observer.on_next(subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE))
        observer.on_completed()

    def getPID(self):
        PID = []
        Observable.create(lambda observer: self.runShell('tasklist /svc /FI "IMAGENAME eq TslGame.exe" /FO "CSV"', observer)) \
            .flat_map(lambda pid_call: Observable.from_(pid_call.stdout.readlines())) \
            .skip(1) \
            .map(lambda line: re.sub(r"[^\d]", "", str(line))).subscribe(lambda line: PID.append(line))
        return PID

    def getNetStat(self):
        NetStats = []
        Observable.create(lambda observer: self.runShell('netstat -ntof', observer)) \
            .flat_map(lambda NetCall: Observable.from_(NetCall.stdout.readlines())) \
            .skip(5) \
            .map(lambda line: str(line)) \
            .map(lambda line: re.sub(r"[\'\"\,]", "", line)) \
            .map(lambda line: re.split('    ', line)) \
            .map(lambda line: list(filter(None, line))) \
            .map(lambda line: [re.sub(r":[\d]+", "", line[2]).strip(), re.sub(r"\\tInHost",  "", line[4]).strip()])\
            .distinct().subscribe(lambda line: NetStats.append(line))
        return NetStats

    def filterNetStatsByPID(self):
        PID = self.getPID()
        NetStats = self.getNetStat()

        ipset = []
        Observable.from_(PID)\
            .map(lambda pid: list(filter(lambda x: x[1] == pid, NetStats)))\
            .distinct()\
            .subscribe(lambda line: ipset.extend(line))

        ips = []
        Observable.from_(ipset)\
            .map(lambda ip: ip[0])\
            .filter(lambda ip: len(ip) != 0)\
            .filter(lambda ip: ip != '127.0.0.1')\
            .filter(lambda ip: ip != '[:]')\
            .subscribe(lambda ip: ips.append(ip))

        return ips

    def getIps(self):
        ips = self.filterNetStatsByPID()
        buffer = len(ips)
        if buffer < 1:
            buffer = 1
        return Observable.from_(ips)\
            .map(lambda ip: [ip, self.ping(ip)])\
            .buffer_with_count(buffer)

    def ping(self, ip):
        res = subprocess.getoutput('ping -w 1000 -n 1 '+ip+' | find "TTL="')
        if res.strip() is not '':
            res = re.findall(r'[\d]+ms', res)[0]
        else:
            res = '--'
        return res

    def run(self):
        return Observable.interval(2000)\
            .filter(lambda filter: len(self.getPID()) == 1)\
            .flat_map(lambda i: self.getIps())


class WindowDraggable():

    def __init__(self, label):
        self.label = label
        label.bind('<ButtonPress-1>', self.StartMove)
        label.bind('<ButtonRelease-1>', self.StopMove)
        label.bind('<B1-Motion>', self.OnMotion)

    def StartMove(self, event):
        self.x = event.x
        self.y = event.y

    def StopMove(self, event):
        self.x = None
        self.y = None

    def OnMotion(self, event):
        x = (event.x_root - self.x -
             self.label.winfo_rootx() + self.label.winfo_rootx())
        y = (event.y_root - self.y -
             self.label.winfo_rooty() + self.label.winfo_rooty())
        root.geometry("+%s+%s" % (x, y))


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.ping = tk.Label(self)
        self.ping["text"] = "WAIT FOR PUBG..."
        self.ping["bg"] = "black"
        self.ping["fg"] = "yellow"
        self.ping.pack(side="top")

    def setPingText(self, res):
        if len(res) != 0:
            text = ''
            for index, line in enumerate(res):
                text += str(line)
                if index != len(res)-1:
                    text += '\n'
            self.ping["text"] = text
        else:
            self.ping["text"] = "WAIT FOR PUBG...R"

    def setPingTextAWS(self, res):
        self.ping["text"] = str(res)+'ms'


def runUI():
    root.call('wm', 'attributes', '.', '-topmost', '1')
    root.configure(background='black')
    root.overrideredirect(True)
    root.bind('<ButtonRelease-3>', exit)
    root.wm_attributes('-alpha', 0.7)
    WindowDraggable(root)
    app = Application(master=root)

    global runner
    # runner = IP_Manager().run().subscribe(on_next=lambda next: app.setPingText(next))
    runner = AWS().check().subscribe(on_next=lambda next: app.setPingTextAWS(next))

    app.mainloop()


def exit(event):
    runner.dispose()
    root.destroy()


runUI()
# AWS().check().subscribe(on_next=lambda next: print(next))
# input('press any key to exit\n')
