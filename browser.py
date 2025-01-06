import socket
import ssl
import os
from pathlib import Path
import tkinter


class URL:
    def __init__(self, url) -> None:
        self.scheme, url = url.split("://", 1)
        
        assert self.scheme in ["http", "https", "file"]
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
        elif self.scheme == "file":
            self.path = url
            return
        
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        if self.scheme == "file":
            return self.handleFile()

        s = socket.socket(family=socket.AF_INET,
                          type =socket.SOCK_STREAM,
                          proto = socket.IPPROTO_TCP)
        s.connect((self.host, self.port))
        
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request_headers = {}
        request_headers["Host"] = self.host
        request_headers["Connection"] = "close"
        request_headers["User-Agent"] = "aarjaay"

        for rh, v in request_headers.items():
            request += "{}: {}\r\n".format(rh, v)
        request += "\r\n"
        s.send(request.encode("utf8"))
        
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line =="\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read()
        s.close()

        return content
        
    def handleFile(self):
        if os.path.isfile(self.path): 
            content = Path(self.path).read_text()
            return content
        else:
            content = "No File at the given path"
            return content

WIDTH, HEIGHT = 800, 600
H_STEP, V_STEP = 13, 18
SCROLL_STEP = 100

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()
    
    def draw(self):
        self.canvas.delete("all")

        for x, y, c in self.display_list:
            y = y - self.scroll
            if y + V_STEP < 0: continue
            if y > HEIGHT: continue
            self.canvas.create_text(x, y, text=c)

def layout(text):
    display_list = []
    cursor_x, cursor_y = H_STEP, V_STEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += H_STEP
        if cursor_x >= WIDTH - H_STEP:
            cursor_x = H_STEP
            cursor_y = cursor_y + V_STEP
    return display_list

def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag= True
        elif c ==">":
            in_tag=False
        elif not in_tag:
            print (c, end="")

def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag= True
        elif c ==">":
            in_tag=False
        elif not in_tag:
            text += c
    return text


def load(url):
    body = url.request()
    show(body)
    
if __name__ == "__main__":
    import sys
    # load(URL(sys.argv[1]))
    Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

# load(URL("http://google.com"))
load(URL(("file:///Users/rj/Desktop/samples.txt")))