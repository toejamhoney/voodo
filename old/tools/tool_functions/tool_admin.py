#!/usr/bin/python
#vim: set fileencoding=utf-8 :

import argparse
import base64
import datetime
import glob
import json
import os
import subprocess
import zipfile

import config


##################################################################################
#### Module Scope Vars
# Never trust user input...
log_dir = config.SETTINGS['LOG_DIR'].rstrip('/\\')


##################################################################################
#### Tool Support Functions

# Simple boolean checker on result that should be used in each tool call
def check_result(result):
    if not result:
      print 'Result error; nothing to diff'
    elif parsed_args_dict['analyzers']:
      print 'Handing catalog off for comparison...'
      runDiff()
    else:
      print 'Complete. No errors detected.'

# Init date/time stamps for file/folder creation 
def get_stamped():
    date_obj = datetime.datetime.today()
    date_stamp = date_obj.strftime('%Y-%m-%d')
    time_stamp = date_obj.strftime('%I_%M')
    return [date_stamp, time_stamp]

# This parses all the command line arguments for each function. You could create another parser,
# and call that instead of this if you want to avoid flags overlapping. For right now it is not 
# so monolithic as to make that option more attractive. One parser should also help reduce duplicate
# flags needed in each function, like: -vm -j and -a
def parse_arguments(line):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--analyzers',
                        nargs='*',
                        default=[],
                        help='optional: specify analyzing tools to be run before and after launch. Options = autorunsc, registry')
    parser.add_argument('-b', '--before',
                        action='store_true',
                        default=False,
                        help='optional: specify this job as creating a before analysis image used in diffs later')
    parser.add_argument('--delay',
                        default='10',
                        help='optional: specify amount of time to allow executable to run. default is 10 sec')
    parser.add_argument('-d', '--diff',
                        action='store_true',
                        default=False,
                        help='optional: specify this job should have a diff run on the logs')
    parser.add_argument('-f', '--flag',
                        nargs='*',
                        default=[],
                        help='optional: flags for exe')
    parser.add_argument('--flag2',
                        nargs='*',
                        default=[],
                        help='optional: flags for exe')
    parser.add_argument('--flag3',
                        nargs='*',
                        default=[],
                        help='optional: flags for exe')
    parser.add_argument('-i', '--input',
                        nargs='*',
                        default = [],
                        help='optional: use with a tool to specify an input file name')
    parser.add_argument('-j', '--job',
                        nargs=1,
                        default='old_no_name_' + datetime.datetime.today().strftime('%I_%M'),
                        help='optional: name for the job that will be run')
    parser.add_argument('-l', '--log',
                        action='store_true',
                        default=False,
                        help='optional: name of log, or white space separated list of log names (from config.py). No entry = no logs')
    parser.add_argument('-m', '--method',
                        help='optional: function to call on guest')
    parser.add_argument('-o', '--output',
                        nargs=1,
                        help='optional: use with a tool to specify an output file name')
    parser.add_argument('-p', '--priority',
                        type=int,
                        default=1,
                        help='optional: set the priority of the jobs being forked. High = 0, Med(Default) = 1, Low = 2')
    parser.add_argument('-q', '--query',
                        nargs='*',
                        help='optional: use with search function to specifiy the term(s) to search with. this or the url option may be used')
    parser.add_argument('-r', '--reset',
                        action='store_true',
                        default=False,
                        help='optional: default is true, tells the driver to reset(kill, restore, start) the guests between forked procs')
    parser.add_argument('-t', '--pin_tool',
                        nargs='*',
                        default=[],
                        help='optional: dll to be used with pin execution')
    parser.add_argument('-u', '--url',
                        nargs='*',
                        help='optional: the url to check for redirects. either this or the query term may be used')
    parser.add_argument('-v', '--vms',
                        nargs='*',
                        default=[],
                        help='list of virtual machine names to run job on')
    parser.add_argument('-w', '--wait',
                        type=int,
                        default=30,
                        help='optional argument for a wait time. default is 10')
    parser.add_argument('-x', '--exe',
                        nargs='*',
                        default=[],
                        help='required for launch command: path to file to load/run')
    try:
      parsed = parser.parse_args(line)
    except SystemExit:
      return None
    else:
      if isinstance(parsed.job, list):
        parsed.job = parsed.job[0]
      if isinstance(parsed.method, list):
        parsed.method = parsed.method[0]
      if isinstance(parsed.url, list):
        parsed.url = parsed.url[0]
      if isinstance(parsed.output, list) and len(parsed.output) == 1:
        parsed.output = parsed.output[0]
      parsed.input = concat(parsed.input, ' ')
      parsed.exe = concat(parsed.exe, ' ')
      parsed.flag = concat(parsed.flag, ' ').replace('+','-')
      parsed.flag2 = concat(parsed.flag2, ' ').replace('+','-')
      parsed.flag3 = concat(parsed.flag3, ' ').replace('+','-')
      parsed.pin_tool = concat(parsed.pin_tool, ' ')
      return parsed

