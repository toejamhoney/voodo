# Python modules
import datetime
import glob
import os
import subprocess


# Voodo modules
try:
    import config
except ImportError:
    config = {'SETTINGS': {'HOST_ADDR': '', 'LOG_DIR': '', 'GUEST_VOODO_DIR': ''} }
    host_address = ''
    host_user = 'logger'
    host_log_dir = ''
    server_dir = ''
else:
    host_address = config.SETTINGS['HOST_ADDR']
    host_user = 'logger'
    host_log_dir = config.SETTINGS['LOG_DIR']
    server_dir = config.SETTINGS['GUEST_VOODO_DIR']

###############################################################################
#### Program Support Functions

def pscp_push(src, dst, host_user='logger'):
    cmd = (server_dir + '\\binaries\\pscp.exe -i c:\\keys\\voo_priv.ppk ' +
        '"' + src + '" ' + host_user + '@' + host_address + ':' + dst + '"')
    ret,out,err = handle_popen(cmd)
    return ret, out, err

def pscp_pull(src, dst, host_user='logger'):
    print server_dir + '\\binaries\\pscp.exe'
    print src
    print "to"
    print dst
    cmd = (server_dir +
        '\\binaries\\pscp.exe -r -i c:\\keys\\voo_priv.ppk ' +
        host_user + '@' + host_address + ':' +
        '"' + src + '" ' + dst)
    ret,out,err = handle_popen(cmd)
    return ret, out, err

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
    ret_val, stdout, stderr = handle_popen(exe_path,
                                            use_shell=False,
                                            wait=False)
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
    ret, out, err = pscp_pull(src, dst, username)
    job_dict['results']['pull_file'] = ret
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
    stdout = ''
    stderr = ''
    if not wait:
        try:
            child = subprocess.Popen(cmd, shell=use_shell)
        except (OSError, ValueError) as error:
            ret_val = False
            stderr = "STDERR: " + unicode(repr(error))
        else:
            if child.returncode:
                ret_val = False
                stderr = "POPEN Error Failed to execute: " + str(cmd)
    else:
        try:
            child = subprocess.Popen(cmd, shell=use_shell,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        except (OSError, ValueError) as error:
            ret_val = False
            stderr = "STDERR: " + unicode(repr(error))
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
except ImportError:
    # Smells like *NIX...move along!
    pass
else:
    def findExe(programToFind):
        registry = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
        key = _winreg.OpenKey(registry,
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\' +
                programToFind, 0, _winreg.KEY_ALL_ACCESS)
        name, value, typeOf = _winreg.EnumValue(key, 0)
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
