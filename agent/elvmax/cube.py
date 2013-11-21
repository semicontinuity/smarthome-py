import socket
import threading
import time


class Search:
    ANY = '0.0.0.0'
    ALL = '255.255.255.255'
    MCAST_ADDR = '224.0.0.1'
    MCAST_PORT = 23272
    RECEIVE_TIMEOUT = 5

    @staticmethod
    def list_cubes():
        cube_search = Search()
        cube_search.send_hello()
        return cube_search.receive()


    def __init__(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #allow multiple sockets to use the same PORT number
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.ANY, self.MCAST_PORT))
        #tell the kernel that we are a multicast socket
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        #Tell the kernel that we want to add ourselves to a multicast group
        #The address for the multicast group is the third param
        value = socket.inet_aton(self.MCAST_ADDR) + socket.inet_aton(self.ANY)
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, value)


    def send_hello(self):
        data = 'eQ3Max*\x00**********I'
        self.send(data, self.MCAST_ADDR)
        self.send(data, self.ALL)


    def send(self, data, addr):
        for i in range(0, 5):
            self._socket.sendto(data, (addr, self.MCAST_PORT))
            time.sleep(0.1)


    def receive(self):
        self._socket.setblocking(0)
        result = []
        finish_time = time.time() + self.RECEIVE_TIMEOUT
        while 1:
            cube_info = self.receive_cube_info()
            if cube_info is not None:
                result = result + [cube_info]
            if time.time() > finish_time:
                break
        self._socket.close()
        return result


    def receive_cube_info(self):
        try:
            data, addr = self._socket.recvfrom(128)
            if data[0:8] == 'eQ3MaxAp':
                firmware = (data[24] << 8) | data[25]
                return data[8:18], addr, 62910 if firmware > 270 else 80, firmware
        except socket.error:
            pass
        return None


class Connection(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.s = None
        self.host = None
        self.port = None
        self.on_message = None

    def start(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(((socket.gethostbyname(self.host)), self.port))
        super(Connection, self).start()

    def stop(self):
        self.s.close()  # will terminate recv()

    def run(self):
        while True:
            message = bytearray()
            while True:
                char = self.s.recv(1)
                if char == '':
                    return
                message.extend(char)
                if char == '\n':
                    break

            self.on_message(message[:len(message) - 2])

    def write_message(self, message):
        self.s.sendall(message)