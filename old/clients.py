import json
import socket
import logging

class BaseClient(object):

    def __init__(self, server_address):
        self.addr = server_address[0]
        self.port = server_address[1]
        self.connected = False
        self.sock = None

    def create_conn(self):
        tries = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while not self.connected and tries < 3:
            logging.info('BaseClient.create_conn(): ' + str(self.addr) + ':' + str(self.port))
            try:
                self.sock.connect( (self.addr, self.port) )
            except socket.error as sock_err:
                if sock_err.errno != 60 or sock_err.errno != 22:
                    raise sock_err
            else:
                self.connected = True
            finally:
                tries += 1

    def create_header(self, data_len):
        header = "_{0:010d}_".format(data_len)
        logging.debug('BaseClient.create_header(): ' + header)
        return header

    def receive(self, data_len):
        recvd = self.sock.recv(data_len)
        while len(recvd) < data_len:
            recvd += self.sock.recv(data_len - len(recvd))
        logging.debug('BaseClient.receive(' + str(data_len) + 'bytes):' + str(recvd)) 
        return recvd

    def receive_header(self):
        header = self.receive(12)
        header = self.verify_header(header)
        logging.debug('BaseClient.receive_header(): ' + str(header))
        return header

    def verify_header(self, header):
        if header[0] != '_' or header[11] != '_':
            return 0
        else:
            return header.strip('_')

    def transmit(self, data):
        logging.info('BaseClient.transmit()')
        if not self.connected:
            print "Diconnected from server"
            logging.warn('BaseClient.transmit() disconnected from server')
            return
        bytes_total = len(data)
        bytes_sent = self.sock.send(data)
        while bytes_sent < bytes_total:
            bytes_sent += self.sock.send(data[bytes_sent:])
        logging.info('transmit() ' + str(bytes_sent) + ' of ' + str(bytes_total) + ' bytes')

    def close_conn(self):
        if not self.connected:
            print "Diconnected from server"
            logging.warn('BaseClient.transmit() disconnected from server')
            return
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except socket.error as e:
            if e.errno == 57:
                pass
            else:
                raise e
        self.sock.close()
        self.connected = False
        
    def __str__(self):
        return str(self.addr) + ':' + str(self.port)

class RPCClient(BaseClient):

    def __init__(self, server_address):
        super(RPCClient, self).__init__(server_address)

    def marshall(self, method_name, params):
        data = { 'method': method_name, 'parameters': params }
        json_data = json.dumps(data)
        logging.debug('RPCClient marshall(): ' + json_data)
        return json_data

    def call(self, method_name, params):
        response = 'RPCClient.call() entry point'
        if method_name == 'debug':
            print "RPC Client Debug() called", method_name, "@", self.addr, ":", self.port, "with", params
            return
        json_data = self.marshall(method_name, params)
        len_header = self.create_header(len(json_data))
        try:
            self.create_conn()
        except socket.error as err:
            response = 'Connection to VM failed: ' + repr(err)
        else:
            self.transmit(len_header)
            logging.debug('Sent header')
            self.transmit(json_data)
            logging.debug('Sent catalog. Blocking for response...')
            response = self.wait_response()
            logging.debug('Recvd response. Closing connection')
            self.close_conn()
        finally:
            logging.debug('Returning response')
            return response

    def wait_response(self):
        len_header = self.receive_header()
        data_len = int(len_header)
        response = self.receive(data_len)
        try:
            response = json.loads(response)
        except Exception as err:
            print repr(err)
            response = repr(err)
        return response

if __name__ == "__main__":
    client = BaseClient( ('192.168.10.1', 4829) )
    client.create_conn()
