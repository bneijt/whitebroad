import tornado.ioloop
import tornado.web
import tornado.websocket
import json
from PIL import Image
import io
import zlib

import logging
logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def asJson(obj):
    return json.dumps(obj) #TODO separators=...

class Whiteboard:
    def __init__(self, path):
        self.path = path
        self.image = Image.new("RGB", (256, 144), color = (255,255,255));
        self._updateHash()

    def adler32(self):
        return self.hash

    def _updateHash(self):
        pixels = bytes()
        for pixel in self.image.getdata():
            pixels += bytes(pixel)
        self.hash = str(zlib.adler32(pixels))
        logger.info("New hash for %s is %s", self.path, self.hash)

    def pixel(self, position):
        assert isinstance(position, tuple)
        assert len(position) == 2
        return self.image.getpixel(position)

    def assertValidChannelRange(self, value):
        assert value >= 0
        assert value <= 255

    def size(self):
        return self.image.size

    def setPixel(self, position, value):
        assert isinstance(position, tuple)
        assert len(position) == 2
        assert isinstance(value, tuple)
        assert len(value) == 3
        self.assertValidChannelRange(value[0])
        self.assertValidChannelRange(value[1])
        self.assertValidChannelRange(value[2])
        self.image.putpixel(position, value)
        self._updateHash()

    def asPNG(self):
        with io.BytesIO() as output:
            self.image.save(output, 'png')
            contents = output.getvalue()
            return contents

sessions = {}

class Session:
    def __init__(self, path, client):
        self.whiteboard = Whiteboard(path)
        self.path = path
        self.clients = [client]

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, path):
        path = path.decode('utf-8')
        self.session = sessions.get(path, Session(path, self))
        if not path in sessions:
            sessions[path] = self.session
        else:
            self.session.clients.append(self)
        self.whiteboard = self.session.whiteboard

    def on_message(self, messageJson):
        try:
            message = json.loads(messageJson)
            if 'adler32' in message:
                self.write_message(asJson(self.whiteboard.adler32()))
            if 'size' in message:
                assert message['size'] == '?'
                size = self.whiteboard.size()
                self.write_message(asJson({"size": {"w": size[0], "h": size[1]}, "hash": self.whiteboard.adler32()}))
            if 'get' in message:
                pos = (int(message['get']['x']), int(message['get']['y']))
                self.broadcastPixelTo(pos, [self])
            if 'set' in message:
                msg = message['set']
                pos = (int(msg['x']), int(msg['y']))
                v = (int(msg['r']), int(msg['g']), int(msg['b']))
                self.whiteboard.setPixel(pos, v)
                self.broadcastPixelTo(pos, self.session.clients)

        except Exception as e:
            logging.exception("Communication failure")
            self.close()

    def tryClose(self):
        try:
            self.close()
        except Exception as e:
            logging.exception("Unable to close connection")

    def broadcastPixelTo(self, pos, clients):
        v = self.whiteboard.pixel(pos)
        msg = asJson({'set':
            {
                'x': pos[0],
                'y': pos[1],
                'r': v[0],
                'g': v[1],
                'b': v[2]
            }, 'hash': self.whiteboard.adler32()})
        for idx, client in enumerate(clients):
            try:
                client.write_message(msg)
            except Exception as e:
                logging.exception("Failed to write to client")
                client.tryClose()

    def on_close(self):
        #Clean up session
        if hasattr(self, 'session'):
            for idx, client in enumerate(self.session.clients):
                if client == self:
                    del self.session.clients[idx]
            if len(self.session.clients) == 0:
                del sessions[self.session.path]
            logger.info("Open sessions are: %s", list(sessions.keys()))

class DownloadWhiteboardHandler(tornado.web.RequestHandler):
    def get(self, path):
        if not path in sessions:
            raise tornado.web.HTTPError(404)

        wb = sessions[path].whiteboard
        self.set_header("Content-Type", 'image/png')
        self.write(wb.asPNG())

app = tornado.web.Application([
    (r"/", tornado.web.RedirectHandler, {"url": "index.html"}),
    (r"/wb/(.*)", WebSocketHandler),
    (r"/png/(.*).png", DownloadWhiteboardHandler),
    (r"/(.*)", tornado.web.StaticFileHandler, {'path': "static"}),
])

if __name__ == '__main__':
    app.listen(8000)
    tornado.ioloop.IOLoop.instance().start()


