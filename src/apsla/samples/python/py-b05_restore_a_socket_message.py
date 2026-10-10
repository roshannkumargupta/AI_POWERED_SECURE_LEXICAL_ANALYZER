import pickle
import socket
sock = socket.socket()
data = sock.recv(4096)
record = pickle.loads(data)
