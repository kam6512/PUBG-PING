
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
        self.ping["text"] = "WAIT FOR AWS KR SERVER...."
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
    runner = AWS().check().subscribe(on_next=lambda next: app.setPingTextAWS(next))

    app.mainloop()


def exit(event):
    runner.dispose()
    root.destroy()


runUI()
# AWS().check().subscribe(on_next=lambda next: print(next))
# input('press any key to exit\n')
