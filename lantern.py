#!/usr/bin/python
# -*- coding: utf-8 -*-

import tornado.ioloop
import functools
import socket
import struct
import sys
import signal

class lantern:
    def __init__(self, state=0,color=0xFFFFFF,ip = '127.0.0.1',port=9999):
        self.state = state
        self.color = color
        self.ip_port = (ip,port)

        self.commands = {
        0x12:self.on,
        0x13:self.off,
        0x20:self.change_color
        }
        self.socket = socket.socket()
        self.init_draw()
        
    def connect(self):
        try:
            self.socket.connect(self.ip_port)
        except:
            print "Couldn't reach server"
            self.closer(None,None)

        
    def init_draw(self):
        if self.state:
            print "Lantern turned on and is shining with color %06X" % self.color
        else:
            print "Lantern turned off"
        
    def redraw(self):
        if self.state:
            print "Lantern turned on and is shining with color %06X" % self.color
        else:
            print "Lantern turned off"
            
    def end_draw(self):
        pass
        
        
    def on(self,val):
        self.state = 1
        self.redraw()
        
    def off(self,val):
        self.state = 0
        self.redraw()
        
    def change_color(self,color):
        (R,G,B) = struct.unpack('>3B',color)
        self.color = 0x010000*R + 0x000100*G+ B
        self.redraw()
        
        
    def tcp_client(self,fd,ev):
        io_loop = tornado.ioloop.IOLoop.current()
        if ev & tornado.ioloop.IOLoop.ERROR:
            self.socket.close()
            io_loop.stop()
        elif ev & tornado.ioloop.IOLoop.READ:
            try:
                buffer = self.socket.recv(3)
            except:
                self.closer(None,None)
            else:
                if len(buffer) > 0:
                    (type,length) = struct.unpack('>BH',buffer)
                    
                    if length>0:
                        value = self.socket.recv(length)
                    else:
                        value = None
                        
                    if type in self.commands:
                        self.commands[type](value)
                    else:
                        print "Unknown command"
                else:
                    self.closer(None,None)
        else:
            print "Unknown signal"
        
    def closer(self,signum,frame):
        print "Shutting down"
        self.socket.close()
        self.end_draw()
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.stop()
        sys.exit(0)
    
if __name__ == '__main__':

    print "Enter server's ip and port (default 127.0.0.1:9999):",
    ip_port = sys.stdin.readline()
    if ip_port.rstrip():
        try:
            i,p = ip_port.split(":")
            l = lantern(ip=i,port = int(p))
        except:
            print "Incorrect address format"
            sys.exit(1)
    else:
        l = lantern()

    io_loop = tornado.ioloop.IOLoop.instance()
    signal.signal(signal.SIGINT,l.closer)
    io_loop.add_handler(l.socket.fileno(), l.tcp_client, tornado.ioloop.IOLoop.READ | tornado.ioloop.IOLoop.ERROR)
    l.connect()
    io_loop.start()
    