# Joins the elements in a list with the passed in char, or returns the first element if its only one
def concat(path_list, char):
    if len(path_list) == 1:
      result = path_list[0]
    else:
      result = char.join(path_list)
    return result

# Parse line input, and create job dictionary
def create_job_dict(line):
    parsed = parse_arguments(line)
    try:
      job_dict = vars(parsed)
    except Exception as error:
      print 'Error creating job dict:',repr(error)
      return False
    # # # 
    job_dict['username'] = config.SETTINGS['LOG_USER']
    job_dict['line'] = line
    job_dict['results'] = {}
    job_dict['date_stamp'],job_dict['time_stamp'] = get_stamped()
    return job_dict

# Overwrites the values in the dynamic conf object files with a new
# object. No safety nets.
def update_config(conf_name, conf_obj):
    with open('conf/'+conf_name+'.py', 'w') as conf_file:
      json.dump(conf_obj, conf_file, indent=4)


##################################################################################
#### File and Analysis Functions

def create_log_dirs(job_dict):
    # Takes a list in job_dict['vms'] and creates log directories for each val in list
    old_mask = os.umask(0007)
    for vm in job_dict.get('vms'):
      job_dict['dest_vm'] = vm
      # # #
      if job_dict.get('before'):
        job_dict['log_dir'] = os.path.join(log_dir, job_dict['job'], 'before')
      else:
        job_dict['log_dir'] = os.path.join(log_dir, job_dict['job'])
      # # #
      try:
        os.makedirs(job_dict['log_dir'], 0770)
      except OSError as error:
        # errno 17 means dir already exists
        if error.errno == 17:
          pass
        else:
          print 'ERROR creating log dirs:',repr(error)
      # # #
      job_dict['dest_vm'] = ''
    os.umask(old_mask)

def write_to_log(job_dict):
    cwd = os.getcwd()
    if job_dict.get('before'):
      full_log_dir = os.path.join(log_dir, job_dict['job'], 'before')
    else:
      full_log_dir = os.path.join(log_dir, job_dict['job'])
    os.chdir(full_log_dir)
    # # #
    for log_name, log_data in job_dict['results'].iteritems():
      encodings = log_data[0]
      payload = log_data[1:]
      file_name = log_name + '.' + job_dict['time_stamp']
      #if job_dict.get('exe'):
        #file_name += '_' + job_dict.get('exe')
      if 'zip' in encodings:
        file_name += '.zip'
      else:
        file_name += '.log'
      with open(file_name, 'ab') as file_out:
        for data in payload:
          if 'base64' in encodings:
            data = base64.b64decode(data)
          if isinstance(data, list):
            data = '\n'.join(data)
          if 'zip' in encodings:
            file_out.write(data)
          else:
            try:
              file_out.write( unicode(data, 'utf_8') )
            except UnicodeEncodeError:
              file_out.write( data )
            except TypeError:
              try:
                file_out.write( unicode(str(data), 'utf_8') )
              except UnicodeEncodeError:
                try:
                  #catalog.decode('utf-8')
                  file_out.write(data.encode('UTF-8'))
                except UnicodeEncodeError:
                  file_out.write(data)
    os.chdir(cwd)

