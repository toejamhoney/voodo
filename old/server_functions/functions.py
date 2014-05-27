#!/usr/bin/python
#vim: set fileencoding=utf-8 :
import base64
import binascii
import codecs
import datetime
import getpass
import glob
import os
import subprocess
import threading
import time
import zipfile

from Registry import Registry
import config


# HKLM\System\CurrentControlSet\Control\Hivelist
hives = {
         'HKCU_1': 's:\\users\\' + getpass.getuser() + '\\NTUSER.DAT',
         'HKCU_2': 's:\\users\\' + getpass.getuser() + '\\AppData\\Local\\Microsoft\\Windows\\UsrClass.dat',
         'HKU_3': 's:\\windows\\System32\\config\\DEFAULT',
         'HKU_1': 's:\\windows\\ServiceProfiles\\LocalService\\NTUSER.DAT',
         'HKU_2': 's:\\windows\\ServiceProfiles\\NetworkService\\NTUSER.DAT',
         'HKLM\\SAM': 's:\\windows\\system32\\config\\sam',
         'HKLM\\SECURITY': 's:\\windows\\system32\\config\\security',
         'HKLM\\SOFTWARE': 's:\\windows\\system32\\config\\software',
         'HKLM\\SYSTEM': 's:\\windows\\system32\\config\\system'
        }

# Sets the time an executable is given to run before being closed
# For notepad.exe 5 seconds is fine, but for something like firefox you need a lot more.
# firefox will finally start after ~60 seconds, and takes almost 5 to exit cleanly
run_delay = 10
# Sets the amount of time to allow that process to shutdown
exit_delay = 20

host_address = config.SETTINGS['HOST_ADDR']
host_user = 'logger'
host_log_dir = config.SETTINGS['LOG_DIR']
server_dir = config.SETTINGS['GUEST_VOODO_DIR']

#################################################################################
#### Analysis Functions


def autorunsc(job_dict):
    #autorunsc = 'autorunsc -a -f -v -x'
    autorunsc = 'autorunsc -a -f -x'
    ret_val, stdout, stderr = handle_popen(autorunsc)
    job_dict['results']['autorunsc'] = ['', ret_val, stdout.decode('iso-8859-1').encode('utf8'), stderr]
    return job_dict

def shadow(job_dict):
    shadow = 'binaries\\vshadow-2008-x86.exe -script=c:\\tmp\\SETVAR1.cmd -p c:'
    expose = 'server_functions\\expose.cmd'
    ret_val, stdout, stderr = handle_popen(shadow)
    print 'SHADOW'
    print stdout
    print stderr
    job_dict['results']['shadow'] = ['', ret_val, stdout, stderr] 
    if ret_val:
      ret_val, stdout, stderr = handle_popen(expose)
      print 'EXPOSE'
      print stdout
      print stderr
      job_dict['results']['shadow_script'] = ['', ret_val, stdout, stderr] 
    return job_dict

def del_shadow(job_dict):
    del_shadow = 'vssadmin Delete Shadows /for=C: /Quiet'
    ret_val, stdout, stderr = handle_popen(del_shadow)
    job_dict['results']['del_shadow'] = ['', ret_val, stdout, stderr]
    return job_dict

def registry(job_dict):
    for name, loc in hives.iteritems():
      print name
      ret_val = []
      try:
        hive_file = open(loc, 'rb')
      except IOError as error:
        job_dict['results'][name] = ['', False, unicode( repr(error) )]
      else:
        registry = Registry.Registry(hive_file)
        rec(registry.root(), ret_val)
        job_dict['results'][name] = ['', True, ret_val]
    return job_dict

