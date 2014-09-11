#!/usr/bin/python
#vim: set fileencoding=utf-8 :

import SocketServer
import base64
import errno
import json
import socket
import sys
import threading

from config import SETTINGS
import server_functions.functions as functions
import server_functions.network_functions as network_functions


########################################
### Globals
localhost_addr = ''
host_interface_addr = ''

# List of imported function modules
# The functions in these modules should be unique, however,
# later modules will override earlier ones.
imported_functions = {}
imported_modules = [ 
                    functions.__dict__,
                    network_functions.__dict__ 
                    ]


########################################
# TCP Server and Request Handler(s)

class voodo_server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
      # Allows ctrl-c to kill all threads
      daemon_threads = True
      # Allows server to more quickly resume binding on socket
      allow_reuse_address = True
      def __init__(self, server_address, RequestHandlerClass):
          SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
          #self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

      def server_bind(self):
          self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          self.socket.bind(self.server_address)

class request_handler(SocketServer.BaseRequestHandler):

      # Called before handle
      def setup(self):
          pass
     
      # Called in finally: after handle
      def finish(self):
          print 'Shutting down socket...'
          self.request.shutdown(2)

      # Called in try:
      def handle(self):
          result = False
          job_dict, error_dict = self.read_incoming_data()
          # If the read fails, then result is the error output
          if error_dict:
            result = error_dict
          # Execute optional functions on the gateway, do not bother with result checking
          if job_dict.get('optional_gtwy_func'):
            for method in job_dict.get('optional_gtwy_func'):
              self.launch_method(method, job_dict)
          # Execute mandatory functions on the gateway, check results, break if any test fails
          if job_dict.get('required_gtwy_func'):
            for method in job_dict.get('required_gtwy_func'):
              result = self.launch_method(method, job_dict)
              # If method returns false, clear the job dict to go straight to return
              if not result['ret_code']:
                job_dict = {}
                break
          # If the job's destination address is not this address, forward the job to the destination
          if job_dict.get('dest_addr') and job_dict.get('dest_addr') != self.server.server_address[0]:
            result = self.forward_job(job_dict['dest_addr'], job_dict['dest_port'], job_dict)
          # Else the job dictionary is at its destination, execute normally
          elif job_dict.get('method'):
            result = self.launch_method(job_dict.get('method'), job_dict)
          # Send the final result back to the sender
          job_dict['job_status'] = True
          self.send_return_value(result)
          print 'End Handle()'

      # Receives all catalog on a socket until _END_OF_LINE string is encountered,
      # returns string without _END_OF_LINE
      def recv_to_EOL(self, sock=None):
          print 'Recv_to_EOL() entry point... ',
          result = ''
          while True:
            if sock:
              try:
                data = sock.recv(1024)
              except socket.timeout:
                print 'Timed out'
                print 'DATA:',result[-100:]
                break
            else:
              try:
                data = self.request.recv(1024)
              except socket.timeout:
                print 'Timed out'
                print 'DATA:',result[-100:]
                break
            if not data:
              break
            if '_END_OF_LINE' not in data:
              result += data
              if '_END_OF_LINE' in result[-100:]:
                result = result[:-12]
                break
            else:
              #result += catalog[:catalog.find('_END_OF_LINE')]
              result += data[:-12]
              break
          print 'End of line received'
          return result

      # Receive and decode json string, return python dictionary
      def read_incoming_data(self):
          data = self.recv_to_EOL()
          job_dict = {}
          error_dict = {}
          try:
            job_dict = json.loads(data)
          except Exception as exception:
            print 'Error reading json stream:',repr(exception)
            index = str(exception).find('(char ')
            index += 6
            print 'Isolating:',str(exception)[index:]
            begin = int(str(exception)[index:].partition(' ')[0])
            print data[begin : begin + 20]
            error_dict = { 'results' : { 'read_incoming_data' : ['', str(exception) ] } }
          else:
            if job_dict.get('payload'):
              try:
                job_dict['payload'] = base64.b64decode(job_dict['payload'])
              except TypeError as err:
                pass
          return job_dict, error_dict

      # Takes a string, and sends a json encoded object back to sender
      def send_return_value(self, data):
          try:
            json_data = json.dumps(data)
          except Exception as error:
            print 'Error encoding JSON return value:',error
            json_data = json.dumps( { 'results' : { 'gw_send_return_value' : ['', str(error)] } } )
          print 'Returning results...'
          self.request.sendall(json_data)
          print 'Sending terminator...'
          EOL = '_END_OF_LINE'
          EOL_length = len(EOL)
          total_sent = 0
          while total_sent < EOL_length:
            sent = self.request.send(EOL[total_sent:])
            if sent == 0:
              raise RuntimeError, "socket connection broken"
            total_sent = total_sent + sent
          print 'Ready...'

      # Forwards the job to destination, and blocks for the response
      def forward_job(self, addr, port, job_dict):
          print 'Forwarding...'
          if job_dict.get('payload'):
            job_dict['payload'] = base64.b64encode(job_dict['payload'])
          json_data = json.dumps(job_dict)
          print '   JSON catalog constructed'
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          sock.settimeout(60)
          print '   New socket made'
          sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          print '   Set socket options'
          print '   Trying to connect'
          try:
            sock.connect( (addr, port) )
          except socket.error as error:
            print '   Socket.error in forwarding:',repr(error)
            # Keeping this line just to hang onto the no route to host errno
            if error.errno == errno.EHOSTUNREACH:
              return False
            else:
              return False
          print '   Sending catalog'
          sock.sendall(json_data + '_END_OF_LINE')
          print '   Trying to receive catalog'
          result = self.recv_to_EOL(sock)
          if not result:
            result = json.dumps({ 'results': { 'gw_forward' : ['', 'Gateway forwarding receive response timeout'] } })
          try:
            result = json.loads(result)
          except ValueError as error:
            result = json.loads(str(error))
          print '   Shuttind down socket'
          sock.shutdown(2)
          print '   Closing socket'
          sock.close()
          print '   Forwarding End'
          return result

      # Checks for valid method in all the imported modules then executes it
      def launch_method(self, method, job_dict):
          if method in imported_functions:
            result = imported_functions[method](job_dict)
          else:
            print 'Method not found'
            result = 'Method not found'
          return result

 