def diff_logs(job_dict):
    be4_dir = os.path.join(log_dir, job_dict['job'], 'before')
    be4_file = newest_file(be4_dir)
    aft_dir = os.path.join(log_dir, job_dict['job'], job_dict['method'])
    aft_file = newest_file(aft_dir)
    if not be4_file or not aft_file:
      print 'Unable to run diff'
      return False
    diff_cmd = r'diff -U 10 ' + be4_file.replace(' ','\\ ') + ' ' + aft_file.replace(' ','\\ ') + ' > ' + aft_file.replace(' ','\\ ') + '_diffed.txt'
    proc = subprocess.Popen(diff_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

def newest_file(path):
    files = glob.glob(path + '*')
    if not files:
      print path,'is empty'
      return False
    new_file = { 'age':0, 'path':'' }
    for a_file in files:
      a_file_path = os.path.abspath(a_file)
      a_file_age = os.path.getmtime(a_file_path)
      if a_file_age > new_file['age']:
        new_file['age'] = a_file_age
        new_file['path'] = a_file_path
    return new_file['path']

def split_path_name(full_path):
    if os.path.isdir(full_path):
        return full_path, None
    if '/' in full_path:
      path_parts = full_path.rpartition('/')
    else:
      path_parts = full_path.rpartition('\\')
    if not path_parts[2]:
        path_parts[2] = ''
    return path_parts[0], path_parts[2]

# Reads a file, adding each line to a list
def read_file(file_name):
    if not file_name:
      return None
    ret_val = []
    try:
      a_file = open(file_name, 'r')
    except IOError as error:
      print 'File open error', error
    else:
      for line in a_file:
        if line.startswith('#'):
          pass
        else:
          ret_val.append(line)
      return ret_val

def create_iso(path):
    if os.name == 'nt':
      file_name = path.rpartition('\\')[2] + '.iso'
    else:
      file_name = path.rpartition('/')[2] + '.iso'
    path_out = os.path.join(config.SETTINGS['ISO_DIR'].replace(' ','\ '), file_name)
    hdi_cmd = 'hdiutil makehybrid -ov -o ' + path_out + ' ' + path + ' -iso -joliet'
    print hdi_cmd
    proc = subprocess.Popen(hdi_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(subprocess.PIPE)
    if stdout.rstrip():
      print stdout
    if stderr.rstrip():
      print stderr
    return file_name

def attach_iso(iso, vm, device='1'):
    path = os.path.join(config.SETTINGS['ISO_DIR'].replace(' ', '\ '), iso)
    cmd = 'VBoxManage storageattach ' + vm + ' --storagectl "IDE" --port 1 --device ' + device + ' --type dvddrive --medium ' + path
    print cmd
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(subprocess.PIPE)
    if stdout.rstrip():
      print stdout
    if stderr.rstrip():
      print stderr

def get_file_stat(path, values):
    ret_values = {}
    try:
      stat_struct = os.stat(path)
    except OSError as error:
      if error.errno == 2:
        # No such file error, file does not exist
        print 'File not found:',path, repr(error)
        ret_values['st_size'] = 0
        return ret_values
      else:
        return None

    for value in values:
      if value == 'st_mode':
        ret_values['st_mode'] = stat_struct.st_mode

      elif value == 'st_ino':
        ret_values['st_ino'] = stat_struct.st_ino

      elif value == 'st_dev':
        ret_values['st_dev'] = stat_struct.st_dev

      elif value == 'st_nlink':
        ret_values['st_nlink'] = stat_struct.st_nlink

      elif value == 'st_uid':
        ret_values['st_uid'] = stat_struct.st_uid

      elif value == 'st_gid':
        ret_values['st_gid'] = stat_struct.st_gid

      elif value == 'st_size':
        ret_values['st_size'] = stat_struct.st_size

      elif value == 'st_atime':
        ret_values['st_atime'] = stat_struct.st_atime

      elif value == 'st_mtime':
        ret_values['st_mtime'] = stat_struct.st_mtime

      elif value == 'st_ctime':
        ret_values['st_ctime'] = stat_struct.st_ctime

    return ret_values

def move_file(src, dst):
    try:
      os.rename(src, dst)
    except OSError as error:
      print 'Error moving file:', repr(error)
      return None

def sanitize_path(path):
    ret_path = expand_path(path)
    if not ret_path or not os.path.exists(ret_path):
        print 'Tool_admin.sanitize_path() could not find the path:',ret_path
        return None
    return ret_path

def expand_path(path):
    if not path:
        return None
    path = os.path.expanduser(path)
    expanded_path = os.path.expandvars(path)
    return expanded_path
