import os
import sys
import cv2
import threading
import numpy as np
import socketserver
import pygame
import socket
import time

current_frame = None
X = np.empty((0, 120, 320))
y = np.empty((0, 1))

class VideoStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        global current_frame
        stream = b' '

        try:
            while True:
                stream += self.rfile.read(1024)
                first = stream.find(b'\xff\xd8')
                last = stream.find(b'\xff\xd9')

                if first != -1 and last != -1:
                    jpg = stream[first:last+2]
                    stream = stream[last+2:]

                    gray = cv2.imdecode(np.frombuffer(jpg, dtype = np.uint8), cv2.IMREAD_GRAYSCALE)
                    current_frame = np.expand_dims(gray, axis=0)

                    cv2.imshow('image', gray)
                    print(gray.shape)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

        finally:
            cv2.destroyAllWindows()
            sys.exit()

class ControlStreamHandler(socketserver.BaseRequestHandler):
    def handle(self):
        global X
        global y

        self.controls = {
            'f': "forward",
            'b': "backward",
            'r': "right",
            'l': "left",
            'q': "quit"
        }

        self.last_command = None
        self.command_sent = False

        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    key_input = pygame.key.get_pressed()

                    if key_input[pygame.K_UP]:
                        print("sending control")
                        self.request.sendall(self.controls['f'].encode('utf-8'))
                        self.last_command = self.controls['f']
                        self.command_sent = True
                        X = np.vstack((X, current_frame))
                        y = np.vstack((y, 1))
                        print("sent control {}".format(self.controls['f']))

                    if key_input[pygame.K_DOWN]:
                        print("sending control")
                        self.request.sendall(self.controls['b'].encode('utf-8'))
                        self.last_command = self.controls['b']
                        self.command_sent = True
                        X = np.vstack((X, current_frame))
                        y = np.vstack((y, 2))
                        print("sent control {}".format(self.controls['b']))

                    if key_input[pygame.K_LEFT]:
                        print("sending control")
                        self.request.sendall(self.controls['l'].encode('utf-8'))
                        self.last_command = self.controls['l']
                        self.command_sent = True
                        X = np.vstack((X, current_frame))
                        y = np.vstack((y, 3))
                        print("sent control {}".format(self.controls['l']))

                    if key_input[pygame.K_RIGHT]:
                        print("sending control")
                        self.request.sendall(self.controls['r'].encode('utf-8'))
                        self.last_command = self.controls['r']
                        self.command_sent = True
                        X = np.vstack((X, current_frame))
                        y = np.vstack((y, 4))
                        print("sent control {}".format(self.controls['r']))

                    if key_input[pygame.K_q]:
                        self.request.sendall(self.controls['q'].encode('utf-8'))
                        if not os.path.exists('training_data'):
                            os.makedirs('training_data')

                        try:
                            np.savez('training_data' + '/' + str(int(time.time())) + '.npz', train=X, train_labels=y)
                        except IOError as e:
                            print(e)

                        pygame.display.quit()
                        break
                
                elif event.type == pygame.KEYUP:
                    if self.command_sent:
                        self.command_sent = False
                        self.request.sendall(self.last_command[::-1].encode('utf-8'))


class Server(object):
    def __init__(self, host, port1, port2):
        self.host = host
        self.port1 = port1
        self.port2 = port2

        pygame.display.init()
        pygame.display.set_mode((250, 250))

    def video_stream(self, host, port):
        s = socketserver.TCPServer((host, port), VideoStreamHandler)
        print("starting stream server")
        s.serve_forever()
    
    def control_stream(self, host, port):
        s = socketserver.TCPServer((host, port), ControlStreamHandler)
        print("starting control server")
        s.serve_forever()

    def start(self):
        stream_thread = threading.Thread(target=self.video_stream, args=(self.host, self.port1))
        stream_thread.daemon = True
        stream_thread.start()
        self.control_stream(self.host, self.port2)

if __name__ == "__main__":
    host, port1, port2 = '0.0.0.0', 6678, 6679
    ts = Server(host, port1, port2)

    ts.start()