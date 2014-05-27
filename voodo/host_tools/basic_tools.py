#!/usr/bin/python
#vim: set fileencoding=utf-8 :

import glob
import os

import config
import handlers.voodo_comm
import tool_functions.tool_admin as tool
import tool_functions.web_comm as spiderman


###########################################################################
### Module Vars
net = handlers.voodo_comm.VoodoClient()
guests = config.GUESTS
nic_flags = {
  'enable': 'netsh interface set interface "{name}" ENABLED',
  'disable': 'netsh interface set interface "{name}" DISABLED',
  'address': 'netsh interface ipv4 set address "{name}" static {address} {netmask} {gateway}'
}

###########################################################################
### Basic Functions

def guest_exec(job_dict, fork_arg=None):
    #if fork_arg:
      #job_dict['flag'] = fork_arg
    if not job_dict.get('method'):# or job_dict.get('method') != 'launch':
      job_dict['method'] = 'launch'
    run_job(job_dict)

def get_event_logs(job_dict):
    if job_dict.get('input') and not job_dict.get('exe'):
        push(job_dict)
        job_dict['exe'] = '"' + config.SETTINGS['MALWARE_DEST'].rstrip('/ \\') + '\\' + job_dict.get('input').rpartition('/')[2] + '"'
    job_dict['method'] = 'launch'
    result = run_job(job_dict)
    if result:
        job_dict['method'] = 'event_logs'
        result = run_job(job_dict)
    return result

def pin(job_dict, fork_arg=None):
    if job_dict.get('input') and not job_dict.get('exe'):
        push(job_dict)
        job_dict['exe'] = '"' + config.SETTINGS['MALWARE_DEST'].rstrip('/ \\') + '\\' + job_dict.get('input').rpartition('/')[2] + '"'
    # Add pin flags
    pin_cmd = '"' + config.SETTINGS['PIN_BAT_DIR'].rstrip('\\/') + '\\pin" '
    if job_dict.get('flag'):
        pin_cmd = ' '.join([pin_cmd, job_dict.get('flag'), '-t'])
    else:
        pin_cmd = ' '.join([pin_cmd, '-t'])
    # Add tool flags
    if job_dict.get('flag2'):
        pin_cmd = ' '.join([pin_cmd, '"' + config.SETTINGS['PIN_TOOLS_DIR'].rstrip('\\/') + '\\' + job_dict.get('pin_tool') + '"', job_dict.get('flag2')])
    else:
        pin_cmd = ' '.join([pin_cmd, '"' + config.SETTINGS['PIN_TOOLS_DIR'].rstrip('\\/') + '\\' + job_dict.get('pin_tool') + '"'])
    # Add binary flags
    if job_dict.get('flag3'):
        pin_cmd = ' '.join([pin_cmd, '--', job_dict.get('exe'), job_dict.get('flag3')])
    else:
        pin_cmd = ' '.join([pin_cmd, '--', job_dict.get('exe')])
    job_dict['pin_cmd'] = pin_cmd
    job_dict['method'] = 'launch_pin'
    # # #
    result = run_job(job_dict)
    return result

def load_iso(job_dict, fork_arg=None):
    if fork_arg:
      job_dict['input'] = fork_arg
    file_in = job_dict.get('input')
    if not file_in:
      return False
    iso = tool.create_iso(file_in)
    for vm in job_dict.get('vms'):
      tool.attach_iso(iso, vm, '0')

def push(job_dict, fork_arg=None):
    if fork_arg:
        full_path = tool.sanitize_path(fork_arg)
        print 'Fork:',full_path
    else:
        full_path = tool.sanitize_path(job_dict.get('input'))
        print 'Input:',full_path
    if not full_path:
        return False

    file_path, file_name = tool.split_path_name(full_path)

    if not job_dict.get('output'):
        job_dict['output'] = config.SETTINGS['MALWARE_DEST']

    job_dict['input'] = full_path
    job_dict['file_path'] = file_path
    job_dict['file_name'] = file_name
    job_dict['method'] = 'pull_file'
    print 'IN:',job_dict.get('input')
    print 'OUT:',job_dict.get('output')
    print 'PATH:',job_dict.get('file_path')
    print 'NAME:',job_dict.get('file_name')
    run_job(job_dict)

def set_nic(job_dict, fork_arg=None):
    vm = job_dict.get('dest_vm')
    try:
      nic_name, nic_cmd, nic_addr, nic_mask, nic_gway = job_dict.get('flag').split(' ')
    except ValueError:
      nic_name, nic_cmd = job_dict.get('flag').split(' ')
      nic_addr = ''
    if nic_name == '0':
      print 'Changing the interface used for host <-> guest communication is not approved behavior at this time'
      return
    # # #
    try:
      nic_name = guests[vm]['nics'][nic_name]
    except Exception as error:
      print repr(error)
      pass
    if nic_addr:
      try:
        nic_gway_addr = guests[nic_gway][address]
      except KeyError:
        nic_gway_addr = nic_gway
      finally:
        guests[vm]['address'] = nic_addr
    # # # 
    if nic_addr:
      job_dict['exe'] = nic_flags[nic_cmd].format(name=nic_name, address=nic_addr, netmask=nic_mask, gateway=nic_gway_addr)
    else:
      job_dict['exe'] = nic_flags[nic_cmd].format(name=nic_name)
    # # #
    job_dict['flag'] = ''
    job_dict['method'] = 'launch'
    result = net.send_job(job_dict)
    # # #
    #tool.update_config('GUESTS', guests)

def run_job(job_dict):
    for vm in job_dict.get('vms'):
      job_dict['dest_vm'] = vm
      result = net.send_job(job_dict)
      if job_dict.get('log'):
        tool.write_to_log(result)
        if job_dict.get('diff'):
          tool.diff_logs(job_dict)
      else:
        for key, value in result['results'].iteritems():
          print '   ',key
          for item in value:
            if item:
              print '        ',item
      return result