def event_logs(job_dict):
    # All the event logs windows generates
    logs = glob.glob('c:\\windows\\system32\\winevt\\logs\\*.evtx')
    job_dict['results']['event_logs'] = []
    check = make_dir('c:\\tmp')
    if check:
      job_dict['results']['event_logs'].append(check)
      return job_dict
 
    with zipfile.ZipFile('c:\\tmp\\evt_logs.zip', 'w', zipfile.ZIP_DEFLATED) as zipped:
      for log in logs:
        log_name = log.rpartition('\\')[2]
        log = '"' + log + '"'
        cmd = 'wevtutil epl "' + log_name.rpartition('.')[0].replace('%4', '/') + '" "c:\\tmp\\' + log_name + '"'
        handle_popen(cmd)
        zipped.write('c:\\tmp\\' + log_name)

    if job_dict.get('exe'):
        exe_path, exe_name = split_path_name(job_dict.get('exe'))
        dst = job_dict.get('dest_vm') + '/' + job_dict.get('date_stamp') + '/' + job_dict.get('job') + '/' + exe_name + '_evtlogs_win7_gaddn.zip'
    else:
        dst = job_dict.get('dest_vm') + '/' + job_dict.get('date_stamp') + '/' + job_dict.get('job') + '/' + job_dict.get('time_stamp') + '_evtlogs_win7_gaddn.zip'
    pscp_push('c:\\tmp\\evt_logs.zip', dst)
    job_dict['results']['event_logs'] = ['', cmd]
    return job_dict

def launch_pin(job_dict):
    if job_dict.get('pin_tool').startswith('v5'):
      # V5 tool still generates a V3.out log file
      log_name = 'V3.out'
    else:
      log_name = job_dict.get('pin_tool').partition('.')[0] + '.out'
    exe_path, exe_name = split_path_name(job_dict.get('exe'))
    result_name = log_name[:-4] + '_V5_msvc10_winxpsp3_' + exe_name
    kill_cmd = 'taskkill /f /t /IM ' + exe_name
    # Create results key
    job_dict['results'][result_name] = []
    check = make_dir('c:\\tmp')
    if check:
      job_dict['results']['launch_pin'].append(check)
      print 'Failed to create c:\\tmp dir'
      return job_dict
    # Change to tmp dir for *.out result file in a clean plase
    os.chdir('c:\\tmp')
   
    # Run PIN tool
    ret_val, stdout, stderr = handle_popen(job_dict.get('pin_cmd'), use_shell=True, wait=False)
    job_dict['results'][result_name] = ['', job_dict.get('pin_cmd'), ret_val]
    manual_sleep(job_dict.get('wait'))

    # Try and close process started, if ! force close
    ret_val, stdout, stderr = handle_popen(kill_cmd, use_shell=False)
    job_dict['results'][result_name].extend( [kill_cmd, ret_val, stdout, stderr] )
    if stderr.startswith('ERROR'):
      kill_cmd += ' /f'
      ret_val, stdout, stderr = handle_popen(kill_cmd, use_shell=False)
      job_dict['results'][result_name].extend( [kill_cmd, ret_val, stdout, stderr] )

    # Send log file back with pscp
    dst = job_dict.get('job') + '/'
    dst += '.'.join( [job_dict.get('dest_vm') + '-sp3', 'v5-msvc10', exe_name.rstrip('"'), 'log'] )
    manual_sleep(1)
    pscp_push(log_name, dst)
    os.chdir(server_dir)
    return job_dict


###############################################################################
#### Program Support Functions

def pscp_push(src, dst, host_user='logger'):
    cmd = ( server_dir + 
        '\\binaries\\pscp.exe -i c:\\keys\\voo_priv.ppk ' +
        '"' + src + '" ' +
        host_user + '@' + host_address + ':' +
        '"' + host_log_dir + '/' + dst + '"' )
    handle_popen(cmd)

def pscp_pull(src, dst, host_user='logger'):
    print server_dir + '\\binaries\\pscp.exe'
    print src
    print "to"
    print dst
    cmd = ( server_dir +
        '\\binaries\\pscp.exe -r -i c:\\keys\\voo_priv.ppk ' +
        host_user+'@'+host_address+':' +
        '"' + src + '" ' + dst )
    handle_popen(cmd)

def launch(job_dict):
    if not job_dict or not job_dict.get('exe'):
      job_dict['results']['launch'] = [ '', False, 'No exe specified' ]
      return job_dict
    if job_dict['exe'] == 'AcroRd32.exe':
      readerPath = findExe('AcroRd32.exe')
      job_dict['exe'] = readerPath
    if job_dict.get('flag'):
      exe_path = job_dict['exe'] + ' ' + job_dict['flag']
    else:
      exe_path = job_dict['exe']
    ret_val, stdout, stderr = handle_popen( exe_path,
                                            use_shell=False,
                                            wait=False )
    manual_sleep(int(job_dict.get('delay')))
    job_dict['results']['launch'] = [ '', ret_val, stdout, stderr ]
    return job_dict

