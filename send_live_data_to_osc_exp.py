#!/usr/bin/env python
# NOTE: broken

import argparse
import json
import select
import socket
import threading
import queue

from pythonosc import udp_client


class TCPClient(object):
    def __init__(self, port, osc_ip, osc_port):
        # NOTE: can't configure the ip meaningfully in this case.
        self.tcp_ip = '127.0.0.1'
        self.tcp_port = port
        self.buffer_size = 99999
        self.osc_ip = osc_ip
        self.osc_port = osc_port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.input_check = []
        self.output_check = []
        self.is_checking = False
        self.message_queue = queue.Queue()

    def connect(self):
        self.socket.connect((self.tcp_ip, self.tcp_port))
        self.output_check.append(self.socket)
        self.is_checking = True

    def start(self):
        thread = threading.Thread(target=self.message_checker)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.is_checking = False
        self.socket.close()

    def message_checker(self):
        # osc_client = udp_client.SimpleUDPClient(args.ip, args.port)
        while self.is_checking:
            readable, writable, exceptional = select.select(self.input_check, self.output_check, self.input_check)
            for s in readable:
                message = s.recv(self.buffer_size)
                msg = message.decode("utf-8")
                try:
                    msg_json = json.loads(msg)
                    print(msg_json[0])
                except:
                    pass
                # osc_client.send_message("/sensor", msg_json[0])
                self.input_check = []

            for s in writable:
                try:
                    next_msg = self.message_queue.get_nowait()
                except queue.Empty:
                    pass
                else:
                    # print("send ")
                    self.socket.send(str(next_msg).encode())

            for s in exceptional:
                print("exceptional ", s)

    def add_message_to_send(self, data):
        self.message_queue.put(data)
        if self.socket not in self.output_check:
            self.output_check.append(self.socket)
        if self.socket not in self.input_check:
            self.input_check.append(self.socket)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--osc-ip", default="127.0.0.1",
        help="The ip of the OSC server")
    parser.add_argument("--osc-port", type=int, default=8080,
        help="The port the OSC server is listening on")
    parser.add_argument("--opensignal-port", type=int, default=5555,
        help="The port the opensignal server is sending to")
    args = parser.parse_args()

    tcp_client = TCPClient(args.opensignal_port, args.osc_ip, args.osc_port)
    tcp_client.connect()
    tcp_client.start()
    tcp_client.add_message_to_send('start')
    while True:
        tcp_client.add_message_to_send('')
    print('END')


#tcp_ip_client_sample.py | 2019-08-01