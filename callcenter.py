"""
This example connects to the specified AMI hosts and prints a message when an
account is ringing and when a call is transferred.
"""
import _thread
from datetime import datetime
from cacofonisk import AmiRunner, BaseReporter
from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

app = Flask(__name__)
sockets = Sockets(app)
allWs = []

class TransferSpammer(BaseReporter):
    """
    通话响铃
    """
    def on_b_dial(self, call_id, caller, to_number, targets):
        # callee_codes = [target.code for target in targets]
        caller_number = caller.number
        print("主叫 {}, 被叫 {} 开始振铃 {}".format( caller_number, to_number, datetime.now().isoformat(timespec='minutes')))
    """
    通话接听
    """
    def on_up(self, call_id, caller, to_number, callee):
        # callee_account_code = callee.code
        caller_number = caller.number
        print("主叫 {}, 被叫 {} 开始通话 {}".format(caller_number, to_number, datetime.now().isoformat(timespec='minutes')))
    """
    忙转接
    """
    def on_warm_transfer(self, call_id, merged_id, redirector, caller, destination):
        print('{} 转接到 {} (was calling {}) {}'.format(caller, destination, redirector, datetime.now().isoformat(timespec='minutes')))

    """
    协商转接
    """
    def on_cold_transfer(self, call_id, merged_id, redirector, caller, to_number, targets):
        print('{} 尝试转接从 {} 到号码 {} (ringing {}) {}'.format(
            redirector, caller, to_number, ', '.join(targets), datetime.now().isoformat(timespec='minutes')
        ))
    """
    通话挂断
    """
    def on_hangup(self, call_id, caller, to_number, reason):
        print("主叫 {}， 被叫 {} (挂断原因: {}) {}".format(caller.number, to_number, self.i18n(reason), datetime.now().isoformat(timespec='minutes')))
        self.sendMessage("主叫 {}, 被叫 {} (挂断原因: {})".format(caller.number, to_number, self.i18n(reason)))

    """
    国际化通话挂断原因
    """
    def i18n(self, message):
        return {
            'completed':'通话完成',
            'cancelled':'通话取消',
        }[message]

    """
    发送消息到 websocket
    """
    def sendMessage(self, message):
        for ws in allWs:
            if ws.closed:
                del ws
            else:
                ws.send(message)

@sockets.route('/echo')
def echo_socket(ws):
    allWs.append(ws)
    while not ws.closed:
        message = ws.receive()
        ws.send(message)

@app.route('/')
def hello():
    return 'Hello flask!'


if __name__ == '__main__':
    ami_host = {'host': '192.168.11.65', 'username': 'admin', 'password': 'admin', 'port': 5038}
    ami_hosts = (ami_host,)

    reporter = TransferSpammer()
    runner = AmiRunner(ami_hosts, reporter)
    _thread.start_new_thread(runner.run, ())

    server = pywsgi.WSGIServer(('', 9995), app, handler_class=WebSocketHandler)
    server.serve_forever()