#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time  : 2018/12/14 10:32 AM
# @Author: jasmine sun
# @File  : vueServer.py

import json
import random

import gevent
import pymysql
from flask import Flask, request
from flask_cors import CORS
from flask_sockets import Sockets

app = Flask(__name__)
# Flask解决跨域
CORS(app, supports_credentials=True)


sockets = Sockets(app)
messages_list = []
avatar_list = ['01.jpg', '02.jpg', '03.jpg', '04.jpg', '05.jpg', '06.jpg']


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


@sockets.route('/submit')
def inbox(ws):
    """Receives incoming chat messages, inserts them into Redis."""
    print('submit')
    while not ws.closed:
        # Sleep to prevent *constant* context-switches.
        gevent.sleep(0.1)
        message = ws.receive()

        if message:
            # json.loads() 函数是将json格式数据转换为字典
            message = json.loads(message)

            # 接收到的消息
            # print(message)
            app.logger.info(u'Inserting message: {}'.format(message))
            html = {
                # 'id': message['id'],
                'avatar': message['avatar'],
                'name': message['name'],
                'text': message['text'],
                'cur_time': message['cur_time']
            }

            # print(html)
            save_msg(html)

            # json.dumps() 函数是将一个Python数据类型列表进行json格式的编码
            messages_list.append(json.dumps(html))
            # print(messages_list)
            # print(type(messages_list[0]))

            chats.start(ws)


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
            # 'name': name
        }
    else:
        message = {
            'avatar': 'default.jpg'
        }

    ws.send(json.dumps(message))
    while not ws.closed:
        # Context switch while `ChatBackend.start` is running in the background.
        gevent.sleep(0.1)


# def get_message_time():
#     # 获取消息的时间
#     # 返回格式 yyyy-MM-dd hh:mm:ss
#     return datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')

@app.route('/auth_params', methods=['POST'])
def get_authparams():
    if request.method == 'post':
        code = request.values.get('code')
        print(code)
        print("send success !")
        return ""
    return ""


# 将数据保存到数据库
def save_msg(html):
    conn = pymysql.connect(host='localhost', port=3306, user='xxx', password='xxx', db='chat_log',
                           charset='utf8', use_unicode=True)
    cursor = conn.cursor()

    try:
        print(html)
        # print(type(html['avatar']))
        sql = "insert into chatroom_record (user_avatar, user_name, chat_text, cur_time) values ('{}','{}','{}','{}')".format(
            html['avatar'],
            html['name'],
            html['text'],
            html['cur_time']
        )
        cursor.execute(sql)
        conn.commit()
    except pymysql.Error as e:
        print("database error, Causes: %d: %s" % (e.args[0], e.args[1]))
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