def pull_file(job_dict):
    src = job_dict.get('input')
    dst = job_dict.get('output')
    check = make_dir(dst)
    if check:
        job_dict['results']['pull_file'] = ['', False, check]
        return job_dict
    username = job_dict.get('username')
    pscp_pull(src, dst, username)
    job_dict['results']['pull_file'] = ['', True]
    return job_dict

def make_dir(path):
    try:
      os.makedirs(path)
    except OSError as error:
      if error.errno == 17:
        # Dir exists already
        pass
      else:
        return 'Err creating dir:' + repr(error)

def clean_up(path):
    result = []
    try:
      os.remove(path)
      result.append('Removed file:' + path)
    except OSError as error:
      result.append('Err removing:' + path + ' ' + repr(error))
      file_iter = glob.iglob(os.path.join(path, '*'))
      for file_guy in file_iter:
        try:
          os.remove(file_guy)
          result.append('Removed file:' + file_guy)
        except OSError as error:
          result.append('Err removing:' + file_guy + ' ' + repr(error))
          print repr(error)
        finally:
          try:
            os.rmdir(path)
            result.append('Removed dir:' + path)
          except OSError as error:
            result.append('Err removing dir:' + path + ' ' + repr(error))
            print repr(error)
    finally:
      return result

def handle_popen(cmd, use_shell=True, verbose=True, wait=True):
    if verbose:
      print cmd
    ret_val = True
    stdout = None
    stderr = None
    if not wait:
      try:
        child = subprocess.Popen(cmd,
                                shell=use_shell)
      except (OSError, ValueError) as error:
        ret_val = False
        stderr = unicode( repr(error) )
      else:
        if child.returncode:
          ret_val = False
    else:
      try:
        child = subprocess.Popen( cmd, 
                                shell=use_shell,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
      except (OSError, ValueError) as error:
        ret_val = False
        stderr = unicode( repr(error) )
      else:
        stdout, stderr = child.communicate()
        if verbose and stdout:
            print stdout
        if verbose and stderr:
            print stderr
        if child.returncode:
          ret_val = False
    return ret_val, stdout, stderr

try:
    import _winreg
except ImportError as err:
    # Smells like *NIX...move along!
    pass
else:
    def findExe(programToFind):
        registry = _winreg.ConnectRegistry(None,_winreg.HKEY_LOCAL_MACHINE)
        key = _winreg.OpenKey(registry,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\' +
                programToFind, 0, _winreg.KEY_ALL_ACCESS)
        name,value,typeOf = _winreg.EnumValue(key,0)
        return value

def manual_sleep(delay):
    then = datetime.datetime.now()
    while True:
      now = datetime.datetime.now()
      if now - then > datetime.timedelta(seconds=delay):
        break

def split_path_name(full_path):
    if os.name == 'nt':
      path_parts = full_path.rpartition('\\')
    else:
      path_parts = full_path.rpartition('/')
    return path_parts[0], path_parts[2]


###############################################################################
#### Registry Module Functions

def rec(key, ret_val):
    for subkey in key.subkeys():
      rec(subkey, ret_val)
      now = datetime.datetime.now()
      if (now - subkey.timestamp() < datetime.timedelta(minutes=5)):
        key = unicode(subkey.path())
        ret_val.append(key)
        for value in subkey.values():
          ret_val.append('    ' + read_value(value))

def read_value(reg_value):
    val_name = reg_value.name()
    val_str = reg_value.value_type_str()
    val_int = reg_value.value_type()
    val = reg_value.value()
    ret_val = val_name + ' ' + val_str + ': '
    if val_int == 0x0003:
      ret_val += binascii.hexlify(val)
    elif val_int == 0x000A or val_int == 0x0008 or val_int == 0x0009:
      ret_val += str(val)
    else:
      ret_val += unicode(val).encode('ascii', 'replace')
    return ret_val
