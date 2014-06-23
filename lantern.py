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
        
        """
        Every new command should be added in this dict in format TYPE:FUNC
        New commands should take exactly one argument, which is a byte string that should be struct.unpack'ed according to the meaning of input for that particular command
        Each function that implements new command should end with self.redraw()
        """
        self.commands = {
        0x12:self.on,
        0x13:self.off,
        0x20:self.change_color
        }
        self.socket = socket.socket()
        self.init_draw()
        
    """
    *draw commands are used for back-end drawing of lantern, they can be rewritten for fancier look
    init_draw should initialize graphics if such initialization is needed and draw initial state of lantern
    redraw is straightforward update of any changes in lantern's state
    end_draw should correctly shut down graphical system
    """
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
        

    "Commands that implement first version of lantern protocol"
    
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
        
    
    "Commands that implement networking"
        
    def tcp_client(self,fd,ev):
        """ 
        Callback function that should be provided as a handler for
        READ and ERROR events on self.socket in tornado.ioloop
        """
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

    def connect(self):
        """
        Connect to server. Should be called after registering all handlers.
        Does not invoke ioloop.start(). It should be invoked right after call to this function
        """
        try:
            self.socket.connect(self.ip_port)
        except:
            print "Couldn't reach server"
            self.closer(None,None)
        
    def closer(self,signum,frame):
        """
        Correctly closes everything that needs to be closed in lantern and stops tornado.ioloop.
        Should be provided as a handler for SIGINT or any other signal that will be used as a stop signal for lantern
        Also can be used as a "finally" statement for cleanup after emergency stop.
        """
        print "Shutting down"
        try:
            self.socket.close()
        except:
            pass
        try:
            self.end_draw()
        except:
            pass
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
    