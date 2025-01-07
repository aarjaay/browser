import socket
import ssl
import os
from pathlib import Path
import tkinter
import tkinter.font

WIDTH, HEIGHT = 800, 600
H_STEP, V_STEP = 13, 18
SCROLL_STEP = 100

class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, tag):
        self.tag = tag

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
        self.display_list = Layout(text).display_list
        self.draw()
    
    def draw(self):
        self.canvas.delete("all")

        for x, y, c, f in self.display_list:
            y = y - self.scroll
            if y + V_STEP < 0: continue
            if y > HEIGHT: continue
            self.canvas.create_text(x, y, text=c, font=f)

class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = H_STEP
        self.cursor_y = V_STEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12

        for tok in tokens:
            self.tokens(tok)

    def token(self, token):
        if isinstance(token, Text):    
            for word in token.text.split():
                font = tkinter.font.Font(
                    size=self.size,
                    weight=self.weight,
                    style=self.style
                )
                w = font.measure(word)
                self.display_list.append((self.cursor_x, self.cursor_y, word, font))
                self.cursor_x += w + font.measure(" ")
                if self.cursor_x + w >= WIDTH - H_STEP:
                    self.cursor_x = H_STEP
                    self.cursor_y += font.metrics("linespace") * 1.25
        elif token.tag == "i":
            self.style = "italic"
        elif token.tag == "/i":
            self.style = "roman"
        elif token.tag == "b":
            self.weight = "bold"
        elif token.tag =="/b":
            self.weight = "normal"
        elif token.tag =="small":
            self.size -= 2
        elif token.tag =="/small":
            self.size += 2
        elif token.tag =="big":
            self.size += 4
        elif token.tag =="/big":
            self.size -= 4
        

def layout(tokens):
    display_list = []
    cursor_x, cursor_y = H_STEP, V_STEP
    weight = "normal"
    style = "roman"
    for token in tokens:
        if isinstance(token, Text):    
            for word in token.text.split():
                font = tkinter.font.Font(
                    size=16,
                    weight=weight,
                    style=style
                )
                w = font.measure(word)
                display_list.append((cursor_x, cursor_y, word, font))
                cursor_x += w + font.measure(" ")
                if cursor_x + w >= WIDTH - H_STEP:
                    cursor_x = H_STEP
                    cursor_y += font.metrics("linespace") * 1.25
        elif token.tag == "i":
            style = "italic"
        elif token.tag == "/i":
            style = "roman"
        elif token.tag == "b":
            weight = "bold"
        elif token.tag =="/b":
            weight = "normal"
        
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
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c
    if not in_tag and buffer:
        out.append(Text(buffer))
    return out

def load(url):
    body = url.request()
    show(body)
    
# if __name__ == "__main__":
#     import sys
#     # load(URL(sys.argv[1]))
#     Browser().load(URL(sys.argv[1]))
#     tkinter.mainloop()

Browser().load(URL("https://browser.engineering/text.html#what-is-a-font"))
tkinter.mainloop()
# load(URL("https://browser.engineering/text.html#what-is-a-font"))
# load(URL(("file:///Users/rj/Desktop/samples.txt")))