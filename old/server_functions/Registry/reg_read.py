import datetime
import os
import sys
import time

import Registry
import win32api
import win32com.shell.shell as shell


ASADMIN = 'asadmin'
'''
if sys.argv[-1] != ASADMIN:
  script = os.path.abspath(sys.argv[0])
  params = ' '.join( [script] + sys.argv[1:] + [ASADMIN] )
  print 'Not admin. Running:'
  print sys.executable
  print params
  shell.ShellExecuteEx(lpVerb='runas', lpFile=sys.executable, lpParameters=params)
  win32api.ShellExecute(0,
                        'runas',
                        'C:\\python27\\python.exe',
                        'C:\\src\\server_functions\\Registry\\reg_read.py asadmin',
                        'C:\\python27\\python.exe',
                        1)
else:
'''
results={}
def rec(key, depth=0):
  for subkey in key.subkeys():
    rec(subkey, depth + 1)
    if (datetime.datetime.now() - subkey.timestamp() < datetime.timedelta(minutes=10)):
      results[subkey.path()] = []
      for value in subkey.values():
        results[subkey.path()].append('    ' + value.name() + ':' + str(value.value()))

output = open('C:\\users\\honey\\desktop\\reg_out.log', 'w')
output.write('Running as admin...\n')
output.write('Attempting to open hive...')
try:
  hive = open(r't:\windows\system32\config\software', 'rb')
except Exception as error:
  print error
  sys.exit(1)
output.write('Hive opened\r\n')
reg = Registry.Registry(hive)
output.write('Loaded hive into registry\r\n')
output.write('Opening...\n')

try:
  key = reg.open('Microsoft\\Windows\\CurrentVersion\\Run')
  #key = reg.root()
#except Registry.RegistryKeyNotFoundException:
except Exception as error:
  output.write(str(error)+'\n')
else:
  output.write('Iterating keys...\n\n')
finally:
  rec(reg.root())
  for result in results:
    output.write(result + '\n')
    for value in results[result]:
      output.write(value + '\n')
  output.close()
