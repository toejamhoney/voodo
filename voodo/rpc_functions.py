# Python Modules
import binascii
import datetime
import getpass
import glob
import os
import zipfile

from Registry import Registry
from utils import handle_popen, make_dir, manual_sleep, pscp_push, server_dir, \
    split_path_name


# Voodo Modules
# Mandiant Modules
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


#################################################################################
#### RPC Object

class RPC(object):
  
    def __init__(self):
        pass
      
    def echo(self, args=None):
        print 'echo():',str(args)
        
    def verify_params(self, params):
        if isinstance(params, dict):
            return True
        else:
            return False
        
    def autorunsc(self, job_dict):
        if not isinstance(job_dict, dict):
            raise AttributeError('RPC method requires dictionary got ' + str(type(job_dict)))
        autorunsc = 'autorunsc -a -f -x'
        ret_val, stdout, stderr = handle_popen(autorunsc)
        job_dict['results']['autorunsc'] = ['', ret_val, stdout.decode('iso-8859-1').encode('utf8'), stderr]
        return job_dict
    
    def shadow(self, job_dict):
        shadow = 'binaries\\vshadow-2008-x86.exe -script=c:\\tmp\\SETVAR1.cmd -p c:'
        expose = 'binaries\\expose.cmd'
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
    
    def del_shadow(self, job_dict):
        del_shadow = 'vssadmin Delete Shadows /for=C: /Quiet'
        ret_val, stdout, stderr = handle_popen(del_shadow)
        job_dict['results']['del_shadow'] = ['', ret_val, stdout, stderr]
        return job_dict
    
    def registry(self, job_dict):
        for name, loc in hives.iteritems():
            print name
            ret_val = []
            try:
                hive_file = open(loc, 'rb')
            except IOError as error:
                job_dict['results'][name] = ['', False, unicode(repr(error))]
            else:
                registry = Registry.Registry(hive_file)
                self.rec(registry.root(), ret_val)
                job_dict['results'][name] = ['', True, ret_val]
        return job_dict
    
    def event_logs(self, job_dict):
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
    
    def launch_pin(self, job_dict):
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
        job_dict['results'][result_name].extend([kill_cmd, ret_val, stdout, stderr])
        if stderr.startswith('ERROR'):
            kill_cmd += ' /f'
            ret_val, stdout, stderr = handle_popen(kill_cmd, use_shell=False)
            job_dict['results'][result_name].extend([kill_cmd, ret_val, stdout, stderr])
    
        # Send log file back with pscp
        dst = job_dict.get('job') + '/'
        dst += '.'.join([job_dict.get('dest_vm') + '-sp3', 'v5-msvc10', exe_name.rstrip('"'), 'log'])
        manual_sleep(1)
        pscp_push(log_name, dst)
        os.chdir(server_dir)
        return job_dict
      
      
    ###############################################################################
    #### Registry Module Functions
    
    def rec(self, key, ret_val):
        for subkey in key.subkeys():
            self.rec(subkey, ret_val)
            now = datetime.datetime.now()
            if (now - subkey.timestamp() < datetime.timedelta(minutes=5)):
                key = unicode(subkey.path())
                ret_val.append(key)
                for value in subkey.values():
                    ret_val.append('    ' + self.read_value(value))
    
    def read_value(self, reg_value):
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