########################################
# Boiler Plate Main

if __name__ == '__main__':
      host_addr = SETTINGS.get('HOST_ADDR')
      gateway = SETTINGS.get('LAN_GATEWAY')
      voodo_port = SETTINGS.get('VOODO_PORT')
      # Merge the module dicts together
      for module in imported_modules:
        imported_functions = dict(imported_functions.items() + module.items())
      # Find the host's IP address by creating a test socket, connecting to gateway
      test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
      if gateway:
        try:
            test_socket.connect( (gateway, 65000) )
        except socket.error as error:
            if error.errno == 9:
                print 'Malformed gateway IP address (LAN_GATEWAY value) in config.py:',gateway
            print 'Unable to initialize server.'
            print error
            print 'Exiting'
            sys.exit(1)
      else:
        try:
            test_socket.connect( (host_addr, 65000) )
        except socket.error as error:
            if error.errno == 9:
                print 'Malformed host IP address (HOST_ADDR) in config.py:',host_addr
            print 'Unable to initialize server.'
            print error
            print 'Exiting'
            sys.exit(1)
      localhost_addr = test_socket.getsockname()[0]
      test_socket.shutdown(2)
      test_socket.close()
      print 'Serving on', localhost_addr,':',voodo_port
      # Check if server is running on VM Gateway. If so, bind to host-only interface
      if localhost_addr == gateway:
        # Find gateway's address on host only interface
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            test_socket.connect( (host_addr, 65000) )
        except socket.error as error:
            if error.errno == 9:
                print 'Malformed gateway IP address (LAN_GATEWAY value) in config.py:',gateway
            print 'Unable to initialize server.'
            print error
            print 'Exiting'
            sys.exit(1)
        host_interface_addr = test_socket.getsockname()[0]
        print 'Running in proxy mode. Serving on', host_interface_addr,':',voodo_port
        test_socket.close()
        # Create thread for serving to host
        host_server = voodo_server( (host_interface_addr, voodo_port), request_handler)
        host_server_thread = threading.Thread(target = host_server.serve_forever)
        host_server_thread.daemon = True
        host_server_thread.start()
      # Begin honey server in main thread
      honey_server = voodo_server( (localhost_addr, voodo_port), request_handler)
      honey_server.serve_forever()
