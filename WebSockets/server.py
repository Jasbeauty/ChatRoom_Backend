#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2018/10/25 10:56 AM
# @Author: jasmine sun
# @File  : test2.py
import datetime
import json
import random

import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

app = Flask(__name__)
# app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)
messages_list = []
avatar_list = ['01.jpg', '02.jpg', '03.jpg', '04.jpg', '05.jpg']


class ChatBackend(object):
    """Interface for registering and updating WebSocket clients."""

    def __init__(self):
        self.clients = list()

    def __iter_data(self):
        if len(messages_list) > 0:
            for message in messages_list:
                messages_list.remove(message)
                yield message

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
        Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            self.clients.remove(client)

    def run(self, ws):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            for client in self.clients:
                if ws != client:
                    # print(ws)
                    # print(client)
                    gevent.spawn(self.send, client, data)

    def start(self, ws):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run(ws))


chats = ChatBackend()


@app.route('/')
def chat_view():
    return render_template('chat_view.html')


@sockets.route('/submit')
def inbox(ws):
    """Receives incoming chat messages, inserts them into Redis."""
    print('submit')
    # print(ws)
    # check_ws = {
    #     'id': ws
    # }
    while not ws.closed:
        # Sleep to prevent *constant* context-switches.
        gevent.sleep(0.1)
        message = ws.receive()

        if message:
            # json.loads() 函数是将json格式数据转换为字典
            message = json.loads(message)
            message['datetime'] = get_message_time()
            # check_ws['avatar'] = message['avatar']
            print(message)
            app.logger.info(u'Inserting message: {}'.format(message))
            html = {
                'id': message['id'],
                'content': '''<img class='message-avatar-left' src="{}" > <div class='message-left'> <a 
                    class='message-author' href='#'>{}</a> <span class='message-date-right'>{} 
                    </span> <pre class='message-content'>{}</pre> </div>'''
                    .format(
                    'static/img/' + message['avatar'], message['handle'], message['datetime'], message['text'])
            }
            message_barrage = {
                'message': html,
                'barrage': message['item']
            }
            # print(html)
            # json.dumps() 函数是将一个Python数据类型列表进行json格式的编码
            messages = json.dumps(message_barrage)
            print(messages)
            messages_list.append(messages)

            chats.start(ws)

        # with gevent.Timeout(1.0, True):
        #     print('closed')
        #     if check_ws['id'] == ws:
        #         avatar_list.append(check_ws['avatar'])


@sockets.route('/receive')
def outbox(ws):
    print('receive')
    """Sends outgoing chat messages, via `ChatBackend`."""
    chats.register(ws)
    # print(ws)

    # 解决error: IndexError: pop from empty list
    if avatar_list:  # if empty_list will evaluate as false
        message = {
            # 将list转为str类型
            'avatar': ''.join(random.sample(avatar_list, 1)),
            # 'avatar': avatar_list.pop()
            # 'item'
        }
    else:
        message = {
            'avatar': 'default.jpg'
        }

    ws.send(json.dumps(message))
    while not ws.closed:
        # Context switch while `ChatBackend.start` is running in the background.
        gevent.sleep(0.1)


def get_message_time():
    # 获取消息的时间
    # 返回格式 yyyy-MM-dd hh:mm:ss
    return datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
