#!/usr/bin/python
#vim: set fileencoding=utf-8 :
import base64
import errno
import json
import os
import socket
import threading
import time

import config
import tools.tool_functions.tool_admin as tool_admin


######################################################################
### Network Communications Handler
class VoodoClient(object):

      def __init__(self):
          self.proxy_port = config.SETTINGS.get('PROXY_PORT')
          self.voodo_port = config.SETTINGS.get('VOODO_PORT')
          self.guests = config.GUESTS
          self.timeout = 60
          self.threads = []

      # Target for threads
      def send_thread(self, IP, data):
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          sock.settimeout(self.timeout)
          try:
            sock.connect( (IP, self.voodo_port) )
          except socket.error as error:
            sock.close()
            if error.errno == errno.ECONNREFUSED:
              pass
            else:
              raise error
          except KeyboardInterrupt:
            sock.close()
            return None
          else:
            try:
              sock.sendall(data + '_END_OF_LINE')
            except Exception as error:
              print "Data transmission error in send_thread:",error
              sock.close()
              return False
            else:
              ret_val = self.recv_to_EOL(sock)
              sock.close()
              return ret_val

      def send_job(self, job_dict):
          result = False
          job_dict['dest_addr'] = self.verify_vm(job_dict['dest_vm'])
          if not job_dict.get('dest_addr'):
            print 'Cannot find VM address'
            return False
          job_dict['dest_port'] = self.voodo_port
          if job_dict.get('payload'):
            job_dict['payload'] = base64.b64encode(job_dict['payload'])
          data = json.dumps(job_dict)
          print '    Job created. remote method:' + job_dict.get('method') + ' dest_vm:' + job_dict['dest_vm'] + ' @ ' + job_dict['dest_addr'] + ':' + str(job_dict['dest_port'])
          # # #
          gateway = config.GUESTS[job_dict['dest_vm']].get('gateway')
          if gateway:
            print '    Sending job to gateway:',gateway,'@',config.GUESTS[gateway]['address']
            result = self.send_thread(config.GUESTS[gateway]['address'], data)
          else:
            print '    Sending job to:',job_dict['dest_vm'],'@',job_dict['dest_addr']
            result = self.send_thread(job_dict['dest_addr'], data)
          return result

      # Checks vm for a running server instance,
      # and then returns a list of tuples (vm name, ip address)
      # Reloads config.py before every run; ensuring it is up to date
      def verify_vm(self, vm_name):
          running = ''
          self.guests = self.reload_settings('guests')
          if self.probe_server(vm_name, self.guests[vm_name]['address']):
            running = config.GUESTS[vm_name]['address']
          if not running:
            print vm_name,'does not have a responsive server agent'
          return running

      # Checks a VM's server agent is up and running
      def probe_server(self, vm, ip_addr):
          if not ip_addr:
            return False
          job_dict = {
            'method':'server_status',
            'dest_VM' : vm,
            'dest_addr' : ip_addr,
            'dest_port' : self.voodo_port,
            'results' : {},
            }
          data = json.dumps(job_dict)
          gateway = config.GUESTS[vm].get('gateway')
          if gateway:
            result = self.send_thread(config.GUESTS[gateway]['address'], data)
          else:
            result = self.send_thread(ip_addr, data)
          return result

      def recv_to_EOL(self, sock):
          result = u''
          counter=0
          log = self.open_log_file()
          while True:
            counter += 1
            data = sock.recv(4096)
            if not data and log:
              log.write('No data\n')
              break
            elif log:
              log.write(data + '\n')
            if '_END_OF_LINE' not in data:
              result += data
              if '_END_OF_LINE' in result[-100:]:
                result = result[:-12]
                if log:
                    log.write('\n\n')
                break
            else:
              result += data[:-12]
              if log:
                  log.write('\n\n')
              break
          if log:
            log.close()
          try:
            result = json.loads(result)
          except (ValueError, TypeError) as error:
            print 'Error in recv to end of line:',error
          return result


######################################################################
### Support Functions

      def reload_settings(self, name):
          with open(config.SETTINGS['VOODO_DIR'] + '/conf/'+ name.upper() +'.py', 'r') as settings_file:
            return json.load(settings_file)

      def open_log_file(self):
          log_filename = os.path.join(config.SETTINGS['LOG_DIR'], 'host')
          try:
            os.makedirs(log_filename)
          except OSError as error:
            if error.errno == 17:
                pass
            else:
                raise error
          log_filename = os.path.join(log_filename, 'client_recv.log')
          date_stamp, time_stamp = tool_admin.get_stamped()
          backup_log = config.SETTINGS['LOG_DIR'] + '/host/client_recv' + '-' + date_stamp + '_' + time_stamp + '.bak'
          log_file_stats = tool_admin.get_file_stat(log_filename, ['st_size',])
          if log_file_stats['st_size'] > 10000000:
            tool_admin.move_file(log_filename, backup_log)
          try:
            log_file = open(log_filename, 'a')
          except IOError as error:
            print 'Error opening log file:', repr(error)
            return None
          else:
            return log_file


######################################################################
### Functions that may be used with proxy, but are unnecessary

      def sock_to_proxy(self, sock):
          try:
            sock.connect((self.gateway_addr, self.voodo_port))
          except Exception as error:
            print self.gateway_addr,":",self.voodo_port
            print "Host to proxy socket connection error:",error

      def sock_thru_proxy(self, sock, dest_addr):
          try:
            sock.send(("CONNECT %s:%d HTTP/1.1\r\n" + "Host: %s:%d\r\n\r\n") % (dest_addr, self.voodo_port, dest_addr, self.voodo_port))
          except Exception as error:
            print "Connection through proxy failed:",error
          else:
            result = sock.recv(1024)
            if result.startswith(r'HTTP/1.0 200'):
              return True
            else:
              return False
